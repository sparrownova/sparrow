# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
from sparrow.tests.utils import FrappeTestCase
from sparrow.utils.logger import sanitized_dict

# test_records = sparrow.get_test_records('Error Snapshot')


class TestErrorSnapshot(FrappeTestCase):
	def test_form_dict_sanitization(self):
		self.assertNotEqual(sanitized_dict({"pwd": "SECRET", "usr": "WHAT"}).get("pwd"), "SECRET")
