# Copyright (c) 2015, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import sparrowTestCase


class TestAddressTemplate(sparrowTestCase):
	def setUp(self):
		self.make_default_address_template()

	def test_default_is_unset(self):
		a = sparrow.get_doc("Address Template", "India")
		a.is_default = 1
		a.save()

		b = sparrow.get_doc("Address Template", "Brazil")
		b.is_default = 1
		b.save()

		self.assertEqual(sparrow.db.get_value("Address Template", "India", "is_default"), 0)

	def tearDown(self):
		a = sparrow.get_doc("Address Template", "India")
		a.is_default = 1
		a.save()

	@classmethod
	def make_default_address_template(self):
		template = """{{ address_line1 }}<br>{% if address_line2 %}{{ address_line2 }}<br>{% endif -%}{{ city }}<br>{% if state %}{{ state }}<br>{% endif -%}{% if pincode %}{{ pincode }}<br>{% endif -%}{{ country }}<br>{% if phone %}Phone: {{ phone }}<br>{% endif -%}{% if fax %}Fax: {{ fax }}<br>{% endif -%}{% if email_id %}Email: {{ email_id }}<br>{% endif -%}"""

		if not sparrow.db.exists("Address Template", "India"):
			sparrow.get_doc(
				{"doctype": "Address Template", "country": "India", "is_default": 1, "template": template}
			).insert()

		if not sparrow.db.exists("Address Template", "Brazil"):
			sparrow.get_doc(
				{"doctype": "Address Template", "country": "Brazil", "template": template}
			).insert()
