# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import FrappeTestCase


class TestDocumentLocks(FrappeTestCase):
	def test_locking(self):
		todo = sparrow.get_doc(dict(doctype="ToDo", description="test")).insert()
		todo_1 = sparrow.get_doc("ToDo", todo.name)

		todo.lock()
		self.assertRaises(sparrow.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(sparrow.DocumentLockedError, todo.lock)
		todo_1.unlock()
