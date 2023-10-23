import sparrow


def execute():
	doctype = "Top Bar Item"
	if not sparrow.db.table_exists(doctype) or not sparrow.db.has_column(doctype, "target"):
		return

	sparrow.reload_doc("website", "doctype", "top_bar_item")
	sparrow.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
