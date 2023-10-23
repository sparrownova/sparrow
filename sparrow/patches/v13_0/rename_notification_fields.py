# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.utils.rename_field import rename_field


def execute():
	"""
	Change notification recipient fields from email to receiver fields
	"""
	sparrow.reload_doc("Email", "doctype", "Notification Recipient")
	sparrow.reload_doc("Email", "doctype", "Notification")

	rename_field("Notification Recipient", "email_by_document_field", "receiver_by_document_field")
	rename_field("Notification Recipient", "email_by_role", "receiver_by_role")
