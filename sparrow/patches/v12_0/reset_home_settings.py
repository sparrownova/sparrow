import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "user")
	sparrow.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
