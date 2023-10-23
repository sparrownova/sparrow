# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.desk.doctype.bulk_update.bulk_update import show_progress
from sparrow.model.document import Document
from sparrow.model.workflow import get_workflow_name


class DeletedDocument(Document):
	pass


@sparrow.whitelist()
def restore(name, alert=True):
	deleted = sparrow.get_doc("Deleted Document", name)

	if deleted.restored:
		sparrow.throw(_("Document {0} Already Restored").format(name), exc=sparrow.DocumentAlreadyRestored)

	doc = sparrow.get_doc(json.loads(deleted.data))

	try:
		doc.insert()
	except sparrow.DocstatusTransitionError:
		sparrow.msgprint(_("Cancelled Document restored as Draft"))
		doc.docstatus = 0
		active_workflow = get_workflow_name(doc.doctype)
		if active_workflow:
			workflow_state_fieldname = sparrow.get_value("Workflow", active_workflow, "workflow_state_field")
			if doc.get(workflow_state_fieldname):
				doc.set(workflow_state_fieldname, None)
		doc.insert()

	doc.add_comment("Edit", _("restored {0} as {1}").format(deleted.deleted_name, doc.name))

	deleted.new_name = doc.name
	deleted.restored = 1
	deleted.db_update()

	if alert:
		sparrow.msgprint(_("Document Restored"))


@sparrow.whitelist()
def bulk_restore(docnames):
	docnames = sparrow.parse_json(docnames)
	message = _("Restoring Deleted Document")
	restored, invalid, failed = [], [], []

	for i, d in enumerate(docnames):
		try:
			show_progress(docnames, message, i + 1, d)
			restore(d, alert=False)
			sparrow.db.commit()
			restored.append(d)

		except sparrow.DocumentAlreadyRestored:
			sparrow.message_log.pop()
			invalid.append(d)

		except Exception:
			sparrow.message_log.pop()
			failed.append(d)
			sparrow.db.rollback()

	return {"restored": restored, "invalid": invalid, "failed": failed}
