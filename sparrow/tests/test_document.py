# Copyright (c) 2022, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
from contextlib import contextmanager
from datetime import timedelta
from unittest.mock import Mock, patch

import sparrow
from sparrow.app import make_form_dict
from sparrow.desk.doctype.note.note import Note
from sparrow.model.naming import make_autoname, parse_naming_series, revert_series_if_last
from sparrow.tests.utils import SparrowTestCase
from sparrow.utils import cint, now_datetime, set_request
from sparrow.website.serve import get_response

from . import update_system_settings


class CustomTestNote(Note):
	@property
	def age(self):
		return now_datetime() - self.creation


class CustomNoteWithoutProperty(Note):
	def age(self):
		return now_datetime() - self.creation


class TestDocument(SparrowTestCase):
	def test_get_return_empty_list_for_table_field_if_none(self):
		d = sparrow.get_doc({"doctype": "User"})
		self.assertEqual(d.get("roles"), [])

	def test_load(self):
		d = sparrow.get_doc("DocType", "User")
		self.assertEqual(d.doctype, "DocType")
		self.assertEqual(d.name, "User")
		self.assertEqual(d.allow_rename, 1)
		self.assertTrue(isinstance(d.fields, list))
		self.assertTrue(isinstance(d.permissions, list))
		self.assertTrue(filter(lambda d: d.fieldname == "email", d.fields))

	def test_load_single(self):
		d = sparrow.get_doc("Website Settings", "Website Settings")
		self.assertEqual(d.name, "Website Settings")
		self.assertEqual(d.doctype, "Website Settings")
		self.assertTrue(d.disable_signup in (0, 1))

	def test_insert(self):
		d = sparrow.get_doc(
			{
				"doctype": "Event",
				"subject": "test-doc-test-event 1",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		)
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(sparrow.db.get_value("Event", d.name, "subject"), "test-doc-test-event 1")

		# test if default values are added
		self.assertEqual(d.send_reminder, 1)
		return d

	def test_insert_with_child(self):
		d = sparrow.get_doc(
			{
				"doctype": "Event",
				"subject": "test-doc-test-event 2",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		)
		d.insert()
		self.assertTrue(d.name.startswith("EV"))
		self.assertEqual(sparrow.db.get_value("Event", d.name, "subject"), "test-doc-test-event 2")

	def test_update(self):
		d = self.test_insert()
		d.subject = "subject changed"
		d.save()

		self.assertEqual(sparrow.db.get_value(d.doctype, d.name, "subject"), "subject changed")

	def test_value_changed(self):
		d = self.test_insert()
		d.subject = "subject changed again"
		d.save()
		self.assertTrue(d.has_value_changed("subject"))
		self.assertFalse(d.has_value_changed("event_type"))

	def test_mandatory(self):
		# TODO: recheck if it is OK to force delete
		sparrow.delete_doc_if_exists("User", "test_mandatory@example.com", 1)

		d = sparrow.get_doc(
			{
				"doctype": "User",
				"email": "test_mandatory@example.com",
			}
		)
		self.assertRaises(sparrow.MandatoryError, d.insert)

		d.set("first_name", "Test Mandatory")
		d.insert()
		self.assertEqual(sparrow.db.get_value("User", d.name), d.name)

	def test_text_editor_field(self):
		try:
			sparrow.get_doc(
				doctype="Activity Log", subject="test", message='<img src="test.png" />'
			).insert()
		except sparrow.MandatoryError:
			self.fail("Text Editor false positive mandatory error")

	def test_conflict_validation(self):
		d1 = self.test_insert()
		d2 = sparrow.get_doc(d1.doctype, d1.name)
		d1.save()
		self.assertRaises(sparrow.TimestampMismatchError, d2.save)

	def test_conflict_validation_single(self):
		d1 = sparrow.get_doc("Website Settings", "Website Settings")
		d1.home_page = "test-web-page-1"

		d2 = sparrow.get_doc("Website Settings", "Website Settings")
		d2.home_page = "test-web-page-1"

		d1.save()
		self.assertRaises(sparrow.TimestampMismatchError, d2.save)

	def test_permission(self):
		sparrow.set_user("Guest")
		self.assertRaises(sparrow.PermissionError, self.test_insert)
		sparrow.set_user("Administrator")

	def test_permission_single(self):
		sparrow.set_user("Guest")
		d = sparrow.get_doc("Website Settings", "Website Settings")
		self.assertRaises(sparrow.PermissionError, d.save)
		sparrow.set_user("Administrator")

	def test_link_validation(self):
		sparrow.delete_doc_if_exists("User", "test_link_validation@example.com", 1)

		d = sparrow.get_doc(
			{
				"doctype": "User",
				"email": "test_link_validation@example.com",
				"first_name": "Link Validation",
				"roles": [{"role": "ABC"}],
			}
		)
		self.assertRaises(sparrow.LinkValidationError, d.insert)

		d.roles = []
		d.append("roles", {"role": "System Manager"})
		d.insert()

		self.assertEqual(sparrow.db.get_value("User", d.name), d.name)

	def test_validate(self):
		d = self.test_insert()
		d.starts_on = "2014-01-01"
		d.ends_on = "2013-01-01"
		self.assertRaises(sparrow.ValidationError, d.validate)
		self.assertRaises(sparrow.ValidationError, d.run_method, "validate")
		self.assertRaises(sparrow.ValidationError, d.save)

	def test_db_set_no_query_on_new_docs(self):
		user = sparrow.new_doc("User")
		user.db_set("user_type", "Magical Wizard")
		with self.assertQueryCount(0):
			user.db_set("user_type", "Magical Wizard")

	def test_update_after_submit(self):
		d = self.test_insert()
		d.starts_on = "2014-09-09"
		self.assertRaises(sparrow.UpdateAfterSubmitError, d.validate_update_after_submit)
		d.meta.get_field("starts_on").allow_on_submit = 1
		d.validate_update_after_submit()
		d.meta.get_field("starts_on").allow_on_submit = 0

		# when comparing date(2014, 1, 1) and "2014-01-01"
		d.reload()
		d.starts_on = "2014-01-01"
		d.validate_update_after_submit()

	def test_varchar_length(self):
		d = self.test_insert()
		d.sender = "abcde" * 100 + "@user.com"
		self.assertRaises(sparrow.CharacterLengthExceededError, d.save)

	def test_xss_filter(self):
		d = self.test_insert()

		# script
		xss = '<script>alert("XSS")</script>'
		escaped_xss = xss.replace("<", "&lt;").replace(">", "&gt;")
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# onload
		xss = '<div onload="alert("XSS")">Test</div>'
		escaped_xss = "<div>Test</div>"
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

		# css attributes
		xss = '<div style="something: doesn\'t work; color: red;">Test</div>'
		escaped_xss = '<div style="">Test</div>'
		d.subject += xss
		d.save()
		d.reload()

		self.assertTrue(xss not in d.subject)
		self.assertTrue(escaped_xss in d.subject)

	def test_naming_series(self):
		data = ["TEST-", "TEST/17-18/.test_data./.####", "TEST.YYYY.MM.####"]

		for series in data:
			name = make_autoname(series)
			prefix = series

			if ".#" in series:
				prefix = series.rsplit(".", 1)[0]

			prefix = parse_naming_series(prefix)
			old_current = sparrow.db.get_value("Series", prefix, "current", order_by="name")

			revert_series_if_last(series, name)
			new_current = cint(sparrow.db.get_value("Series", prefix, "current", order_by="name"))

			self.assertEqual(cint(old_current) - 1, new_current)

	def test_non_negative_check(self):
		sparrow.delete_doc_if_exists("Currency", "Sparrow Coin", 1)

		d = sparrow.get_doc(
			{"doctype": "Currency", "currency_name": "Sparrow Coin", "smallest_currency_fraction_value": -1}
		)

		self.assertRaises(sparrow.NonNegativeError, d.insert)

		d.set("smallest_currency_fraction_value", 1)
		d.insert()
		self.assertEqual(sparrow.db.get_value("Currency", d.name), d.name)

		sparrow.delete_doc_if_exists("Currency", "Sparrow Coin", 1)

	def test_get_formatted(self):
		sparrow.get_doc(
			{
				"doctype": "DocType",
				"name": "Test Formatted",
				"module": "Custom",
				"custom": 1,
				"fields": [
					{"label": "Currency", "fieldname": "currency", "reqd": 1, "fieldtype": "Currency"},
				],
			}
		).insert(ignore_if_duplicate=True)

		sparrow.delete_doc_if_exists("Currency", "INR", 1)

		d = sparrow.get_doc(
			{
				"doctype": "Currency",
				"currency_name": "INR",
				"symbol": "₹",
			}
		).insert()

		d = sparrow.get_doc({"doctype": "Test Formatted", "currency": 100000})
		self.assertEqual(d.get_formatted("currency", currency="INR", format="#,###.##"), "₹ 100,000.00")

		# should work even if options aren't set in df
		# and currency param is not passed
		self.assertIn("0", d.get_formatted("currency"))

	def test_limit_for_get(self):
		doc = sparrow.get_doc("DocType", "DocType")
		# assuming DocType has more than 3 Data fields
		self.assertEqual(len(doc.get("fields", limit=3)), 3)

		# limit with filters
		self.assertEqual(len(doc.get("fields", filters={"fieldtype": "Data"}, limit=3)), 3)

	def test_virtual_fields(self):
		"""Virtual fields are accessible via API and Form views, whenever .as_dict is invoked"""
		sparrow.db.delete("Custom Field", {"dt": "Note", "fieldname": "age"})
		note = sparrow.new_doc("Note")
		note.content = "some content"
		note.title = sparrow.generate_hash(length=20)
		note.insert()

		def patch_note(class_=None):
			return patch("sparrow.controllers", new={sparrow.local.site: {"Note": class_ or CustomTestNote}})

		@contextmanager
		def customize_note(with_options=False):
			options = (
				"sparrow.utils.now_datetime() - sparrow.utils.get_datetime(doc.creation)" if with_options else ""
			)
			custom_field = sparrow.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Note",
					"fieldname": "age",
					"fieldtype": "Data",
					"read_only": True,
					"is_virtual": True,
					"options": options,
				}
			)

			try:
				yield custom_field.insert(ignore_if_duplicate=True)
			finally:
				custom_field.delete()
				# to truly delete the field
				# creation is commited due to DDL
				sparrow.db.commit()

		with patch_note():
			doc = sparrow.get_last_doc("Note")
			self.assertIsInstance(doc, CustomTestNote)
			self.assertIsInstance(doc.age, timedelta)
			self.assertIsNone(doc.as_dict().get("age"))
			self.assertIsNone(doc.get_valid_dict().get("age"))

		with customize_note(), patch_note():
			doc = sparrow.get_last_doc("Note")
			self.assertIsInstance(doc, CustomTestNote)
			self.assertIsInstance(doc.age, timedelta)
			self.assertIsInstance(doc.as_dict().get("age"), timedelta)
			self.assertIsInstance(doc.get_valid_dict().get("age"), timedelta)

		# has virtual field, but age method is not a property
		with customize_note(), patch_note(class_=CustomNoteWithoutProperty):
			doc = sparrow.get_last_doc("Note")
			self.assertIsInstance(doc, CustomNoteWithoutProperty)
			self.assertNotIsInstance(type(doc).age, property)
			self.assertIsNone(doc.as_dict().get("age"))
			self.assertIsNone(doc.get_valid_dict().get("age"))

		with customize_note(with_options=True):
			doc = sparrow.get_last_doc("Note")
			self.assertIsInstance(doc, Note)
			self.assertIsInstance(doc.as_dict().get("age"), timedelta)
			self.assertIsInstance(doc.get_valid_dict().get("age"), timedelta)

	def test_run_method(self):
		doc = sparrow.get_last_doc("User")

		# Case 1: Override with a string
		doc.as_dict = ""

		# run_method should throw TypeError
		self.assertRaisesRegex(TypeError, "not callable", doc.run_method, "as_dict")

		# Case 2: Override with a function
		def my_as_dict(*args, **kwargs):
			return "success"

		doc.as_dict = my_as_dict

		# run_method should get overridden
		self.assertEqual(doc.run_method("as_dict"), "success")

	def test_extend(self):
		doc = sparrow.get_last_doc("User")
		self.assertRaises(ValueError, doc.extend, "user_emails", None)

		# allow calling doc.extend with iterable objects
		doc.extend("user_emails", ())
		doc.extend("user_emails", [])
		doc.extend("user_emails", (x for x in ()))

	def test_set(self):
		doc = sparrow.get_last_doc("User")

		# setting None should init a table field to empty list
		doc.set("user_emails", None)
		self.assertEqual(doc.user_emails, [])

		# setting a string value should fail
		self.assertRaises(TypeError, doc.set, "user_emails", "fail")
		# but not when loading from db
		doc.flags.ignore_children = True
		doc.update({"user_emails": "ok"})

	def test_doc_events(self):
		"""validate that all present doc events are correct methods"""

		for doctype, doc_hooks in sparrow.get_doc_hooks().items():
			for _, hooks in doc_hooks.items():
				for hook in hooks:
					try:
						sparrow.get_attr(hook)
					except Exception as e:
						self.fail(f"Invalid doc hook: {doctype}:{hook}\n{e}")

	def test_realtime_notify(self):
		todo = sparrow.new_doc("ToDo")
		todo.description = "this will trigger realtime update"
		todo.notify_update = Mock()
		todo.insert()
		self.assertEqual(todo.notify_update.call_count, 1)

		todo.reload()
		todo.flags.notify_update = False
		todo.description = "this won't trigger realtime update"
		todo.save()
		self.assertEqual(todo.notify_update.call_count, 1)

	def test_error_on_saving_new_doc_with_name(self):
		"""Trying to save a new doc with name should raise DoesNotExistError"""

		doc = sparrow.get_doc(
			{
				"doctype": "ToDo",
				"description": "this should raise sparrow.DoesNotExistError",
				"name": "lets-trick-doc-save",
			}
		)

		self.assertRaises(sparrow.DoesNotExistError, doc.save)


