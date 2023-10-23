# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	if not sparrow.db.table_exists("Data Import"):
		return

	meta = sparrow.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	sparrow.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	sparrow.rename_doc("DocType", "Data Import", "Data Import Legacy")
	sparrow.db.commit()
	sparrow.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	sparrow.rename_doc("DocType", "Data Import Beta", "Data Import")
