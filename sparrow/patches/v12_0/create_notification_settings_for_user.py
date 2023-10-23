import sparrow
from sparrow.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	sparrow.reload_doc("desk", "doctype", "notification_settings")
	sparrow.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = sparrow.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
