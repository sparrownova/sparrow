# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import gc
import logging
import os

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.local import LocalManager
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response

import sparrow
import sparrow.api
import sparrow.auth
import sparrow.handler
import sparrow.monitor
import sparrow.rate_limiter
import sparrow.recorder
import sparrow.utils.response
from sparrow import _
from sparrow.core.doctype.comment.comment import update_comments_in_parent_after_request
from sparrow.middlewares import StaticDataMiddleware
from sparrow.utils import cint, get_site_name, sanitize_html
from sparrow.utils.data import escape_html
from sparrow.utils.error import make_error_snapshot
from sparrow.website.serve import get_response

local_manager = LocalManager(sparrow.local)

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")
SAFE_HTTP_METHODS = ("GET", "HEAD", "OPTIONS")
UNSAFE_HTTP_METHODS = ("POST", "PUT", "DELETE", "PATCH")


class RequestContext:
	def __init__(self, environ):
		self.request = Request(environ)

	def __enter__(self):
		init_request(self.request)

	def __exit__(self, type, value, traceback):
		sparrow.destroy()


# If gc.freeze is done then importing modules before forking allows us to share the memory
if sparrow._tune_gc:
	import bleach

	import sparrow.boot
	import sparrow.client
	import sparrow.core.doctype.file.file
	import sparrow.core.doctype.user.user
	import sparrow.database.mariadb.database  # Load database related utils
	import sparrow.database.query
	import sparrow.desk.desktop  # workspace
	import sparrow.desk.form.save
	import sparrow.model.db_query
	import sparrow.query_builder
	import sparrow.utils.background_jobs  # Enqueue is very common
	import sparrow.utils.data  # common utils
	import sparrow.utils.jinja  # web page rendering
	import sparrow.utils.jinja_globals
	import sparrow.utils.redis_wrapper  # Exact redis_wrapper
	import sparrow.utils.safe_exec
	import sparrow.website.path_resolver  # all the page types and resolver
	import sparrow.website.router  # Website router
	import sparrow.website.website_generator  # web page doctypes

# end: module pre-loading


@local_manager.middleware
@Request.application
def application(request: Request):
	response = None

	try:
		rollback = True

		init_request(request)

		sparrow.api.validate_auth()

		if request.method == "OPTIONS":
			response = Response()

		elif sparrow.form_dict.cmd:
			response = sparrow.handler.handle()

		elif request.path.startswith("/api/"):
			response = sparrow.api.handle()

		elif request.path.startswith("/backups"):
			response = sparrow.utils.response.download_backup(request.path)

		elif request.path.startswith("/private/files/"):
			response = sparrow.utils.response.download_private_file(request.path)

		elif request.method in ("GET", "HEAD", "POST"):
			response = get_response()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = sync_database(rollback)

	finally:
		# Important note:
		# this function *must* always return a response, hence any exception thrown outside of
		# try..catch block like this finally block needs to be handled appropriately.

		if request.method in UNSAFE_HTTP_METHODS and sparrow.db and rollback:
			sparrow.db.rollback()

		try:
			run_after_request_hooks(request, response)
		except Exception as e:
			# We can not handle exceptions safely here.
			sparrow.logger().error("Failed to run after request hook", exc_info=True)

		log_request(request, response)
		process_response(response)
		sparrow.destroy()

	return response


def run_after_request_hooks(request, response):
	if not getattr(sparrow.local, "initialised", False):
		return

	for after_request_task in sparrow.get_hooks("after_request"):
		sparrow.call(after_request_task, response=response, request=request)


def init_request(request):
	sparrow.local.request = request
	sparrow.local.is_ajax = sparrow.get_request_header("X-Requested-With") == "XMLHttpRequest"

	site = _site or request.headers.get("X-Sparrow-Site-Name") or get_site_name(request.host)
	sparrow.init(site=site, sites_path=_sites_path, force=True)

	if not (sparrow.local.conf and sparrow.local.conf.db_name):
		# site does not exist
		raise NotFound

	if sparrow.local.conf.maintenance_mode:
		sparrow.connect()
		if sparrow.local.conf.allow_reads_during_maintenance:
			setup_read_only_mode()
		else:
			raise sparrow.SessionStopped("Session Stopped")
	else:
		sparrow.connect(set_admin_as_user=False)

	request.max_content_length = cint(sparrow.local.conf.get("max_file_size")) or 10 * 1024 * 1024

	make_form_dict(request)

	if request.method != "OPTIONS":
		sparrow.local.http_request = sparrow.auth.HTTPRequest()

	for before_request_task in sparrow.get_hooks("before_request"):
		sparrow.call(before_request_task)


