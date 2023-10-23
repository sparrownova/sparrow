# Copyright (c) 2022, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import datetime
import decimal
import json
import mimetypes
import os
from typing import TYPE_CHECKING
from urllib.parse import quote

import werkzeug.utils
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.local import LocalProxy
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

import sparrow
import sparrow.model.document
import sparrow.sessions
import sparrow.utils
from sparrow import _
from sparrow.core.doctype.access_log.access_log import make_access_log
from sparrow.utils import cint, format_timedelta

if TYPE_CHECKING:
	from sparrow.core.doctype.file.file import File


def report_error(status_code):
	"""Build error. Show traceback in developer mode"""
	allow_traceback = (
		cint(sparrow.db.get_system_setting("allow_error_traceback")) if sparrow.db else True
	)
	if (
		allow_traceback
		and (status_code != 404 or sparrow.conf.logging)
		and not sparrow.local.flags.disable_traceback
	):
		traceback = sparrow.utils.get_traceback()
		if traceback:
			sparrow.errprint(traceback)
			sparrow.local.response.exception = traceback.splitlines()[-1]

	response = build_response("json")
	response.status_code = status_code
	return response


def build_response(response_type=None):
	if "docs" in sparrow.local.response and not sparrow.local.response.docs:
		del sparrow.local.response["docs"]

	response_type_map = {
		"csv": as_csv,
		"txt": as_txt,
		"download": as_raw,
		"json": as_json,
		"pdf": as_pdf,
		"page": as_page,
		"redirect": redirect,
		"binary": as_binary,
	}

	return response_type_map[sparrow.response.get("type") or response_type]()


def as_csv():
	response = Response()
	response.mimetype = "text/csv"
	response.charset = "utf-8"
	response.headers["Content-Disposition"] = (
		'attachment; filename="%s.csv"' % sparrow.response["doctype"].replace(" ", "_")
	).encode("utf-8")
	response.data = sparrow.response["result"]
	return response


def as_txt():
	response = Response()
	response.mimetype = "text"
	response.charset = "utf-8"
	response.headers["Content-Disposition"] = (
		'attachment; filename="%s.txt"' % sparrow.response["doctype"].replace(" ", "_")
	).encode("utf-8")
	response.data = sparrow.response["result"]
	return response


def as_raw():
	response = Response()
	response.mimetype = (
		sparrow.response.get("content_type")
		or mimetypes.guess_type(sparrow.response["filename"])[0]
		or "application/unknown"
	)
	response.headers["Content-Disposition"] = (
		f'{sparrow.response.get("display_content_as","attachment")}; filename="{sparrow.response["filename"].replace(" ", "_")}"'
	).encode()
	response.data = sparrow.response["filecontent"]
	return response


def as_json():
	make_logs()
	response = Response()
	if sparrow.local.response.http_status_code:
		response.status_code = sparrow.local.response["http_status_code"]
		del sparrow.local.response["http_status_code"]

	response.mimetype = "application/json"
	response.charset = "utf-8"
	response.data = json.dumps(sparrow.local.response, default=json_handler, separators=(",", ":"))
	return response


def as_pdf():
	response = Response()
	response.mimetype = "application/pdf"
	encoded_filename = quote(sparrow.response["filename"].replace(" ", "_"))
	response.headers["Content-Disposition"] = (
		'filename="%s"' % sparrow.response["filename"].replace(" ", "_")
		+ ";filename*=utf-8''%s" % encoded_filename
	).encode("utf-8")
	response.data = sparrow.response["filecontent"]
	return response


def as_binary():
	response = Response()
	response.mimetype = "application/octet-stream"
	filename = "_".join(sparrow.response["filename"].split())
	response.headers["Content-Disposition"] = ('filename="%s"' % filename).encode("utf-8")
	response.data = sparrow.response["filecontent"]
	return response


