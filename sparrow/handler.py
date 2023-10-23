# Copyright (c) 2022, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import os
from mimetypes import guess_type
from typing import TYPE_CHECKING

from werkzeug.wrappers import Response

import sparrow
import sparrow.sessions
import sparrow.utils
from sparrow import _, is_whitelisted
from sparrow.core.doctype.server_script.server_script_utils import get_server_script_map
from sparrow.utils import cint
from sparrow.utils.csvutils import build_csv_response
from sparrow.utils.image import optimize_image
from sparrow.utils.response import build_response

if TYPE_CHECKING:
	from sparrow.core.doctype.file.file import File
	from sparrow.core.doctype.user.user import User

ALLOWED_MIMETYPES = (
	"image/png",
	"image/jpeg",
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"application/vnd.ms-excel",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"application/vnd.oasis.opendocument.text",
	"application/vnd.oasis.opendocument.spreadsheet",
	"text/plain",
	"video/quicktime",
	"video/mp4",
)


def handle():
	"""handle request"""

	cmd = sparrow.local.form_dict.cmd
	data = None

	if cmd != "login":
		data = execute_cmd(cmd)

	# data can be an empty string or list which are valid responses
	if data is not None:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		sparrow.response["message"] = data

	return build_response("json")


def execute_cmd(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in sparrow.get_hooks("override_whitelisted_methods", {}).get(cmd, []):
		# override using the first hook
		cmd = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(cmd)
	if server_script:
		return run_server_script(server_script)

	try:
		method = get_attr(cmd)
	except Exception as e:
		sparrow.throw(_("Failed to get method for command {0} with {1}").format(cmd, e))

	if from_async:
		method = method.queue

	if method != run_doc_method:
		is_whitelisted(method)
		is_valid_http_method(method)

	return sparrow.call(method, **sparrow.form_dict)


def run_server_script(server_script):
	response = sparrow.get_doc("Server Script", server_script).execute_method()

	# some server scripts return output using flags (empty dict by default),
	# while others directly modify sparrow.response
	# return flags if not empty dict (this overwrites sparrow.response.message)
	if response != {}:
		return response


def is_valid_http_method(method):
	if sparrow.flags.in_safe_exec:
		return

	http_method = sparrow.local.request.method

	if http_method not in sparrow.allowed_http_methods_for_whitelisted_func[method]:
		throw_permission_error()


def throw_permission_error():
	sparrow.throw(_("Not permitted"), sparrow.PermissionError)


@sparrow.whitelist(allow_guest=True)
def version():
	return sparrow.__version__


@sparrow.whitelist(allow_guest=True)
def logout():
	sparrow.local.login_manager.logout()
	sparrow.db.commit()


@sparrow.whitelist(allow_guest=True)
def web_logout():
	sparrow.local.login_manager.logout()
	sparrow.db.commit()
	sparrow.respond_as_web_page(
		_("Logged Out"), _("You have been successfully logged out"), indicator_color="green"
	)


@sparrow.whitelist()
def uploadfile():
	ret = None

	try:
		if sparrow.form_dict.get("from_form"):
			try:
				ret = sparrow.get_doc(
					{
						"doctype": "File",
						"attached_to_name": sparrow.form_dict.docname,
						"attached_to_doctype": sparrow.form_dict.doctype,
						"attached_to_field": sparrow.form_dict.docfield,
						"file_url": sparrow.form_dict.file_url,
						"file_name": sparrow.form_dict.filename,
						"is_private": sparrow.utils.cint(sparrow.form_dict.is_private),
						"content": sparrow.form_dict.filedata,
						"decode": True,
					}
				)
				ret.save()
			except sparrow.DuplicateEntryError:
				# ignore pass
				ret = None
				sparrow.db.rollback()
		else:
			if sparrow.form_dict.get("method"):
				method = sparrow.get_attr(sparrow.form_dict.method)
				is_whitelisted(method)
				ret = method()
	except Exception:
		sparrow.errprint(sparrow.utils.get_traceback())
		sparrow.response["http_status_code"] = 500
		ret = None

	return ret


@sparrow.whitelist(allow_guest=True)
def upload_file():
	user = None
	if sparrow.session.user == "Guest":
		if sparrow.get_system_settings("allow_guests_to_upload_files"):
			ignore_permissions = True
		else:
			raise sparrow.PermissionError
	else:
		user: "User" = sparrow.get_doc("User", sparrow.session.user)
		ignore_permissions = False

	files = sparrow.request.files
	is_private = sparrow.form_dict.is_private
	doctype = sparrow.form_dict.doctype
	docname = sparrow.form_dict.docname
	fieldname = sparrow.form_dict.fieldname
	file_url = sparrow.form_dict.file_url
	folder = sparrow.form_dict.folder or "Home"
	method = sparrow.form_dict.method
	filename = sparrow.form_dict.file_name
	optimize = sparrow.form_dict.optimize
	content = None

	if "file" in files:
		file = files["file"]
		content = file.stream.read()
		filename = file.filename

		content_type = guess_type(filename)[0]
		if optimize and content_type and content_type.startswith("image/"):
			args = {"content": content, "content_type": content_type}
			if sparrow.form_dict.max_width:
				args["max_width"] = int(sparrow.form_dict.max_width)
			if sparrow.form_dict.max_height:
				args["max_height"] = int(sparrow.form_dict.max_height)
			content = optimize_image(**args)

	sparrow.local.uploaded_file = content
	sparrow.local.uploaded_filename = filename

	if content is not None and (
		sparrow.session.user == "Guest" or (user and not user.has_desk_access())
	):
		filetype = guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			sparrow.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

	if method:
		method = sparrow.get_attr(method)
		is_whitelisted(method)
		return method()
	else:
		return sparrow.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": doctype,
				"attached_to_name": docname,
				"attached_to_field": fieldname,
				"folder": folder,
				"file_name": filename,
				"file_url": file_url,
				"is_private": cint(is_private),
				"content": content,
			}
		).save(ignore_permissions=ignore_permissions)


