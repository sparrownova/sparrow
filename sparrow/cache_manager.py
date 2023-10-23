# Copyright (c) 2018, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow

common_default_keys = ["__default", "__global"]

doctypes_for_mapping = {
	"Energy Point Rule",
	"Assignment Rule",
	"Milestone Tracker",
	"Document Naming Rule",
}


def get_doctype_map_key(doctype):
	return sparrow.scrub(doctype) + "_map"


doctype_map_keys = tuple(map(get_doctype_map_key, doctypes_for_mapping))

snova_cache_keys = ("assets_json",)

global_cache_keys = (
	"app_hooks",
	"installed_apps",
	"all_apps",
	"app_modules",
	"module_app",
	"system_settings",
	"scheduler_events",
	"time_zone",
	"webhooks",
	"active_domains",
	"active_modules",
	"assignment_rule",
	"server_script_map",
	"wkhtmltopdf_version",
	"domain_restricted_doctypes",
	"domain_restricted_pages",
	"information_schema:counts",
	"sitemap_routes",
	"db_tables",
	"server_script_autocompletion_items",
) + doctype_map_keys

user_cache_keys = (
	"bootinfo",
	"user_recent",
	"roles",
	"user_doc",
	"lang",
	"defaults",
	"user_permissions",
	"home_page",
	"linked_with",
	"desktop_icons",
	"portal_menu_items",
	"user_perm_can_read",
	"has_role:Page",
	"has_role:Report",
	"desk_sidebar_items",
	"contacts",
)

doctype_cache_keys = (
	"doctype_meta",
	"doctype_form_meta",
	"table_columns",
	"last_modified",
	"linked_doctypes",
	"notifications",
	"workflow",
	"data_import_column_header_map",
)


def clear_user_cache(user=None):
	from sparrow.desk.notifications import clear_notifications

	cache = sparrow.cache()

	# this will automatically reload the global cache
	# so it is important to clear this first
	clear_notifications(user)

	if user:
		for name in user_cache_keys:
			cache.hdel(name, user)
		cache.delete_keys("user:" + user)
		clear_defaults_cache(user)
	else:
		for name in user_cache_keys:
			cache.delete_key(name)
		clear_defaults_cache()
		clear_global_cache()


def clear_domain_cache(user=None):
	cache = sparrow.cache()
	domain_cache_keys = ("domain_restricted_doctypes", "domain_restricted_pages")
	cache.delete_value(domain_cache_keys)


def clear_global_cache():
	from sparrow.website.utils import clear_website_cache

	clear_doctype_cache()
	clear_website_cache()
	sparrow.cache().delete_value(global_cache_keys)
	sparrow.cache().delete_value(snova_cache_keys)
	sparrow.setup_module_map()


def clear_defaults_cache(user=None):
	if user:
		for p in [user] + common_default_keys:
			sparrow.cache().hdel("defaults", p)
	elif sparrow.flags.in_install != "sparrow":
		sparrow.cache().delete_key("defaults")


def clear_doctype_cache(doctype=None):
	from sparrow.desk.notifications import delete_notification_count_for

	clear_controller_cache(doctype)

	cache = sparrow.cache()

	for key in ("is_table", "doctype_modules", "document_cache"):
		cache.delete_value(key)

	sparrow.local.document_cache = {}

	def clear_single(dt):
		for name in doctype_cache_keys:
			cache.hdel(name, dt)

	if doctype:
		clear_single(doctype)

		# clear all parent doctypes
		for dt in sparrow.get_all(
			"DocField", "parent", dict(fieldtype=["in", sparrow.model.table_fields], options=doctype)
		):
			clear_single(dt.parent)

		# clear all parent doctypes
		if not sparrow.flags.in_install:
			for dt in sparrow.get_all(
				"Custom Field", "dt", dict(fieldtype=["in", sparrow.model.table_fields], options=doctype)
			):
				clear_single(dt.dt)

		# clear all notifications
		delete_notification_count_for(doctype)

	else:
		# clear all
		for name in doctype_cache_keys:
			cache.delete_value(name)


def clear_controller_cache(doctype=None):
	if not doctype:
		sparrow.controllers.pop(sparrow.local.site, None)
		return

	if site_controllers := sparrow.controllers.get(sparrow.local.site):
		site_controllers.pop(doctype, None)


def get_doctype_map(doctype, name, filters=None, order_by=None):
	return sparrow.cache().hget(
		get_doctype_map_key(doctype),
		name,
		lambda: sparrow.get_all(doctype, filters=filters, order_by=order_by, ignore_ddl=True),
	)


def clear_doctype_map(doctype, name):
	sparrow.cache().hdel(sparrow.scrub(doctype) + "_map", name)


def build_table_count_cache():
	if (
		sparrow.flags.in_patch
		or sparrow.flags.in_install
		or sparrow.flags.in_migrate
		or sparrow.flags.in_import
		or sparrow.flags.in_setup_wizard
	):
		return

	_cache = sparrow.cache()
	table_name = sparrow.qb.Field("table_name").as_("name")
	table_rows = sparrow.qb.Field("table_rows").as_("count")
	information_schema = sparrow.qb.Schema("information_schema")

	data = (sparrow.qb.from_(information_schema.tables).select(table_name, table_rows)).run(
		as_dict=True
	)
	counts = {d.get("name").replace("tab", "", 1): d.get("count", None) for d in data}
	_cache.set_value("information_schema:counts", counts)

	return counts


def build_domain_restriced_doctype_cache(*args, **kwargs):
	if (
		sparrow.flags.in_patch
		or sparrow.flags.in_install
		or sparrow.flags.in_migrate
		or sparrow.flags.in_import
		or sparrow.flags.in_setup_wizard
	):
		return
	_cache = sparrow.cache()
	active_domains = sparrow.get_active_domains()
	doctypes = sparrow.get_all("DocType", filters={"restrict_to_domain": ("IN", active_domains)})
	doctypes = [doc.name for doc in doctypes]
	_cache.set_value("domain_restricted_doctypes", doctypes)

	return doctypes


def build_domain_restriced_page_cache(*args, **kwargs):
	if (
		sparrow.flags.in_patch
		or sparrow.flags.in_install
		or sparrow.flags.in_migrate
		or sparrow.flags.in_import
		or sparrow.flags.in_setup_wizard
	):
		return
	_cache = sparrow.cache()
	active_domains = sparrow.get_active_domains()
	pages = sparrow.get_all("Page", filters={"restrict_to_domain": ("IN", active_domains)})
	pages = [page.name for page in pages]
	_cache.set_value("domain_restricted_pages", pages)

	return pages
