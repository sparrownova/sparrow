# Copyright (c) 2017, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class PrintStyle(Document):
	def validate(self):
		if (
			self.standard == 1
			and not sparrow.local.conf.get("developer_mode")
			and not (sparrow.flags.in_import or sparrow.flags.in_test)
		):

			sparrow.throw(sparrow._("Standard Print Style cannot be changed. Please duplicate to edit."))

	def on_update(self):
		self.export_doc()

	def export_doc(self):
		# export
		from sparrow.modules.utils import export_module_json

		export_module_json(self, self.standard == 1, "Printing")
