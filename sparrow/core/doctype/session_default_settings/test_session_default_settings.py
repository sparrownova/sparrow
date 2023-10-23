# Copyright (c) 2019, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.core.doctype.session_default_settings.session_default_settings import (
	clear_session_defaults,
	set_session_default_values,
)
from sparrow.tests.utils import SparrowTestCase


class TestSessionDefaultSettings(SparrowTestCase):
	def test_set_session_default_settings(self):
		sparrow.set_user("Administrator")
		settings = sparrow.get_single("Session Default Settings")
		settings.session_defaults = []
		settings.append("session_defaults", {"ref_doctype": "Role"})
		settings.save()

		set_session_default_values({"role": "Website Manager"})

		todo = sparrow.get_doc(
			dict(doctype="ToDo", description="test session defaults set", assigned_by="Administrator")
		).insert()
		self.assertEqual(todo.role, "Website Manager")

	def test_clear_session_defaults(self):
		clear_session_defaults()
		todo = sparrow.get_doc(
			dict(doctype="ToDo", description="test session defaults cleared", assigned_by="Administrator")
		).insert()
		self.assertNotEqual(todo.role, "Website Manager")
