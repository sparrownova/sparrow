# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class NotificationSettings(Document):
	def on_update(self):
		from sparrow.desk.notifications import clear_notification_config

		clear_notification_config(sparrow.session.user)


def is_notifications_enabled(user):
	enabled = sparrow.db.get_value("Notification Settings", user, "enabled")
	if enabled is None:
		return True
	return enabled


def is_email_notifications_enabled(user):
	enabled = sparrow.db.get_value("Notification Settings", user, "enable_email_notifications")
	if enabled is None:
		return True
	return enabled


def is_email_notifications_enabled_for_type(user, notification_type):
	if not is_email_notifications_enabled(user):
		return False

	if notification_type == "Alert":
		return False

	fieldname = "enable_email_" + sparrow.scrub(notification_type)
	enabled = sparrow.db.get_value("Notification Settings", user, fieldname)
	if enabled is None:
		return True
	return enabled


def create_notification_settings(user):
	if not sparrow.db.exists("Notification Settings", user):
		_doc = sparrow.new_doc("Notification Settings")
		_doc.name = user
		_doc.insert(ignore_permissions=True)


def toggle_notifications(user: str, enable: bool = False):
	try:
		settings = sparrow.get_doc("Notification Settings", user)
	except sparrow.DoesNotExistError:
		sparrow.clear_last_message()
		return

	if settings.enabled != enable:
		settings.enabled = enable
		settings.save()


@sparrow.whitelist()
def get_subscribed_documents():
	if not sparrow.session.user:
		return []

	try:
		if sparrow.db.exists("Notification Settings", sparrow.session.user):
			doc = sparrow.get_doc("Notification Settings", sparrow.session.user)
			return [item.document for item in doc.subscribed_documents]
	# Notification Settings is fetched even before sync doctype is called
	# but it will throw an ImportError, we can ignore it in migrate
	except ImportError:
		pass

	return []


def get_permission_query_conditions(user):
	if not user:
		user = sparrow.session.user

	if user == "Administrator":
		return

	roles = sparrow.get_roles(user)
	if "System Manager" in roles:
		return """(`tabNotification Settings`.name != 'Administrator')"""

	return f"""(`tabNotification Settings`.name = {sparrow.db.escape(user)})"""


@sparrow.whitelist()
def set_seen_value(value, user):
	sparrow.db.set_value("Notification Settings", user, "seen", value, update_modified=False)
