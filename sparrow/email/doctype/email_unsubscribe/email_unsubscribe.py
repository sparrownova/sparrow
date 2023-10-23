# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document


class EmailUnsubscribe(Document):
	def validate(self):
		if not self.global_unsubscribe and not (self.reference_doctype and self.reference_name):
			sparrow.throw(_("Reference DocType and Reference Name are required"), sparrow.MandatoryError)

		if not self.global_unsubscribe and sparrow.db.get_value(
			self.doctype, self.name, "global_unsubscribe"
		):
			sparrow.throw(_("Delete this record to allow sending to this email address"))

		if self.global_unsubscribe:
			if sparrow.get_all(
				"Email Unsubscribe",
				filters={"email": self.email, "global_unsubscribe": 1, "name": ["!=", self.name]},
			):
				sparrow.throw(_("{0} already unsubscribed").format(self.email), sparrow.DuplicateEntryError)

		else:
			if sparrow.get_all(
				"Email Unsubscribe",
				filters={
					"email": self.email,
					"reference_doctype": self.reference_doctype,
					"reference_name": self.reference_name,
					"name": ["!=", self.name],
				},
			):
				sparrow.throw(
					_("{0} already unsubscribed for {1} {2}").format(
						self.email, self.reference_doctype, self.reference_name
					),
					sparrow.DuplicateEntryError,
				)

	def on_update(self):
		if self.reference_doctype and self.reference_name:
			doc = sparrow.get_doc(self.reference_doctype, self.reference_name)
			doc.add_comment("Label", _("Left this conversation"), comment_email=self.email)
