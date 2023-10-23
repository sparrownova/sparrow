import sparrow


def execute():
	"""Drop search index on message_id"""

	if sparrow.db.get_column_type("Email Queue", "message_id") == "text":
		return

	if index := sparrow.db.get_column_index("tabEmail Queue", "message_id", unique=False):
		sparrow.db.sql(f"ALTER TABLE `tabEmail Queue` DROP INDEX `{index.Key_name}`")
