# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.model.document import Document


class ClientScript(Document):
	def on_update(self):
		sparrow.clear_cache(doctype=self.dt)

	def on_trash(self):
		sparrow.clear_cache(doctype=self.dt)
