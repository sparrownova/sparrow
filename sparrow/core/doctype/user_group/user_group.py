# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow

# import sparrow
from sparrow.model.document import Document


class UserGroup(Document):
	def after_insert(self):
		sparrow.cache().delete_key("user_groups")

	def on_trash(self):
		sparrow.cache().delete_key("user_groups")
