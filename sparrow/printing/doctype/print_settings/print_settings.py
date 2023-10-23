# Copyright (c) 2018, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document
from sparrow.utils import cint


class PrintSettings(Document):
	def validate(self):
		if self.pdf_page_size == "Custom" and not (self.pdf_page_height and self.pdf_page_width):
			sparrow.throw(_("Page height and width cannot be zero"))

	def on_update(self):
		sparrow.clear_cache()


@sparrow.whitelist()
def is_print_server_enabled():
	if not hasattr(sparrow.local, "enable_print_server"):
		sparrow.local.enable_print_server = cint(
			sparrow.db.get_single_value("Print Settings", "enable_print_server")
		)

	return sparrow.local.enable_print_server
