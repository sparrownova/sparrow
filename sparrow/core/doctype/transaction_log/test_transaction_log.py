# Copyright (c) 2018, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import hashlib

import sparrow
from sparrow.tests.utils import sparrowTestCase

test_records = []


class TestTransactionLog(sparrowTestCase):
	def test_validate_chaining(self):
		sparrow.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 1",
				"data": "first_data",
			}
		).insert(ignore_permissions=True)

		second_log = sparrow.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 2",
				"data": "second_data",
			}
		).insert(ignore_permissions=True)

		third_log = sparrow.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 3",
				"data": "third_data",
			}
		).insert(ignore_permissions=True)

		sha = hashlib.sha256()
		sha.update(
            sparrow.safe_encode(str(third_log.transaction_hash))
            + sparrow.safe_encode(str(second_log.chaining_hash))
		)

		self.assertEqual(sha.hexdigest(), third_log.chaining_hash)
