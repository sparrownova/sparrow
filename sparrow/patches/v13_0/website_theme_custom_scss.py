import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "website_theme_ignore_app")
	sparrow.reload_doc("website", "doctype", "color")
	sparrow.reload_doc("website", "doctype", "website_theme")
	sparrow.reload_doc("website", "doctype", "website_settings")

	for theme in sparrow.get_all("Website Theme"):
		doc = sparrow.get_doc("Website Theme", theme.name)
		if not doc.get("custom_scss") and doc.theme_scss:
			# move old theme to new theme
			doc.custom_scss = doc.theme_scss

			if doc.background_color:
				setup_color_record(doc.background_color)

			doc.save()


def setup_color_record(color):
	sparrow.get_doc(
		{
			"doctype": "Color",
			"__newname": color,
			"color": color,
		}
	).save()
