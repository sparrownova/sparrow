# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import base64
import binascii
import json
from urllib.parse import urlencode, urlparse

import sparrow
import sparrow.client
import sparrow.handler
from sparrow import _
from sparrow.utils.data import sbool
from sparrow.utils.response import build_response


def handle():
	"""
	Handler for `/api` methods

	### Examples:

	`/api/method/{methodname}` will call a whitelisted method

	`/api/resource/{doctype}` will query a table
	        examples:
	        - `?fields=["name", "owner"]`
	        - `?filters=[["Task", "name", "like", "%005"]]`
	        - `?limit_start=0`
	        - `?limit_page_length=20`

	`/api/resource/{doctype}/{name}` will point to a resource
	        `GET` will return doclist
	        `POST` will insert
	        `PUT` will update
	        `DELETE` will delete

	`/api/resource/{doctype}/{name}?run_method={method}` will run a whitelisted controller method
	"""

	parts = sparrow.request.path[1:].split("/", 3)
	call = doctype = name = None

	if len(parts) > 1:
		call = parts[1]

	if len(parts) > 2:
		doctype = parts[2]

	if len(parts) > 3:
		name = parts[3]

	if call == "method":
		sparrow.local.form_dict.cmd = doctype
		return sparrow.handler.handle()

	elif call == "resource":
		if "run_method" in sparrow.local.form_dict:
			method = sparrow.local.form_dict.pop("run_method")
			doc = sparrow.get_doc(doctype, name)
			doc.is_whitelisted(method)

			if sparrow.local.request.method == "GET":
				if not doc.has_permission("read"):
					sparrow.throw(_("Not permitted"), sparrow.PermissionError)
				sparrow.local.response.update({"data": doc.run_method(method, **sparrow.local.form_dict)})

			if sparrow.local.request.method == "POST":
				if not doc.has_permission("write"):
					sparrow.throw(_("Not permitted"), sparrow.PermissionError)

				sparrow.local.response.update({"data": doc.run_method(method, **sparrow.local.form_dict)})
				sparrow.db.commit()

		else:
			if name:
				if sparrow.local.request.method == "GET":
					doc = sparrow.get_doc(doctype, name)
					if not doc.has_permission("read"):
						raise sparrow.PermissionError
					if sparrow.get_system_settings("apply_perm_level_on_api_calls"):
						doc.apply_fieldlevel_read_permissions()
					sparrow.local.response.update({"data": doc})

				if sparrow.local.request.method == "PUT":
					data = get_request_form_data()

					doc = sparrow.get_doc(doctype, name, for_update=True)

					if "flags" in data:
						del data["flags"]

					# Not checking permissions here because it's checked in doc.save
					doc.update(data)
					doc.save()
					if sparrow.get_system_settings("apply_perm_level_on_api_calls"):
						doc.apply_fieldlevel_read_permissions()
					sparrow.local.response.update({"data": doc})

					# check for child table doctype
					if doc.get("parenttype"):
						sparrow.get_doc(doc.parenttype, doc.parent).save()

					sparrow.db.commit()

				if sparrow.local.request.method == "DELETE":
					# Not checking permissions here because it's checked in delete_doc
					sparrow.delete_doc(doctype, name, ignore_missing=False)
					sparrow.local.response.http_status_code = 202
					sparrow.local.response.message = "ok"
					sparrow.db.commit()

			elif doctype:
				if sparrow.local.request.method == "GET":
					# set fields for sparrow.get_list
					if sparrow.local.form_dict.get("fields"):
						sparrow.local.form_dict["fields"] = json.loads(sparrow.local.form_dict["fields"])

					# set limit of records for sparrow.get_list
					sparrow.local.form_dict.setdefault(
						"limit_page_length",
                        sparrow.local.form_dict.limit or sparrow.local.form_dict.limit_page_length or 20,
					)

					# convert strings to native types - only as_dict and debug accept bool
					for param in ["as_dict", "debug"]:
						param_val = sparrow.local.form_dict.get(param)
						if param_val is not None:
							sparrow.local.form_dict[param] = sbool(param_val)

					# evaluate sparrow.get_list
					data = sparrow.call(sparrow.client.get_list, doctype, **sparrow.local.form_dict)

					# set sparrow.get_list result to response
					sparrow.local.response.update({"data": data})

				if sparrow.local.request.method == "POST":
					# fetch data from from dict
					data = get_request_form_data()
					data.update({"doctype": doctype})

					# insert document from request data
					doc = sparrow.get_doc(data).insert()

					# set response data
					sparrow.local.response.update({"data": doc.as_dict()})

					# commit for POST requests
					sparrow.db.commit()
			else:
				raise sparrow.DoesNotExistError

	else:
		raise sparrow.DoesNotExistError

	return build_response("json")


