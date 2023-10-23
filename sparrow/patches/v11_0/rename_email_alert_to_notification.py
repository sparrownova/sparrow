import sparrow
from sparrow.model.rename_doc import rename_doc


def execute():
	if sparrow.db.table_exists("Email Alert Recipient") and not sparrow.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		sparrow.reload_doc("email", "doctype", "notification_recipient")

	if sparrow.db.table_exists("Email Alert") and not sparrow.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		sparrow.reload_doc("email", "doctype", "notification")
