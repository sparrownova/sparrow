import sparrow
from sparrow.tests.utils import FrappeTestCase
from sparrow.website.path_resolver import PathResolver
from sparrow.website.serve import get_response_content

test_records = sparrow.get_test_records("Web Page")


class TestWebPage(FrappeTestCase):
	def setUp(self):
		sparrow.db.delete("Web Page")
		for t in test_records:
			sparrow.get_doc(t).insert()

	def test_path_resolver(self):
		self.assertTrue(PathResolver("test-web-page-1").is_valid_path())
		self.assertTrue(PathResolver("test-web-page-1/test-web-page-2").is_valid_path())
		self.assertTrue(PathResolver("test-web-page-1/test-web-page-3").is_valid_path())
		self.assertFalse(PathResolver("test-web-page-1/test-web-page-Random").is_valid_path())

	def test_content_type(self):
		web_page = sparrow.get_doc(
			dict(
				doctype="Web Page",
				title="Test Content Type",
				published=1,
				content_type="Rich Text",
				main_section="rich text",
				main_section_md="# h1\nmarkdown content",
				main_section_html="<div>html content</div>",
			)
		).insert()

		self.assertIn("rich text", get_response_content("/test-content-type"))

		web_page.content_type = "Markdown"
		web_page.save()
		self.assertIn("markdown content", get_response_content("/test-content-type"))

		web_page.content_type = "HTML"
		web_page.save()
		self.assertIn("html content", get_response_content("/test-content-type"))

		web_page.delete()

	def test_dynamic_route(self):
		web_page = sparrow.get_doc(
			dict(
				doctype="Web Page",
				title="Test Dynamic Route",
				published=1,
				dynamic_route=1,
				route="/doctype-view/<doctype>",
				content_type="HTML",
				dynamic_template=1,
				main_section_html="<div>{{ sparrow.form_dict.doctype }}</div>",
			)
		).insert()
		try:
			from sparrow.utils import get_html_for_route

			content = get_html_for_route("/doctype-view/DocField")
			self.assertIn("<div>DocField</div>", content)
		finally:
			web_page.delete()