@sparrow.whitelist(allow_guest=True)
def download_file(file_url: str):
	"""
	Download file using token and REST API. Valid session or
	token is required to download private files.

	Method : GET
	Endpoints : download_file, sparrow.core.doctype.file.file.download_file
	URL Params : file_name = /path/to/file relative to site path
	"""
	file: "File" = sparrow.get_doc("File", {"file_url": file_url})
	if not file.is_downloadable():
		raise sparrow.PermissionError

	sparrow.local.response.filename = os.path.basename(file_url)
	sparrow.local.response.filecontent = file.get_content()
	sparrow.local.response.type = "download"


def get_attr(cmd):
	"""get method object from cmd"""
	if "." in cmd:
		method = sparrow.get_attr(cmd)
	else:
		method = globals()[cmd]
	sparrow.log("method:" + cmd)
	return method


@sparrow.whitelist(allow_guest=True)
def ping():
	return "pong"


def run_doc_method(method, docs=None, dt=None, dn=None, arg=None, args=None):
	"""run a whitelisted controller method"""
	from inspect import getfullargspec

	if not args and arg:
		args = arg

	if dt:  # not called from a doctype (from a page)
		if not dn:
			dn = dt  # single
		doc = sparrow.get_doc(dt, dn)

	else:
		docs = sparrow.parse_json(docs)
		doc = sparrow.get_doc(docs)
		doc._original_modified = doc.modified
		doc.check_if_latest()

	if not doc or not doc.has_permission("read"):
		throw_permission_error()

	try:
		args = sparrow.parse_json(args)
	except ValueError:
		pass

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	fnargs = getfullargspec(method_obj).args

	if not fnargs or (len(fnargs) == 1 and fnargs[0] == "self"):
		response = doc.run_method(method)

	elif "args" in fnargs or not isinstance(args, dict):
		response = doc.run_method(method, args)

	else:
		response = doc.run_method(method, **args)

	sparrow.response.docs.append(doc)
	if response is None:
		return

	# build output as csv
	if cint(sparrow.form_dict.get("as_csv")):
		build_csv_response(response, _(doc.doctype).replace(" ", ""))
		return

	sparrow.response["message"] = response


# for backwards compatibility
runserverobj = run_doc_method
