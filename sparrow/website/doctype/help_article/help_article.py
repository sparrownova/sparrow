# Copyright (c) 2013, Sparrow and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.rate_limiter import rate_limit
from sparrow.utils import cint, is_markdown, markdown
from sparrow.website.utils import get_comment_list
from sparrow.website.website_generator import WebsiteGenerator


class HelpArticle(WebsiteGenerator):
	def validate(self):
		self.set_route()

	def set_route(self):
		"""Set route from category and title if missing"""
		if not self.route:
			self.route = "/".join(
				[sparrow.get_value("Help Category", self.category, "route"), self.scrub(self.title)]
			)

	def on_update(self):
		self.update_category()
		clear_cache()

	def update_category(self):
		cnt = sparrow.db.sql(
			"""select count(*) from `tabHelp Article`
			where category=%s and ifnull(published,0)=1""",
			self.category,
		)[0][0]
		cat = sparrow.get_doc("Help Category", self.category)
		cat.help_articles = cnt
		cat.save()

	def get_context(self, context):
		if is_markdown(context.content):
			context.content = markdown(context.content)
		context.login_required = True
		context.category = sparrow.get_doc("Help Category", self.category)
		context.level_class = get_level_class(self.level)
		context.comment_list = get_comment_list(self.doctype, self.name)
		context.show_sidebar = True
		context.sidebar_items = get_sidebar_items()
		context.parents = self.get_parents(context)

	def get_parents(self, context):
		return [{"title": context.category.category_name, "route": context.category.route}]


def get_list_context(context=None):
	filters = dict(published=1)

	category = sparrow.db.get_value("Help Category", {"route": sparrow.local.path})

	if category:
		filters["category"] = category

	list_context = sparrow._dict(
		title=category or _("Knowledge Base"),
		get_level_class=get_level_class,
		show_sidebar=True,
		sidebar_items=get_sidebar_items(),
		hide_filters=True,
		filters=filters,
		category=sparrow.local.form_dict.category,
		no_breadcrumbs=True,
	)

	if sparrow.local.form_dict.txt:
		list_context.blog_subtitle = _('Filtered by "{0}"').format(sparrow.local.form_dict.txt)
	#
	# list_context.update(sparrow.get_doc("Blog Settings", "Blog Settings").as_dict())
	return list_context


def get_level_class(level):
	return {"Beginner": "green", "Intermediate": "orange", "Expert": "red"}[level]


def get_sidebar_items():
	def _get():
		return sparrow.db.sql(
			"""select
				concat(category_name, " (", help_articles, ")") as title,
				concat('/', route) as route
			from
				`tabHelp Category`
			where
				ifnull(published,0)=1 and help_articles > 0
			order by
				help_articles desc""",
			as_dict=True,
		)

	return sparrow.cache().get_value("knowledge_base:category_sidebar", _get)


def clear_cache():
	clear_website_cache()

	from sparrow.website.utils import clear_cache

	clear_cache()


def clear_website_cache(path=None):
	sparrow.cache().delete_value("knowledge_base:category_sidebar")
	sparrow.cache().delete_value("knowledge_base:faq")


@sparrow.whitelist(allow_guest=True)
@rate_limit(key="article", limit=5, seconds=60 * 60)
def add_feedback(article: str, helpful: str):
	if not isinstance("article", str):
		sparrow.throw(_("Invalid Article Name"))

	field = "not_helpful" if helpful == "No" else "helpful"
	value = cint(sparrow.db.get_value("Help Article", article, field))
	sparrow.db.set_value("Help Article", article, field, value + 1, update_modified=False)
