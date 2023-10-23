# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "DocField")

	if sparrow.db.has_column("DocField", "show_days"):
		sparrow.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		sparrow.db.sql_ddl("alter table tabDocField drop column show_days")

	if sparrow.db.has_column("DocField", "show_seconds"):
		sparrow.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		sparrow.db.sql_ddl("alter table tabDocField drop column show_seconds")

	sparrow.clear_cache(doctype="DocField")
