# Copyright (c) 2019, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.core.doctype.user.user import get_system_users
from sparrow.desk.form.assign_to import add as assign_task
from sparrow.tests.utils import FrappeTestCase


class TestNotificationLog(FrappeTestCase):
	def test_assignment(self):
		todo = get_todo()
		user = get_user()

		assign_task(
			{"assign_to": [user], "doctype": "ToDo", "name": todo.name, "description": todo.description}
		)
		log_type = sparrow.db.get_value(
			"Notification Log", {"document_type": "ToDo", "document_name": todo.name}, "type"
		)
		self.assertEqual(log_type, "Assignment")

	def test_share(self):
		todo = get_todo()
		user = get_user()

		sparrow.share.add("ToDo", todo.name, user, notify=1)
		log_type = sparrow.db.get_value(
			"Notification Log", {"document_type": "ToDo", "document_name": todo.name}, "type"
		)
		self.assertEqual(log_type, "Share")

		email = get_last_email_queue()
		content = "Subject: {} shared a document ToDo".format(
			sparrow.utils.get_fullname(sparrow.session.user)
		)
		self.assertTrue(content in email.message)


def get_last_email_queue():
	res = sparrow.get_all("Email Queue", fields=["message"], order_by="creation desc", limit=1)
	return res[0]


def get_todo():
	if not sparrow.get_all("ToDo"):
		return sparrow.get_doc({"doctype": "ToDo", "description": "Test for Notification"}).insert()

	res = sparrow.get_all("ToDo", limit=1)
	return sparrow.get_cached_doc("ToDo", res[0].name)


def get_user():
	return get_system_users(limit=1)[0]
