# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
import json

import sparrow
from sparrow.tests.utils import SparrowTestCase


class TestSeen(SparrowTestCase):
	def tearDown(self):
		sparrow.set_user("Administrator")

	def test_if_user_is_added(self):
		ev = sparrow.get_doc(
			{
				"doctype": "Event",
				"subject": "test event for seen",
				"starts_on": "2016-01-01 10:10:00",
				"event_type": "Public",
			}
		).insert()

		sparrow.set_user("test@example.com")

		from sparrow.desk.form.load import getdoc

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = sparrow.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))

		# test another user
		sparrow.set_user("test1@example.com")

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = sparrow.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))

		ev.save()
		ev = sparrow.get_doc("Event", ev.name)

		self.assertFalse("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))
