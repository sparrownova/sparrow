# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE
from tenacity import retry, retry_if_exception_type, stop_after_attempt

import sparrow
from sparrow.model.document import Document
from sparrow.utils import cstr


class AccessLog(Document):
	pass


@sparrow.whitelist()
def make_access_log(
	doctype=None,
	document=None,
	method=None,
	file_type=None,
	report_name=None,
	filters=None,
	page=None,
	columns=None,
):
	_make_access_log(
		doctype,
		document,
		method,
		file_type,
		report_name,
		filters,
		page,
		columns,
	)


@sparrow.write_only()
@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(sparrow.DuplicateEntryError))
def _make_access_log(
	doctype=None,
	document=None,
	method=None,
	file_type=None,
	report_name=None,
	filters=None,
	page=None,
	columns=None,
):
	user = sparrow.session.user
	in_request = sparrow.request and sparrow.request.method == "GET"

	sparrow.get_doc(
		{
			"doctype": "Access Log",
			"user": user,
			"export_from": doctype,
			"reference_document": document,
			"file_type": file_type,
			"report_name": report_name,
			"page": page,
			"method": method,
			"filters": cstr(filters) or None,
			"columns": columns,
		}
	).db_insert()

	# `sparrow.db.commit` added because insert doesnt `commit` when called in GET requests like `printview`
	# dont commit in test mode. It must be tempting to put this block along with the in_request in the
	# whitelisted method...yeah, don't do it. That part would be executed possibly on a read only DB conn
	if not sparrow.flags.in_test or in_request:
		sparrow.db.commit()
