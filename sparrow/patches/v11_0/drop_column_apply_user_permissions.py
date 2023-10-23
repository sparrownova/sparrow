import sparrow


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if sparrow.db.table_exists(doctype):
			if column in sparrow.db.get_table_columns(doctype):
				sparrow.db.sql(f"alter table `tab{doctype}` drop column {column}")

	sparrow.reload_doc("core", "doctype", "docperm", force=True)
	sparrow.reload_doc("core", "doctype", "custom_docperm", force=True)
