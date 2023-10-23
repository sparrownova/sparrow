# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "website_theme_ignore_app")
	themes = sparrow.get_all(
		"Website Theme", filters={"theme_url": ("not like", "/files/website_theme/%")}
	)
	for theme in themes:
		doc = sparrow.get_doc("Website Theme", theme.name)
		try:
			doc.generate_bootstrap_theme()
			doc.save()
		except Exception:
			print("Ignoring....")
			print(sparrow.get_traceback())
