# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():

	sparrow.reload_doc("Email", "doctype", "Notification")

	notifications = sparrow.get_all("Notification", {"is_standard": 1}, {"name", "channel"})
	for notification in notifications:
		if not notification.channel:
			sparrow.db.set_value(
				"Notification", notification.name, "channel", "Email", update_modified=False
			)
			sparrow.db.commit()
