# Copyright (c) 2019, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import json

import sparrow
from sparrow.contacts.doctype.contact.contact import get_contact_name
from sparrow.core.doctype.user.user import create_contact
from sparrow.tests.utils import FrappeTestCase
from sparrow.website.doctype.personal_data_download_request.personal_data_download_request import (
	get_user_data,
)


class TestRequestPersonalData(FrappeTestCase):
	def setUp(self):
		create_user_if_not_exists(email="test_privacy@example.com")

	def tearDown(self):
		sparrow.db.delete("Personal Data Download Request")

	def test_user_data_creation(self):
		user_data = json.loads(get_user_data("test_privacy@example.com"))
		contact_name = get_contact_name("test_privacy@example.com")
		expected_data = {"Contact": sparrow.get_all("Contact", {"name": contact_name}, ["*"])}
		expected_data = json.loads(json.dumps(expected_data, default=str))
		self.assertEqual({"Contact": user_data["Contact"]}, expected_data)

	def test_file_and_email_creation(self):
		sparrow.set_user("test_privacy@example.com")
		download_request = sparrow.get_doc(
			{"doctype": "Personal Data Download Request", "user": "test_privacy@example.com"}
		)
		download_request.save(ignore_permissions=True)

		sparrow.set_user("Administrator")

		file_count = sparrow.db.count(
			"File",
			{
				"attached_to_doctype": "Personal Data Download Request",
				"attached_to_name": download_request.name,
			},
		)

		self.assertEqual(file_count, 1)

		email_queue = sparrow.get_all(
			"Email Queue", fields=["message"], order_by="creation DESC", limit=1
		)
		self.assertIn(sparrow._("Download Your Data"), email_queue[0].message)

		sparrow.db.delete("Email Queue")


def create_user_if_not_exists(email, first_name=None):
	sparrow.delete_doc_if_exists("User", email)

	user = sparrow.get_doc(
		{
			"doctype": "User",
			"user_type": "Website User",
			"email": email,
			"send_welcome_email": 0,
			"first_name": first_name or email.split("@", 1)[0],
			"birth_date": sparrow.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)
	create_contact(user=user)
