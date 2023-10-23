# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

from urllib.parse import parse_qsl

import sparrow
from sparrow import _
from sparrow.twofactor import get_qr_svg_code


def get_context(context):
	context.no_cache = 1
	context.qr_code_user, context.qrcode_svg = get_user_svg_from_cache()


def get_query_key():
	"""Return query string arg."""
	query_string = sparrow.local.request.query_string
	query = dict(parse_qsl(query_string))
	query = {key.decode(): val.decode() for key, val in query.items()}
	if not "k" in list(query):
		sparrow.throw(_("Not Permitted"), sparrow.PermissionError)
	query = (query["k"]).strip()
	if False in [i.isalpha() or i.isdigit() for i in query]:
		sparrow.throw(_("Not Permitted"), sparrow.PermissionError)
	return query


def get_user_svg_from_cache():
	"""Get User and SVG code from cache."""
	key = get_query_key()
	totp_uri = sparrow.cache().get_value(f"{key}_uri")
	user = sparrow.cache().get_value(f"{key}_user")
	if not totp_uri or not user:
		sparrow.throw(_("Page has expired!"), sparrow.PermissionError)
	if not sparrow.db.exists("User", user):
		sparrow.throw(_("Not Permitted"), sparrow.PermissionError)
	user = sparrow.get_doc("User", user)
	svg = get_qr_svg_code(totp_uri)
	return (user, svg.decode())
