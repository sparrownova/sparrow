import re

import sparrow


def execute():
	fields = sparrow.db.sql(
		"""
			SELECT COLUMN_NAME , TABLE_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
			WHERE DATA_TYPE IN ('INT', 'FLOAT', 'DECIMAL') AND IS_NULLABLE = 'YES'
		""",
		as_dict=1,
	)

	update_column_table_map = {}

	for field in fields:
		update_column_table_map.setdefault(field.TABLE_NAME, [])

		update_column_table_map[field.TABLE_NAME].append(
			"`{fieldname}`=COALESCE(`{fieldname}`, 0)".format(fieldname=field.COLUMN_NAME)
		)

	for table in sparrow.db.get_tables():
		if update_column_table_map.get(table) and sparrow.db.exists("DocType", re.sub("^tab", "", table)):
			sparrow.db.sql(
				"""UPDATE `{table}` SET {columns}""".format(
					table=table, columns=", ".join(update_column_table_map.get(table))
				)
			)
