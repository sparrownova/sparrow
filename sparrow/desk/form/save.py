# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow.desk.form.load import run_onload
from sparrow.model.docstatus import DocStatus
from sparrow.monitor import add_data_to_monitor
from sparrow.utils.telemetry import capture_doc


@sparrow.whitelist()
def savedocs(doc, action):
	"""save / submit / update doclist"""
	doc = sparrow.get_doc(json.loads(doc))
	capture_doc(doc, action)
	set_local_name(doc)

	# action
	doc.docstatus = {
		"Save": DocStatus.draft(),
		"Submit": DocStatus.submitted(),
		"Update": DocStatus.submitted(),
		"Cancel": DocStatus.cancelled(),
	}[action]

	doc.save()

	# update recent documents
	run_onload(doc)
	send_updated_docs(doc)

	add_data_to_monitor(doctype=doc.doctype, action=action)

	sparrow.msgprint(sparrow._("Saved"), indicator="green", alert=True)


@sparrow.whitelist()
def cancel(doctype=None, name=None, workflow_state_fieldname=None, workflow_state=None):
	"""cancel a doclist"""
	doc = sparrow.get_doc(doctype, name)
	capture_doc(doc, "Cancel")

	if workflow_state_fieldname and workflow_state:
		doc.set(workflow_state_fieldname, workflow_state)
	doc.cancel()
	send_updated_docs(doc)
	sparrow.msgprint(sparrow._("Cancelled"), indicator="red", alert=True)


def send_updated_docs(doc):
	from .load import get_docinfo

	get_docinfo(doc)

	d = doc.as_dict()
	if hasattr(doc, "localname"):
		d["localname"] = doc.localname

	sparrow.response.docs.append(d)


def set_local_name(doc):
	def _set_local_name(d):
		if doc.get("__islocal") or d.get("__islocal"):
			d.localname = d.name
			d.name = None

	_set_local_name(doc)
	for child in doc.get_all_children():
		_set_local_name(child)

	if doc.get("__newname"):
		doc.name = doc.get("__newname")
