# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
import json

import sparrow
from sparrow.tests.utils import SparrowTestCase
from sparrow.utils import set_request
from sparrow.website.doctype.web_form.web_form import accept
from sparrow.website.serve import get_response_content

test_dependencies = ["Web Form"]


class TestWebForm(SparrowTestCase):
	def setUp(self):
		sparrow.conf.disable_website_cache = True
		sparrow.local.path = None

	def tearDown(self):
		sparrow.conf.disable_website_cache = False
		sparrow.local.path = None
		sparrow.local.request_ip = None
		sparrow.form_dict.web_form = None
		sparrow.form_dict.data = None
		sparrow.form_dict.docname = None

	def test_accept(self):
		sparrow.set_user("Administrator")

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description",
			"starts_on": "2014-09-09",
		}

		sparrow.form_dict.web_form = "manage-events"
		sparrow.form_dict.data = json.dumps(doc)
		sparrow.local.request_ip = "127.0.0.1"

		accept(web_form="manage-events", data=json.dumps(doc))

		self.event_name = sparrow.db.get_value("Event", {"subject": "_Test Event Web Form"})
		self.assertTrue(self.event_name)

	def test_edit(self):
		self.test_accept()

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description 1",
			"starts_on": "2014-09-09",
			"name": self.event_name,
		}

		self.assertNotEqual(
			sparrow.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)

		sparrow.form_dict.web_form = "manage-events"
		sparrow.form_dict.docname = self.event_name
		sparrow.form_dict.data = json.dumps(doc)

		accept(web_form="manage-events", docname=self.event_name, data=json.dumps(doc))

		self.assertEqual(
			sparrow.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)

	def test_webform_render(self):
		set_request(method="GET", path="manage-events/new")
		content = get_response_content("manage-events/new")
		self.assertIn('<h1 class="ellipsis">New Manage Events</h1>', content)
		self.assertIn('data-doctype="Web Form"', content)
		self.assertIn('data-path="manage-events/new"', content)
		self.assertIn('source-type="Generator"', content)

	def test_webform_html_meta_is_added(self):
		set_request(method="GET", path="manage-events/new")
		content = get_response_content("manage-events/new")

		self.assertIn('<meta name="name" content="Test Meta Form Title">', content)
		self.assertIn('<meta property="og:description" content="Test Meta Form Description">', content)
		self.assertIn('<meta property="og:image" content="https://sparrow.io/files/sparrow.png">', content)
