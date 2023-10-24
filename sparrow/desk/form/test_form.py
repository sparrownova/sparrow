# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.desk.form.linked_with import get_linked_docs, get_linked_doctypes
from sparrow.tests.utils import sparrowTestCase


class TestForm(sparrowTestCase):
	def test_linked_with(self):
		results = get_linked_docs("Role", "System Manager", linkinfo=get_linked_doctypes("Role"))
		self.assertTrue("User" in results)
		self.assertTrue("DocType" in results)


if __name__ == "__main__":
	import unittest

	sparrow.connect()
	unittest.main()
