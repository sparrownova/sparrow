# Copyright (c) 2013, Sparrow and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.website.doctype.help_article.help_article import clear_cache
from sparrow.website.website_generator import WebsiteGenerator


class HelpCategory(WebsiteGenerator):
	website = sparrow._dict(condition_field="published", page_title_field="category_name")

	def before_insert(self):
		self.published = 1

	def autoname(self):
		self.name = self.category_name

	def validate(self):
		self.set_route()

	def set_route(self):
		if not self.route:
			self.route = "kb/" + self.scrub(self.category_name)

	def on_update(self):
		clear_cache()
