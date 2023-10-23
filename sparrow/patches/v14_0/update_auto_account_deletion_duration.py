import sparrow


def execute():
	days = sparrow.db.get_single_value("Website Settings", "auto_account_deletion")
	sparrow.db.set_single_value("Website Settings", "auto_account_deletion", days * 24)
