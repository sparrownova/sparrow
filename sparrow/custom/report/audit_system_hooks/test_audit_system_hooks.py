# Copyright (c) 2022, Sparrow Technologies and contributors
# For license information, please see license.txt


from sparrow.custom.report.audit_system_hooks.audit_system_hooks import execute
from sparrow.tests.utils import sparrowTestCase


class TestAuditSystemHooksReport(sparrowTestCase):
	def test_basic_query(self):
		_, data = execute()
		for row in data:
			if row.get("hook_name") == "app_name":
				self.assertEqual(row.get("hook_values"), "sparrow")
				break
		else:
			self.fail("Failed to generate hooks report")
