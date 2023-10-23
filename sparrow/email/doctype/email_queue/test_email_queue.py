# Copyright (c) 2015, Sparrow Technologies and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.tests.utils import FrappeTestCase


class TestEmailQueue(FrappeTestCase):
	def test_email_queue_deletion_based_on_modified_date(self):
		from sparrow.email.doctype.email_queue.email_queue import EmailQueue

		old_record = sparrow.get_doc(
			{
				"doctype": "Email Queue",
				"sender": "Test <test@example.com>",
				"show_as_cc": "",
				"message": "Test message",
				"status": "Sent",
				"priority": 1,
				"recipients": [
					{
						"recipient": "test_auth@test.com",
					}
				],
			}
		).insert()

		old_record.modified = "2010-01-01 00:00:01"
		old_record.recipients[0].modified = old_record.modified
		old_record.db_update_all()

		new_record = sparrow.copy_doc(old_record)
		new_record.insert()

		EmailQueue.clear_old_logs()

		self.assertFalse(sparrow.db.exists("Email Queue", old_record.name))
		self.assertFalse(sparrow.db.exists("Email Queue Recipient", {"parent": old_record.name}))

		self.assertTrue(sparrow.db.exists("Email Queue", new_record.name))
		self.assertTrue(sparrow.db.exists("Email Queue Recipient", {"parent": new_record.name}))
