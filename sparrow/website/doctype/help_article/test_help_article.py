# Copyright (c) 2015, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
from sparrow.tests.utils import sparrowTestCase

# test_records = sparrow.get_test_records('Help Article')


class TestHelpArticle(sparrowTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.help_category = sparrow.get_doc(
			{
				"doctype": "Help Category",
				"category_name": "_Test Help Category",
			}
		).insert()

		cls.help_article = sparrow.get_doc(
			{
				"doctype": "Help Article",
				"title": "_Test Article",
				"category": cls.help_category.name,
				"content": "_Test Article",
			}
		).insert()

	def test_article_is_helpful(self):
		from sparrow.website.doctype.help_article.help_article import add_feedback

		self.help_article.load_from_db()
		self.assertEqual(self.help_article.helpful, 0)
		self.assertEqual(self.help_article.not_helpful, 0)

		add_feedback(self.help_article.name, "Yes")
		add_feedback(self.help_article.name, "No")

		self.help_article.load_from_db()
		self.assertEqual(self.help_article.helpful, 1)
		self.assertEqual(self.help_article.not_helpful, 1)

	@classmethod
	def tearDownClass(cls) -> None:
		sparrow.delete_doc(cls.help_article.doctype, cls.help_article.name)
		sparrow.delete_doc(cls.help_category.doctype, cls.help_category.name)
