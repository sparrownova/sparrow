# Copyright (c) 2022, Sparrow Technologies and contributors
# For license information, please see license.txt


from sparrow.core.report.database_storage_usage_by_tables.database_storage_usage_by_tables import (
	execute,
)
from sparrow.tests.utils import FrappeTestCase


class TestDBUsageReport(FrappeTestCase):
	def test_basic_query(self):
		_, data = execute()
		tables = [d.table for d in data]
		self.assertFalse({"tabUser", "tabDocField"}.difference(tables))
