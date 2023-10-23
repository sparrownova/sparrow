# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors

from unittest.mock import patch

import sparrow
from sparrow.tests.utils import FrappeTestCase


class TestClient(FrappeTestCase):
	def test_set_value(self):
		todo = sparrow.get_doc(dict(doctype="ToDo", description="test")).insert()
		sparrow.set_value("ToDo", todo.name, "description", "test 1")
		self.assertEqual(sparrow.get_value("ToDo", todo.name, "description"), "test 1")

		sparrow.set_value("ToDo", todo.name, {"description": "test 2"})
		self.assertEqual(sparrow.get_value("ToDo", todo.name, "description"), "test 2")

	def test_delete(self):
		from sparrow.client import delete
		from sparrow.desk.doctype.note.note import Note

		note = sparrow.get_doc(
			doctype="Note",
			title=sparrow.generate_hash(length=8),
			content="test",
			seen_by=[{"user": "Administrator"}],
		).insert()

		child_row_name = note.seen_by[0].name

		with patch.object(Note, "save") as save:
			delete("Note Seen By", child_row_name)
			save.assert_called()

		delete("Note", note.name)

		self.assertFalse(sparrow.db.exists("Note", note.name))
		self.assertRaises(sparrow.DoesNotExistError, delete, "Note", note.name)
		self.assertRaises(sparrow.DoesNotExistError, delete, "Note Seen By", child_row_name)

	def test_http_valid_method_access(self):
		from sparrow.client import delete
		from sparrow.handler import execute_cmd

		sparrow.set_user("Administrator")

		sparrow.local.request = sparrow._dict()
		sparrow.local.request.method = "POST"

		sparrow.local.form_dict = sparrow._dict(
			{"doc": dict(doctype="ToDo", description="Valid http method"), "cmd": "sparrow.client.save"}
		)
		todo = execute_cmd("sparrow.client.save")

		self.assertEqual(todo.get("description"), "Valid http method")

		delete("ToDo", todo.name)

	def test_http_invalid_method_access(self):
		from sparrow.handler import execute_cmd

		sparrow.set_user("Administrator")

		sparrow.local.request = sparrow._dict()
		sparrow.local.request.method = "GET"

		sparrow.local.form_dict = sparrow._dict(
			{"doc": dict(doctype="ToDo", description="Invalid http method"), "cmd": "sparrow.client.save"}
		)

		self.assertRaises(sparrow.PermissionError, execute_cmd, "sparrow.client.save")

	def test_run_doc_method(self):
		from sparrow.handler import execute_cmd

		if not sparrow.db.exists("Report", "Test Run Doc Method"):
			report = sparrow.get_doc(
				{
					"doctype": "Report",
					"ref_doctype": "User",
					"report_name": "Test Run Doc Method",
					"report_type": "Query Report",
					"is_standard": "No",
					"roles": [{"role": "System Manager"}],
				}
			).insert()
		else:
			report = sparrow.get_doc("Report", "Test Run Doc Method")

		sparrow.local.request = sparrow._dict()
		sparrow.local.request.method = "GET"

		# Whitelisted, works as expected
		sparrow.local.form_dict = sparrow._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "toggle_disable",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		execute_cmd(sparrow.local.form_dict.cmd)

		# Not whitelisted, throws permission error
		sparrow.local.form_dict = sparrow._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "create_report_py",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		self.assertRaises(sparrow.PermissionError, execute_cmd, sparrow.local.form_dict.cmd)

	def test_array_values_in_request_args(self):
		import requests

		from sparrow.auth import CookieManager, LoginManager

		sparrow.utils.set_request(path="/")
		sparrow.local.cookie_manager = CookieManager()
		sparrow.local.login_manager = LoginManager()
		sparrow.local.login_manager.login_as("Administrator")
		params = {
			"doctype": "DocType",
			"fields": ["name", "modified"],
			"sid": sparrow.session.sid,
		}
		headers = {
			"accept": "application/json",
			"content-type": "application/json",
		}
		url = (
			f"http://{sparrow.local.site}:{sparrow.conf.webserver_port}/api/method/sparrow.client.get_list"
		)
		res = requests.post(url, json=params, headers=headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		first_item = data["message"][0]
		self.assertTrue("name" in first_item)
		self.assertTrue("modified" in first_item)
		sparrow.local.login_manager.logout()

	def test_client_get(self):
		from sparrow.client import get

		todo = sparrow.get_doc(doctype="ToDo", description="test").insert()
		filters = {"name": todo.name}
		filters_json = sparrow.as_json(filters)

		self.assertEqual(get("ToDo", filters=filters).description, "test")
		self.assertEqual(get("ToDo", filters=filters_json).description, "test")
		self.assertEqual(get("System Settings", "", "").doctype, "System Settings")
		self.assertEqual(get("ToDo", filters={}), get("ToDo", filters="{}"))
		todo.delete()

	def test_client_insert(self):
		from sparrow.client import insert

		def get_random_title():
			return f"test-{sparrow.generate_hash()}"

		# test insert dict
		doc = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(doc)
		self.assertTrue(note1)

		# test insert json
		doc["title"] = get_random_title()
		json_doc = sparrow.as_json(doc)
		note2 = insert(json_doc)
		self.assertTrue(note2)

		# test insert child doc without parent fields
		child_doc = {"doctype": "Note Seen By", "user": "Administrator"}
		with self.assertRaises(sparrow.ValidationError):
			insert(child_doc)

		# test insert child doc with parent fields
		child_doc = {
			"doctype": "Note Seen By",
			"user": "Administrator",
			"parenttype": "Note",
			"parent": note1.name,
			"parentfield": "seen_by",
		}
		note3 = insert(child_doc)
		self.assertTrue(note3)

		# cleanup
		sparrow.delete_doc("Note", note1.name)
		sparrow.delete_doc("Note", note2.name)

	def test_client_insert_many(self):
		from sparrow.client import insert, insert_many

		def get_random_title():
			return f"test-{sparrow.generate_hash(length=5)}"

		# insert a (parent) doc
		note1 = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(note1)

		doc_list = [
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{"doctype": "Note", "title": "not-a-random-title", "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": "another-note-title", "content": "test"},
		]

		# insert all docs
		docs = insert_many(doc_list)

		self.assertEqual(len(docs), 7)
		self.assertEqual(docs[3], "not-a-random-title")
		self.assertEqual(docs[6], "another-note-title")
		self.assertIn(note1.name, docs)

		# cleanup
		for doc in docs:
			sparrow.delete_doc("Note", doc)
