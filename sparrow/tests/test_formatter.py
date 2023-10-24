import sparrow
from sparrow import format
from sparrow.tests.utils import sparrowTestCase


class TestFormatter(sparrowTestCase):
	def test_currency_formatting(self):
		df = sparrow._dict({"fieldname": "amount", "fieldtype": "Currency", "options": "currency"})

		doc = sparrow._dict({"amount": 5})
		sparrow.db.set_default("currency", "INR")

		# if currency field is not passed then default currency should be used.
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "₹ 100,000.00")

		doc.currency = "USD"
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "$ 100,000.00")

		sparrow.db.set_default("currency", None)
