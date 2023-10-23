# Copyright (c) 2022, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import base64
import unittest

import requests

import sparrow
from sparrow.core.doctype.user.user import generate_keys
from sparrow.sparrowclient import AuthError, SparrowClient, SparrowException
from sparrow.utils.data import get_url


class TestSparrowClient(unittest.TestCase):
	PASSWORD = sparrow.conf.admin_password or "admin"

	@classmethod
	def setUpClass(cls) -> None:
		site_url = get_url()
		try:
			SparrowClient(site_url, "Administrator", cls.PASSWORD, verify=False)
		except AuthError:
			raise unittest.SkipTest(
				f"AuthError raised for {site_url} [usr=Administrator, pwd={cls.PASSWORD}]"
			)

		return super().setUpClass()

	def test_insert_many(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": ("in", ("Sing", "a", "song", "of", "sixpence"))})
		sparrow.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "Sing"},
				{"doctype": "Note", "public": True, "title": "a"},
				{"doctype": "Note", "public": True, "title": "song"},
				{"doctype": "Note", "public": True, "title": "of"},
				{"doctype": "Note", "public": True, "title": "sixpence"},
			]
		)

		self.assertTrue(sparrow.db.get_value("Note", {"title": "Sing"}))
		self.assertTrue(sparrow.db.get_value("Note", {"title": "a"}))
		self.assertTrue(sparrow.db.get_value("Note", {"title": "song"}))
		self.assertTrue(sparrow.db.get_value("Note", {"title": "of"}))
		self.assertTrue(sparrow.db.get_value("Note", {"title": "sixpence"}))

	def test_create_doc(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": "test_create"})
		sparrow.db.commit()

		server.insert({"doctype": "Note", "public": True, "title": "test_create"})

		self.assertTrue(sparrow.db.get_value("Note", {"title": "test_create"}))

	def test_list_docs(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		doc_list = server.get_list("Note")

		self.assertTrue(len(doc_list))

	def test_get_doc(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": "get_this"})
		sparrow.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "get_this"},
			]
		)
		doc = server.get_doc("Note", "get_this")
		self.assertTrue(doc)

	def test_get_value(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": "get_value"})
		sparrow.db.commit()

		test_content = "test get value"

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "get_value", "content": test_content},
			]
		)
		self.assertEqual(
			server.get_value("Note", "content", {"title": "get_value"}).get("content"), test_content
		)
		name = server.get_value("Note", "name", {"title": "get_value"}).get("name")

		# test by name
		self.assertEqual(server.get_value("Note", "content", name).get("content"), test_content)

		self.assertRaises(
			SparrowException,
			server.get_value,
			"Note",
			"(select (password) from(__Auth) order by name desc limit 1)",
			{"title": "get_value"},
		)

	def test_get_single(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		server.set_value("Website Settings", "Website Settings", "title_prefix", "test-prefix")
		self.assertEqual(
			server.get_value("Website Settings", "title_prefix", "Website Settings").get("title_prefix"),
			"test-prefix",
		)
		self.assertEqual(
			server.get_value("Website Settings", "title_prefix").get("title_prefix"), "test-prefix"
		)
		sparrow.db.set_value("Website Settings", None, "title_prefix", "")

	def test_update_doc(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": ("in", ("Sing", "sing"))})
		sparrow.db.commit()

		server.insert({"doctype": "Note", "public": True, "title": "Sing"})
		doc = server.get_doc("Note", "Sing")
		changed_title = "sing"
		doc["title"] = changed_title
		doc = server.update(doc)
		self.assertTrue(doc["title"] == changed_title)

	def test_update_child_doc(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Contact", {"first_name": "George", "last_name": "Steevens"})
		sparrow.db.delete("Contact", {"first_name": "William", "last_name": "Shakespeare"})
		sparrow.db.delete("Communication", {"reference_doctype": "Event"})
		sparrow.db.delete("Communication Link", {"link_doctype": "Contact"})
		sparrow.db.delete("Event", {"subject": "Sing a song of sixpence"})
		sparrow.db.delete("Event Participants", {"reference_doctype": "Contact"})
		sparrow.db.commit()

		# create multiple contacts
		server.insert_many(
			[
				{"doctype": "Contact", "first_name": "George", "last_name": "Steevens"},
				{"doctype": "Contact", "first_name": "William", "last_name": "Shakespeare"},
			]
		)

		# create an event with one of the created contacts
		event = server.insert(
			{
				"doctype": "Event",
				"subject": "Sing a song of sixpence",
				"event_participants": [
					{"reference_doctype": "Contact", "reference_docname": "George Steevens"}
				],
			}
		)

		# update the event's contact to the second contact
		server.update(
			{
				"doctype": "Event Participants",
				"name": event.get("event_participants")[0].get("name"),
				"reference_docname": "William Shakespeare",
			}
		)

		# the change should run the parent document's validations and
		# create a Communication record with the new contact
		self.assertTrue(sparrow.db.exists("Communication Link", {"link_name": "William Shakespeare"}))

	def test_delete_doc(self):
		server = SparrowClient(get_url(), "Administrator", self.PASSWORD, verify=False)
		sparrow.db.delete("Note", {"title": "delete"})
		sparrow.db.commit()

		server.insert_many(
			[
				{"doctype": "Note", "public": True, "title": "delete"},
			]
		)
		server.delete("Note", "delete")

		self.assertFalse(sparrow.db.get_value("Note", {"title": "delete"}))

	def test_auth_via_api_key_secret(self):
		# generate API key and API secret for administrator
		keys = generate_keys("Administrator")
		sparrow.db.commit()
		generated_secret = sparrow.utils.password.get_decrypted_password(
			"User", "Administrator", fieldname="api_secret"
		)

		api_key = sparrow.db.get_value("User", "Administrator", "api_key")
		header = {"Authorization": f"token {api_key}:{generated_secret}"}
		res = requests.post(get_url() + "/api/method/sparrow.auth.get_logged_user", headers=header)

		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])
		self.assertEqual(keys["api_secret"], generated_secret)

		header = {
			"Authorization": "Basic {}".format(
				base64.b64encode(sparrow.safe_encode(f"{api_key}:{generated_secret}")).decode()
			)
		}
		res = requests.post(get_url() + "/api/method/sparrow.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 200)
		self.assertEqual("Administrator", res.json()["message"])

		# Valid api key, invalid api secret
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": f"token {api_key}:{api_secret}"}
		res = requests.post(get_url() + "/api/method/sparrow.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 403)

		# random api key and api secret
		api_key = "@3djdk3kld"
		api_secret = "ksk&93nxoe3os"
		header = {"Authorization": f"token {api_key}:{api_secret}"}
		res = requests.post(get_url() + "/api/method/sparrow.auth.get_logged_user", headers=header)
		self.assertEqual(res.status_code, 401)
