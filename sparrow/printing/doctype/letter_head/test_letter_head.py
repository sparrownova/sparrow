# Copyright (c) 2017, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import sparrowTestCase


class TestLetterHead(sparrowTestCase):
	def test_auto_image(self):
		letter_head = sparrow.get_doc(
			dict(doctype="Letter Head", letter_head_name="Test", source="Image", image="/public/test.png")
		).insert()

		# test if image is automatically set
		self.assertTrue(letter_head.image in letter_head.content)
