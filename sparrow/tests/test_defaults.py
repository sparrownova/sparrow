# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
from contextlib import contextmanager

import sparrow
from sparrow.core.doctype.user_permission.test_user_permission import create_user
from sparrow.defaults import *
from sparrow.query_builder.utils import db_type_is
from sparrow.tests.test_query_builder import run_only_if
from sparrow.tests.utils import FrappeTestCase


class TestDefaults(FrappeTestCase):
	def test_global(self):
		clear_user_default("key1")
		set_global_default("key1", "value1")
		self.assertEqual(get_global_default("key1"), "value1")

		set_global_default("key1", "value2")
		self.assertEqual(get_global_default("key1"), "value2")

		add_global_default("key1", "value3")
		self.assertEqual(get_global_default("key1"), "value2")
		self.assertEqual(get_defaults()["key1"], ["value2", "value3"])
		self.assertEqual(get_user_default_as_list("key1"), ["value2", "value3"])

	def test_user(self):
		set_user_default("key1", "2value1")
		self.assertEqual(get_user_default_as_list("key1"), ["2value1"])

		set_user_default("key1", "2value2")
		self.assertEqual(get_user_default("key1"), "2value2")

		add_user_default("key1", "3value3")
		self.assertEqual(get_user_default("key1"), "2value2")
		self.assertEqual(get_user_default_as_list("key1"), ["2value2", "3value3"])

	def test_global_if_not_user(self):
		set_global_default("key4", "value4")
		self.assertEqual(get_user_default("key4"), "value4")

	def test_clear(self):
		set_user_default("key5", "value5")
		self.assertEqual(get_user_default("key5"), "value5")
		clear_user_default("key5")
		self.assertEqual(get_user_default("key5"), None)

	def test_clear_global(self):
		set_global_default("key6", "value6")
		self.assertEqual(get_user_default("key6"), "value6")

		clear_default("key6", value="value6")
		self.assertEqual(get_user_default("key6"), None)

	def test_user_permission_on_defaults(self):
		self.assertEqual(get_global_default("language"), "en")
		self.assertEqual(get_user_default("language"), "en")
		self.assertEqual(get_user_default_as_list("language"), ["en"])

		with as_restricted_user():
			self.assertEqual(get_global_default("language"), None)
			self.assertEqual(get_user_default("language"), None)
			self.assertEqual(get_user_default_as_list("language"), [])


@contextmanager
def as_restricted_user():
	old_user = sparrow.session.user
	user = "test@example.com"

	perm_doc = sparrow.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": "Language",
			"for_value": "en-GB",
		}
	).insert(ignore_permissions=True)

	sparrow.set_user(user)

	yield

	perm_doc.delete(ignore_permissions=True)
	sparrow.set_user(old_user)

	@run_only_if(db_type_is.MARIADB)
	def test_user_permission_defaults(self):
		# Create user permission
		create_user("user_default_test@example.com", "Blogger")
		sparrow.set_user("user_default_test@example.com")
		set_global_default("Country", "")
		clear_user_default("Country")

		perm_doc = sparrow.get_doc(
			dict(
				doctype="User Permission",
				user=sparrow.session.user,
				allow="Country",
				for_value="India",
			)
		).insert(ignore_permissions=True)

		sparrow.db.set_value("User Permission", perm_doc.name, "is_default", 1)
		set_global_default("Country", "United States")
		self.assertEqual(get_user_default("Country"), "India")

		sparrow.db.set_value("User Permission", perm_doc.name, "is_default", 0)
		clear_user_default("Country")
		self.assertEqual(get_user_default("Country"), None)

		perm_doc = sparrow.get_doc(
			dict(
				doctype="User Permission",
				user=sparrow.session.user,
				allow="Country",
				for_value="United States",
			)
		).insert(ignore_permissions=True)

		self.assertEqual(get_user_default("Country"), "United States")