def setup_read_only_mode():
	"""During maintenance_mode reads to DB can still be performed to reduce downtime. This
	function sets up read only mode

	- Setting global flag so other pages, desk and database can know that we are in read only mode.
	- Setup read only database access either by:
	    - Connecting to read replica if one exists
	    - Or setting up read only SQL transactions.
	"""
	sparrow.flags.read_only = True

	# If replica is available then just connect replica, else setup read only transaction.
	if sparrow.conf.read_from_replica:
		sparrow.connect_replica()
	else:
		sparrow.db.begin(read_only=True)


def log_request(request, response):
	if hasattr(sparrow.local, "conf") and sparrow.local.conf.enable_sparrow_logger:
		sparrow.logger("sparrow.web", allow_site=sparrow.local.site).info(
			{
				"site": get_site_name(request.host),
				"remote_addr": getattr(request, "remote_addr", "NOTFOUND"),
				"base_url": getattr(request, "base_url", "NOTFOUND"),
				"full_path": getattr(request, "full_path", "NOTFOUND"),
				"method": getattr(request, "method", "NOTFOUND"),
				"scheme": getattr(request, "scheme", "NOTFOUND"),
				"http_status_code": getattr(response, "status_code", "NOTFOUND"),
			}
		)


def process_response(response):
	if not response:
		return

	# set cookies
	if hasattr(sparrow.local, "cookie_manager"):
		sparrow.local.cookie_manager.flush_cookies(response=response)

	# rate limiter headers
	if hasattr(sparrow.local, "rate_limiter"):
		response.headers.extend(sparrow.local.rate_limiter.headers())

	# CORS headers
	if hasattr(sparrow.local, "conf"):
		set_cors_headers(response)


def set_cors_headers(response):
	if not (
		(allowed_origins := sparrow.conf.allow_cors)
		and (request := sparrow.local.request)
		and (origin := request.headers.get("Origin"))
	):
		return

	if allowed_origins != "*":
		if not isinstance(allowed_origins, list):
			allowed_origins = [allowed_origins]

		if origin not in allowed_origins:
			return

	cors_headers = {
		"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Origin": origin,
		"Vary": "Origin",
	}

	# only required for preflight requests
	if request.method == "OPTIONS":
		cors_headers["Access-Control-Allow-Methods"] = request.headers.get(
			"Access-Control-Request-Method"
		)

		if allowed_headers := request.headers.get("Access-Control-Request-Headers"):
			cors_headers["Access-Control-Allow-Headers"] = allowed_headers

		# allow browsers to cache preflight requests for upto a day
		if not sparrow.conf.developer_mode:
			cors_headers["Access-Control-Max-Age"] = "86400"

	response.headers.extend(cors_headers)


def make_form_dict(request):
	import json

	request_data = request.get_data(as_text=True)
	if "application/json" in (request.content_type or "") and request_data:
		args = json.loads(request_data)
	else:
		args = {}
		args.update(request.args or {})
		args.update(request.form or {})

	if not isinstance(args, dict):
		sparrow.throw(_("Invalid request arguments"))

	sparrow.local.form_dict = sparrow._dict(args)

	if "_" in sparrow.local.form_dict:
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		sparrow.local.form_dict.pop("_")


