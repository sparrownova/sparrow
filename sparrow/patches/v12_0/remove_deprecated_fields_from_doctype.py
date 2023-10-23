import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "doctype_link")
	sparrow.reload_doc("core", "doctype", "doctype_action")
	sparrow.reload_doc("core", "doctype", "doctype")
	sparrow.model.delete_fields(
		{"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1
	)

	sparrow.db.delete("Property Setter", {"property": "read_only_onload"})
