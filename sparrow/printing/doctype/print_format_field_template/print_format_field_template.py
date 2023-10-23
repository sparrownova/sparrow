# Copyright (c) 2021, Sparrow Technologies and contributors
# For license information, please see license.txt

import sparrow
from sparrow import _
from sparrow.model.document import Document


class PrintFormatFieldTemplate(Document):
	def validate(self):
		if self.standard and not (sparrow.conf.developer_mode or sparrow.flags.in_patch):
			sparrow.throw(_("Enable developer mode to create a standard Print Template"))

	def before_insert(self):
		self.validate_duplicate()

	def on_update(self):
		self.validate_duplicate()
		self.export_doc()

	def validate_duplicate(self):
		if not self.standard:
			return
		if not self.field:
			return

		filters = {"document_type": self.document_type, "field": self.field}
		if not self.is_new():
			filters.update({"name": ("!=", self.name)})
		result = sparrow.get_all("Print Format Field Template", filters=filters, limit=1)
		if result:
			sparrow.throw(
				_("A template already exists for field {0} of {1}").format(
					sparrow.bold(self.field), sparrow.bold(self.document_type)
				),
				sparrow.DuplicateEntryError,
				title=_("Duplicate Entry"),
			)

	def export_doc(self):
		from sparrow.modules.utils import export_module_json

		export_module_json(self, self.standard, self.module)