def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	return_as_message = False
	accept_header = sparrow.get_request_header("Accept") or ""
	respond_as_json = (
		sparrow.get_request_header("Accept")
		and (sparrow.local.is_ajax or "application/json" in accept_header)
		or (sparrow.local.request.path.startswith("/api/") and not accept_header.startswith("text"))
	)

	if not sparrow.session.user:
		# If session creation fails then user won't be unset. This causes a lot of code that
		# assumes presence of this to fail. Session creation fails => guest or expired login
		# usually.
		sparrow.session.user = "Guest"

	if respond_as_json:
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = sparrow.utils.response.report_error(http_status_code)

	elif isinstance(e, sparrow.SessionStopped):
		response = sparrow.utils.response.handle_session_stopped()

	elif (
		http_status_code == 500
		and (sparrow.db and isinstance(e, sparrow.db.InternalError))
		and (sparrow.db and (sparrow.db.is_deadlocked(e) or sparrow.db.is_timedout(e)))
	):
		http_status_code = 508

	elif http_status_code == 401:
		sparrow.respond_as_web_page(
			_("Session Expired"),
			_("Your session has expired, please login again to continue."),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 403:
		sparrow.respond_as_web_page(
			_("Not Permitted"),
			_("You do not have enough permissions to complete the action"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 404:
		sparrow.respond_as_web_page(
			_("Not Found"),
			_("The resource you are looking for is not available"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 429:
		response = sparrow.rate_limiter.respond()

	else:
		traceback = "<pre>" + escape_html(sparrow.get_traceback()) + "</pre>"
		# disable traceback in production if flag is set
		if sparrow.local.flags.disable_traceback and not sparrow.local.dev_server:
			traceback = ""

		sparrow.respond_as_web_page(
			"Server Error", traceback, http_status_code=http_status_code, indicator_color="red", width=640
		)
		return_as_message = True

	if e.__class__ == sparrow.AuthenticationError:
		if hasattr(sparrow.local, "login_manager"):
			sparrow.local.login_manager.clear_cookies()

	if http_status_code >= 500:
		make_error_snapshot(e)

	if return_as_message:
		response = get_response("message", http_status_code=http_status_code)

	if sparrow.conf.get("developer_mode") and not respond_as_json:
		# don't fail silently for non-json response errors
		print(sparrow.get_traceback())

	return response


def sync_database(rollback: bool) -> bool:
	# if HTTP method would change server state, commit if necessary
	if (
		sparrow.db
		and (sparrow.local.flags.commit or sparrow.local.request.method in UNSAFE_HTTP_METHODS)
		and sparrow.db.transaction_writes
	):
		sparrow.db.commit()
		rollback = False
	elif sparrow.db:
		sparrow.db.rollback()
		rollback = False

	# update session
	if session := getattr(sparrow.local, "session_obj", None):
		if session.update():
			sparrow.db.commit()
			rollback = False

	update_comments_in_parent_after_request()

	return rollback


def serve(
	port=8000, profile=False, no_reload=False, no_threading=False, site=None, sites_path="."
):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	if profile or os.environ.get("USE_PROFILER"):
		application = ProfilerMiddleware(application, sort_by=("cumtime", "calls"))

	if not os.environ.get("NO_STATICS"):
		application = SharedDataMiddleware(
			application, {"/assets": str(os.path.join(sites_path, "assets"))}
		)

		application = StaticDataMiddleware(application, {"/files": str(os.path.abspath(sites_path))})

	application.debug = True
	application.config = {"SERVER_NAME": "127.0.0.1:8000"}

	log = logging.getLogger("werkzeug")
	log.propagate = False

	in_test_env = os.environ.get("CI")
	if in_test_env:
		log.setLevel(logging.ERROR)

	run_simple(
		"0.0.0.0",
		int(port),
		application,
		exclude_patterns=["test_*"],
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading,
	)


# Both Gunicorn and RQ use forking to spawn workers. In an ideal world, the fork should be sharing
# most of the memory if there are no writes made to data because of Copy on Write, however,
# python's GC is not CoW friendly and writes to data even if user-code doesn't. Specifically, the
# generational GC which stores and mutates every python object: `PyGC_Head`
#
# Calling gc.freeze() moves all the objects imported so far into permanant generation and hence
# doesn't mutate `PyGC_Head`
#
# Refer to issue for more info: https://github.com/sparrownova/sparrow/issues/18927
if sparrow._tune_gc:
	gc.collect()  # clean up any garbage created so far before freeze
	gc.freeze()
