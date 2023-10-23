# Copyright (c) 2017, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import json
from contextlib import contextmanager
from unittest import skip

import sparrow
from sparrow.integrations.doctype.webhook.webhook import (
	enqueue_webhook,
	get_webhook_data,
	get_webhook_headers,
)
from sparrow.tests.utils import FrappeTestCase


@contextmanager
def get_test_webhook(config):
	wh = sparrow.get_doc(config).insert()
	wh.reload()
	try:
		yield wh
	finally:
		wh.delete()


class TestWebhook(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		# delete any existing webhooks
		sparrow.db.delete("Webhook")
		# Delete existing logs if any
		sparrow.db.delete("Webhook Request Log")
		super().setUpClass()
		# create test webhooks
		cls.create_sample_webhooks()

	@classmethod
	def create_sample_webhooks(cls):
		samples_webhooks_data = [
			{
				"webhook_doctype": "User",
				"webhook_docevent": "after_insert",
				"request_url": "https://httpbin.org/post",
				"condition": "doc.email",
				"enabled": True,
			},
			{
				"webhook_doctype": "User",
				"webhook_docevent": "after_insert",
				"request_url": "https://httpbin.org/post",
				"condition": "doc.first_name",
				"enabled": False,
			},
		]

		cls.sample_webhooks = []
		for wh_fields in samples_webhooks_data:
			wh = sparrow.new_doc("Webhook")
			wh.update(wh_fields)
			wh.insert()
			cls.sample_webhooks.append(wh)

	@classmethod
	def tearDownClass(cls):
		# delete any existing webhooks
		sparrow.db.delete("Webhook")

	def setUp(self):
		# retrieve or create a User webhook for `after_insert`
		webhook_fields = {
			"webhook_doctype": "User",
			"webhook_docevent": "after_insert",
			"request_url": "https://httpbin.org/post",
		}

		if sparrow.db.exists("Webhook", webhook_fields):
			self.webhook = sparrow.get_doc("Webhook", webhook_fields)
		else:
			self.webhook = sparrow.new_doc("Webhook")
			self.webhook.update(webhook_fields)

		# create a User document
		self.user = sparrow.new_doc("User")
		self.user.first_name = sparrow.mock("name")
		self.user.email = sparrow.mock("email")
		self.user.save()

		# Create another test user specific to this test
		self.test_user = sparrow.new_doc("User")
		self.test_user.email = "user1@integration.webhooks.test.com"
		self.test_user.first_name = "user1"

	def tearDown(self) -> None:
		self.user.delete()
		self.test_user.delete()
		super().tearDown()

	def test_webhook_trigger_with_enabled_webhooks(self):
		"""Test webhook trigger for enabled webhooks"""

		sparrow.cache().delete_value("webhooks")
		sparrow.flags.webhooks = None

		# Insert the user to db
		self.test_user.insert()

		self.assertTrue("User" in sparrow.flags.webhooks)
		# only 1 hook (enabled) must be queued
		self.assertEqual(len(sparrow.flags.webhooks.get("User")), 1)
		self.assertTrue(self.test_user.email in sparrow.flags.webhooks_executed)
		self.assertEqual(
			sparrow.flags.webhooks_executed.get(self.test_user.email)[0], self.sample_webhooks[0].name
		)

	def test_validate_doc_events(self):
		"Test creating a submit-related webhook for a non-submittable DocType"

		self.webhook.webhook_docevent = "on_submit"
		self.assertRaises(sparrow.ValidationError, self.webhook.save)

	def test_validate_request_url(self):
		"Test validation for the webhook request URL"

		self.webhook.request_url = "httpbin.org?post"
		self.assertRaises(sparrow.ValidationError, self.webhook.save)

	def test_validate_headers(self):
		"Test validation for request headers"

		# test incomplete headers
		self.webhook.set("webhook_headers", [{"key": "Content-Type"}])
		self.webhook.save()
		headers = get_webhook_headers(doc=None, webhook=self.webhook)
		self.assertEqual(headers, {})

		# test complete headers
		self.webhook.set("webhook_headers", [{"key": "Content-Type", "value": "application/json"}])
		self.webhook.save()
		headers = get_webhook_headers(doc=None, webhook=self.webhook)
		self.assertEqual(headers, {"Content-Type": "application/json"})

	def test_validate_request_body_form(self):
		"Test validation of Form URL-Encoded request body"

		self.webhook.request_structure = "Form URL-Encoded"
		self.webhook.set("webhook_data", [{"fieldname": "name", "key": "name"}])
		self.webhook.webhook_json = """{
			"name": "{{ doc.name }}"
		}"""
		self.webhook.save()
		self.assertEqual(self.webhook.webhook_json, None)

		data = get_webhook_data(doc=self.user, webhook=self.webhook)
		self.assertEqual(data, {"name": self.user.name})

	def test_validate_request_body_json(self):
		"Test validation of JSON request body"

		self.webhook.request_structure = "JSON"
		self.webhook.set("webhook_data", [{"fieldname": "name", "key": "name"}])
		self.webhook.webhook_json = """{
			"name": "{{ doc.name }}"
		}"""
		self.webhook.save()
		self.assertEqual(self.webhook.webhook_data, [])

		data = get_webhook_data(doc=self.user, webhook=self.webhook)
		self.assertEqual(data, {"name": self.user.name})

	def test_webhook_req_log_creation(self):
		if not sparrow.db.get_value("User", "user2@integration.webhooks.test.com"):
			user = sparrow.get_doc(
				{"doctype": "User", "email": "user2@integration.webhooks.test.com", "first_name": "user2"}
			).insert()
		else:
			user = sparrow.get_doc("User", "user2@integration.webhooks.test.com")

		webhook = sparrow.get_doc("Webhook", {"webhook_doctype": "User"})
		enqueue_webhook(user, webhook)

		self.assertTrue(sparrow.get_all("Webhook Request Log", pluck="name"))

	@skip("flaky because of network call, tested on develop branch")
	def test_webhook_with_array_body(self):
		"""Check if array request body are supported."""
		wh_config = {
			"doctype": "Webhook",
			"webhook_doctype": "Note",
			"webhook_docevent": "after_insert",
			"enabled": 1,
			"request_url": "https://httpbin.org/post",
			"request_method": "POST",
			"request_structure": "JSON",
			"webhook_json": '[\r\n{% for n in range(3) %}\r\n    {\r\n        "title": "{{ doc.title }}",\r\n        "n": {{ n }}\r\n    }\r\n    {%- if not loop.last -%}\r\n        , \r\n    {%endif%}\r\n{%endfor%}\r\n]',
			"meets_condition": "Yes",
			"webhook_headers": [
				{
					"key": "Content-Type",
					"value": "application/json",
				}
			],
		}

		with get_test_webhook(wh_config) as wh:
			doc = sparrow.new_doc("Note")
			doc.title = "Test Webhook Note"

			enqueue_webhook(doc, wh)
			log = sparrow.get_last_doc("Webhook Request Log")
			self.assertEqual(len(json.loads(log.response)["json"]), 3)
