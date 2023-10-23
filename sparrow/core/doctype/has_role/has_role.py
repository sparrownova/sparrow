# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class HasRole(Document):
	def before_insert(self):
		if sparrow.db.exists("Has Role", {"parent": self.parent, "role": self.role}):
			sparrow.throw(sparrow._("User '{0}' already has the role '{1}'").format(self.parent, self.role))
