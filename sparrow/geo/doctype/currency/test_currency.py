# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# pre loaded

import sparrow
from sparrow.tests.utils import FrappeTestCase


class TestUser(FrappeTestCase):
	def test_default_currency_on_setup(self):
		usd = sparrow.get_doc("Currency", "USD")
		self.assertDocumentEqual({"enabled": 1, "fraction": "Cent"}, usd)
