# Copyright (c) 2019, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import json

import sparrow
from sparrow.templates.includes.comments.comments import add_comment
from sparrow.tests.test_model_utils import set_user
from sparrow.tests.utils import SparrowTestCase, change_settings
from sparrow.website.doctype.blog_post.test_blog_post import make_test_blog


class TestComment(SparrowTestCase):
	def tearDown(self):
		sparrow.form_dict.comment = None
		sparrow.form_dict.comment_email = None
		sparrow.form_dict.comment_by = None
		sparrow.form_dict.reference_doctype = None
		sparrow.form_dict.reference_name = None
		sparrow.form_dict.route = None
		sparrow.local.request_ip = None

	def test_comment_creation(self):
		test_doc = sparrow.get_doc(dict(doctype="ToDo", description="test"))
		test_doc.insert()
		comment = test_doc.add_comment("Comment", "test comment")

		test_doc.reload()

		# check if updated in _comments cache
		comments = json.loads(test_doc.get("_comments"))
		self.assertEqual(comments[0].get("name"), comment.name)
		self.assertEqual(comments[0].get("comment"), comment.content)

		# check document creation
		comment_1 = sparrow.get_all(
			"Comment",
			fields=["*"],
			filters=dict(reference_doctype=test_doc.doctype, reference_name=test_doc.name),
		)[0]

		self.assertEqual(comment_1.content, "test comment")

	# test via blog
	def test_public_comment(self):
		test_blog = make_test_blog()

		sparrow.db.delete("Comment", {"reference_doctype": "Blog Post"})

		sparrow.form_dict.comment = "Good comment with 10 chars"
		sparrow.form_dict.comment_email = "test@test.com"
		sparrow.form_dict.comment_by = "Good Tester"
		sparrow.form_dict.reference_doctype = "Blog Post"
		sparrow.form_dict.reference_name = test_blog.name
		sparrow.form_dict.route = test_blog.route
		sparrow.local.request_ip = "127.0.0.1"

		add_comment()

		self.assertEqual(
			sparrow.get_all(
				"Comment",
				fields=["*"],
				filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
			)[0].published,
			1,
		)

		sparrow.db.delete("Comment", {"reference_doctype": "Blog Post"})

		sparrow.form_dict.comment = "pleez vizits my site http://mysite.com"
		sparrow.form_dict.comment_by = "bad commentor"

		add_comment()

		self.assertEqual(
			len(
				sparrow.get_all(
					"Comment",
					fields=["*"],
					filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
				)
			),
			0,
		)

		# test for filtering html and css injection elements
		sparrow.db.delete("Comment", {"reference_doctype": "Blog Post"})

		sparrow.form_dict.comment = "<script>alert(1)</script>Comment"
		sparrow.form_dict.comment_by = "hacker"

		add_comment()

		self.assertEqual(
			sparrow.get_all(
				"Comment",
				fields=["content"],
				filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
			)[0]["content"],
			"Comment",
		)

		test_blog.delete()

	@change_settings("Blog Settings", {"allow_guest_to_comment": 0})
	def test_guest_cannot_comment(self):
		test_blog = make_test_blog()
		with set_user("Guest"):
			sparrow.form_dict.comment = "Good comment with 10 chars"
			sparrow.form_dict.comment_email = "mail@example.org"
			sparrow.form_dict.comment_by = "Good Tester"
			sparrow.form_dict.reference_doctype = "Blog Post"
			sparrow.form_dict.reference_name = test_blog.name
			sparrow.form_dict.route = test_blog.route
			sparrow.local.request_ip = "127.0.0.1"

			self.assertEqual(add_comment(), None)

	def test_user_not_logged_in(self):
		some_system_user = sparrow.db.get_value("User", {})

		test_blog = make_test_blog()
		with set_user("Guest"):
			sparrow.form_dict.comment = "Good comment with 10 chars"
			sparrow.form_dict.comment_email = some_system_user
			sparrow.form_dict.comment_by = "Good Tester"
			sparrow.form_dict.reference_doctype = "Blog Post"
			sparrow.form_dict.reference_name = test_blog.name
			sparrow.form_dict.route = test_blog.route
			sparrow.local.request_ip = "127.0.0.1"

			self.assertRaises(sparrow.ValidationError, add_comment)