class TestDocumentWebView(SparrowTestCase):
	def get(self, path, user="Guest"):
		sparrow.set_user(user)
		set_request(method="GET", path=path)
		make_form_dict(sparrow.local.request)
		response = get_response()
		sparrow.set_user("Administrator")
		return response

	def test_web_view_link_authentication(self):
		todo = sparrow.get_doc({"doctype": "ToDo", "description": "Test"}).insert()
		document_key = todo.get_document_share_key()

		# with old-style signature key
		update_system_settings({"allow_older_web_view_links": True}, True)
		old_document_key = todo.get_signature()
		url = f"/ToDo/{todo.name}?key={old_document_key}"
		self.assertEqual(self.get(url).status, "200 OK")

		update_system_settings({"allow_older_web_view_links": False}, True)
		self.assertEqual(self.get(url).status, "401 UNAUTHORIZED")

		# with valid key
		url = f"/ToDo/{todo.name}?key={document_key}"
		self.assertEqual(self.get(url).status, "200 OK")

		# with invalid key
		invalid_key_url = f"/ToDo/{todo.name}?key=INVALID_KEY"
		self.assertEqual(self.get(invalid_key_url).status, "401 UNAUTHORIZED")

		# expire the key
		document_key_doc = sparrow.get_doc("Document Share Key", {"key": document_key})
		document_key_doc.expires_on = "2020-01-01"
		document_key_doc.save(ignore_permissions=True)

		# with expired key
		self.assertEqual(self.get(url).status, "410 GONE")

		# without key
		url_without_key = f"/ToDo/{todo.name}"
		self.assertEqual(self.get(url_without_key).status, "403 FORBIDDEN")

		# Logged-in user can access the page without key
		self.assertEqual(self.get(url_without_key, "Administrator").status, "200 OK")
