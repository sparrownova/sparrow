# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class AboutUsSettings(Document):
	def on_update(self):
		from sparrow.website.utils import clear_cache

		clear_cache("about")


def get_args():
	obj = sparrow.get_doc("About Us Settings")
	return {"obj": obj}
