# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	"""Set default module for standard Web Template, if none."""
	sparrow.reload_doc("website", "doctype", "Web Template Field")
	sparrow.reload_doc("website", "doctype", "web_template")

	standard_templates = sparrow.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = sparrow.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
