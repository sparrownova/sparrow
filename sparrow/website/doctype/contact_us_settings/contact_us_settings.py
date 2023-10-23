# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class ContactUsSettings(Document):
	def on_update(self):
		from sparrow.website.utils import clear_cache

		clear_cache("contact")
