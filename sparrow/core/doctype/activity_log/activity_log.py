# Copyright (c) 2022, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.core.utils import set_timeline_doc
from sparrow.model.document import Document
from sparrow.query_builder import DocType, Interval
from sparrow.query_builder.functions import Now
from sparrow.utils import get_fullname, now


class ActivityLog(Document):
	def before_insert(self):
		self.full_name = get_fullname(self.user)
		self.date = now()

	def validate(self):
		self.set_status()
		set_timeline_doc(self)
		self.set_ip_address()

	def set_status(self):
		if not self.is_new():
			return

		if self.reference_doctype and self.reference_name:
			self.status = "Linked"

	def set_ip_address(self):
		if self.operation in ("Login", "Logout"):
			self.ip_address = getattr(sparrow.local, "request_ip")

	@staticmethod
	def clear_old_logs(days=None):
		if not days:
			days = 90
		doctype = DocType("Activity Log")
		sparrow.db.delete(doctype, filters=(doctype.modified < (Now() - Interval(days=days))))


def on_doctype_update():
	"""Add indexes in `tabActivity Log`"""
	sparrow.db.add_index("Activity Log", ["reference_doctype", "reference_name"])
	sparrow.db.add_index("Activity Log", ["timeline_doctype", "timeline_name"])


def add_authentication_log(subject, user, operation="Login", status="Success"):
	sparrow.get_doc(
		{
			"doctype": "Activity Log",
			"user": user,
			"status": status,
			"subject": subject,
			"operation": operation,
		}
	).insert(ignore_permissions=True, ignore_links=True)
