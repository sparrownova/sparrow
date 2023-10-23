# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document
from sparrow.utils import cint


class BulkUpdate(Document):
	@sparrow.whitelist()
	def bulk_update(self):
		self.check_permission("write")
		limit = self.limit if self.limit and cint(self.limit) < 500 else 500

		condition = ""
		if self.condition:
			if ";" in self.condition:
				sparrow.throw(_("; not allowed in condition"))

			condition = f" where {self.condition}"

		docnames = sparrow.db.sql_list(
			f"""select name from `tab{self.document_type}`{condition} limit {limit} offset 0"""
		)
		return submit_cancel_or_update_docs(
			self.document_type, docnames, "update", {self.field: self.update_value}
		)


@sparrow.whitelist()
def submit_cancel_or_update_docs(doctype, docnames, action="submit", data=None):
	docnames = sparrow.parse_json(docnames)

	if data:
		data = sparrow.parse_json(data)

	failed = []

	for i, d in enumerate(docnames, 1):
		doc = sparrow.get_doc(doctype, d)
		try:
			message = ""
			if action == "submit" and doc.docstatus.is_draft():
				doc.submit()
				message = _("Submitting {0}").format(doctype)
			elif action == "cancel" and doc.docstatus.is_submitted():
				doc.cancel()
				message = _("Cancelling {0}").format(doctype)
			elif action == "update" and not doc.docstatus.is_cancelled():
				doc.update(data)
				doc.save()
				message = _("Updating {0}").format(doctype)
			else:
				failed.append(d)
			sparrow.db.commit()
			show_progress(docnames, message, i, d)

		except Exception:
			failed.append(d)
			sparrow.db.rollback()

	return failed


def show_progress(docnames, message, i, description):
	n = len(docnames)
	if n >= 10:
		sparrow.publish_progress(float(i) * 100 / n, title=message, description=description)