def get_request_form_data():
	if sparrow.local.form_dict.data is None:
		data = sparrow.safe_decode(sparrow.local.request.get_data())
	else:
		data = sparrow.local.form_dict.data

	try:
		return sparrow.parse_json(data)
	except ValueError:
		return sparrow.local.form_dict


def validate_auth():
	"""
	Authenticate and sets user for the request.
	"""
	authorization_header = sparrow.get_request_header("Authorization", "").split(" ")

	if len(authorization_header) == 2:
		validate_oauth(authorization_header)
		validate_auth_via_api_keys(authorization_header)

	validate_auth_via_hooks()


def validate_oauth(authorization_header):
	"""
	Authenticate request using OAuth and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	from sparrow.integrations.oauth2 import get_oauth_server
	from sparrow.oauth import get_url_delimiter

	form_dict = sparrow.local.form_dict
	token = authorization_header[1]
	req = sparrow.request
	parsed_url = urlparse(req.url)
	access_token = {"access_token": token}
	uri = (
		parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
	)
	http_method = req.method
	headers = req.headers
	body = req.get_data()
	if req.content_type and "multipart/form-data" in req.content_type:
		body = None

	try:
		required_scopes = sparrow.db.get_value("OAuth Bearer Token", token, "scopes").split(
			get_url_delimiter()
		)
		valid, oauthlib_request = get_oauth_server().verify_request(
			uri, http_method, body, headers, required_scopes
		)
		if valid:
			sparrow.set_user(sparrow.db.get_value("OAuth Bearer Token", token, "user"))
			sparrow.local.form_dict = form_dict
	except AttributeError:
		pass


def validate_auth_via_api_keys(authorization_header):
	"""
	Authenticate request using API keys and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	try:
		auth_type, auth_token = authorization_header
		authorization_source = sparrow.get_request_header("Sparrow-Authorization-Source")
		if auth_type.lower() == "basic":
			api_key, api_secret = sparrow.safe_decode(base64.b64decode(auth_token)).split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
		elif auth_type.lower() == "token":
			api_key, api_secret = auth_token.split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
	except binascii.Error:
		sparrow.throw(
			_("Failed to decode token, please provide a valid base64-encoded token."),
			sparrow.InvalidAuthorizationToken,
		)
	except (AttributeError, TypeError, ValueError):
		pass


def validate_api_key_secret(api_key, api_secret, sparrow_authorization_source=None):
	"""sparrow_authorization_source to provide api key and secret for a doctype apart from User"""
	doctype = sparrow_authorization_source or "User"
	doc = sparrow.db.get_value(doctype=doctype, filters={"api_key": api_key}, fieldname=["name"])
	form_dict = sparrow.local.form_dict
	doc_secret = sparrow.utils.password.get_decrypted_password(doctype, doc, fieldname="api_secret")
	if api_secret == doc_secret:
		if doctype == "User":
			user = sparrow.db.get_value(doctype="User", filters={"api_key": api_key}, fieldname=["name"])
		else:
			user = sparrow.db.get_value(doctype, doc, "user")
		if sparrow.local.login_manager.user in ("", "Guest"):
			sparrow.set_user(user)
		sparrow.local.form_dict = form_dict


def validate_auth_via_hooks():
	for auth_hook in sparrow.get_hooks("auth_hooks", []):
		sparrow.get_attr(auth_hook)()
