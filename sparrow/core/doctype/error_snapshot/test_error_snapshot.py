# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
from sparrow.tests.utils import SparrowTestCase
from sparrow.utils.logger import sanitized_dict

# test_records = sparrow.get_test_records('Error Snapshot')


class TestErrorSnapshot(SparrowTestCase):
	def test_form_dict_sanitization(self):
		self.assertNotEqual(sanitized_dict({"pwd": "SECRET", "usr": "WHAT"}).get("pwd"), "SECRET")
