# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class Currency(Document):
	def validate(self):
		if not sparrow.flags.in_install_app:
			sparrow.clear_cache()
