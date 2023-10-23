# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class CustomDocPerm(Document):
	def on_update(self):
		sparrow.clear_cache(doctype=self.parent)
