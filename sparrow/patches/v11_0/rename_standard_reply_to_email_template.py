import sparrow
from sparrow.model.rename_doc import rename_doc


def execute():
	if sparrow.db.table_exists("Standard Reply") and not sparrow.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		sparrow.reload_doc("email", "doctype", "email_template")
