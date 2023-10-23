# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class EmailGroupMember(Document):
	def after_delete(self):
		email_group = sparrow.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()

	def after_insert(self):
		email_group = sparrow.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()


def after_doctype_insert():
	sparrow.db.add_unique("Email Group Member", ("email_group", "email"))