def make_logs(response=None):
	"""make strings for msgprint and errprint"""
	if not response:
		response = sparrow.local.response

	if sparrow.error_log:
		response["exc"] = json.dumps([sparrow.utils.cstr(d["exc"]) for d in sparrow.local.error_log])

	if sparrow.local.message_log:
		response["_server_messages"] = json.dumps(
			[sparrow.utils.cstr(d) for d in sparrow.local.message_log]
		)

	if sparrow.debug_log and sparrow.conf.get("logging") or False:
		response["_debug_messages"] = json.dumps(sparrow.local.debug_log)

	if sparrow.flags.error_message:
		response["_error_message"] = sparrow.flags.error_message


def json_handler(obj):
	"""serialize non-serializable data for json"""
	from collections.abc import Iterable
	from re import Match

	if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
		return str(obj)

	elif isinstance(obj, datetime.timedelta):
		return format_timedelta(obj)

	elif isinstance(obj, decimal.Decimal):
		return float(obj)

	elif isinstance(obj, LocalProxy):
		return str(obj)

	elif isinstance(obj, sparrow.model.document.BaseDocument):
		doc = obj.as_dict(no_nulls=True)
		return doc

	elif isinstance(obj, Iterable):
		return list(obj)

	elif isinstance(obj, Match):
		return obj.string

	elif type(obj) == type or isinstance(obj, Exception):
		return repr(obj)

	elif callable(obj):
		return repr(obj)

	else:
		raise TypeError(
			f"""Object of type {type(obj)} with value of {repr(obj)} is not JSON serializable"""
		)


def as_page():
	"""print web page"""
	from sparrow.website.serve import get_response

	return get_response(
		sparrow.response["route"], http_status_code=sparrow.response.get("http_status_code")
	)


def redirect():
	return werkzeug.utils.redirect(sparrow.response.location)


def download_backup(path):
	try:
		sparrow.only_for(("System Manager", "Administrator"))
		make_access_log(report_name="Backup")
	except sparrow.PermissionError:
		raise Forbidden(
			_("You need to be logged in and have System Manager Role to be able to access backups.")
		)

	return send_private_file(path)


def download_private_file(path: str) -> Response:
	"""Checks permissions and sends back private file"""

	files = sparrow.get_all("File", filters={"file_url": path}, fields="*")
	# this file might be attached to multiple documents
	# if the file is accessible from any one of those documents
	# then it should be downloadable
	for file_data in files:
		file: "File" = sparrow.get_doc(doctype="File", **file_data)
		if file.is_downloadable():
			break

	else:
		raise Forbidden(_("You don't have permission to access this file"))

	make_access_log(doctype="File", document=file.name, file_type=os.path.splitext(path)[-1][1:])
	return send_private_file(path.split("/private", 1)[1])


def send_private_file(path: str) -> Response:
	path = os.path.join(sparrow.local.conf.get("private_path", "private"), path.strip("/"))
	filename = os.path.basename(path)

	if sparrow.local.request.headers.get("X-Use-X-Accel-Redirect"):
		path = "/protected/" + path
		response = Response()
		response.headers["X-Accel-Redirect"] = quote(sparrow.utils.encode(path))

	else:
		filepath = sparrow.utils.get_site_path(path)
		try:
			f = open(filepath, "rb")
		except OSError:
			raise NotFound

		response = Response(wrap_file(sparrow.local.request.environ, f), direct_passthrough=True)

	# no need for content disposition and force download. let browser handle its opening.
	# Except for those that can be injected with scripts.

	extension = os.path.splitext(path)[1]
	blacklist = [".svg", ".html", ".htm", ".xml"]

	if extension.lower() in blacklist:
		response.headers.add("Content-Disposition", "attachment", filename=filename.encode("utf-8"))

	response.mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

	return response


def handle_session_stopped():
	from sparrow.website.serve import get_response

	sparrow.respond_as_web_page(
		_("Updating"),
		_("The system is being updated. Please refresh again after a few moments."),
		http_status_code=503,
		indicator_color="orange",
		fullpage=True,
		primary_action=None,
	)
	return get_response("message", http_status_code=503)
