# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import SparrowTestCase

test_records = sparrow.get_test_records("Page")


class TestPage(SparrowTestCase):
	def test_naming(self):
		self.assertRaises(
			sparrow.NameError,
			sparrow.get_doc(dict(doctype="Page", page_name="DocType", module="Core")).insert,
		)
		self.assertRaises(
			sparrow.NameError,
			sparrow.get_doc(dict(doctype="Page", page_name="Settings", module="Core")).insert,
		)
