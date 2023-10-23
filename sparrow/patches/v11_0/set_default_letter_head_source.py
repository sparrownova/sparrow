import sparrow


def execute():
	sparrow.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	sparrow.db.sql("update `tabLetter Head` set source = 'HTML'")
