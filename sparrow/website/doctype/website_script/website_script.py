# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class WebsiteScript(Document):
	def on_update(self):
		"""clear cache"""
		sparrow.clear_cache(user="Guest")

		from sparrow.website.utils import clear_cache

		clear_cache()
