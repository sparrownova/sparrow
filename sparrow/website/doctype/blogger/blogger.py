# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document


class Blogger(Document):
	def validate(self):
		if self.user and not sparrow.db.exists("User", self.user):
			# for data import
			sparrow.get_doc(
				{"doctype": "User", "email": self.user, "first_name": self.user.split("@", 1)[0]}
			).insert()

	def on_update(self):
		"if user is set, then update all older blogs"

		from sparrow.website.doctype.blog_post.blog_post import clear_blog_cache

		clear_blog_cache()

		if self.user:
			for blog in sparrow.db.sql_list(
				"""select name from `tabBlog Post` where owner=%s
				and ifnull(blogger,'')=''""",
				self.user,
			):
				b = sparrow.get_doc("Blog Post", blog)
				b.blogger = self.name
				b.save()

			sparrow.permissions.add_user_permission("Blogger", self.name, self.user)
