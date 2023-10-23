# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

# pre loaded

import sparrow
from sparrow.tests.utils import SparrowTestCase


class TestUser(SparrowTestCase):
	def test_default_currency_on_setup(self):
		usd = sparrow.get_doc("Currency", "USD")
		self.assertDocumentEqual({"enabled": 1, "fraction": "Cent"}, usd)
