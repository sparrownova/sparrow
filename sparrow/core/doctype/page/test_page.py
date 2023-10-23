# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import FrappeTestCase

test_records = sparrow.get_test_records("Page")


class TestPage(FrappeTestCase):
	def test_naming(self):
		self.assertRaises(
			sparrow.NameError,
			sparrow.get_doc(dict(doctype="Page", page_name="DocType", module="Core")).insert,
		)
		self.assertRaises(
			sparrow.NameError,
			sparrow.get_doc(dict(doctype="Page", page_name="Settings", module="Core")).insert,
		)
