# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.boot import get_allowed_pages, get_allowed_reports
from sparrow.cache_manager import (
	build_domain_restriced_doctype_cache,
	build_domain_restriced_page_cache,
	build_table_count_cache,
)
from sparrow.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache, set_hidden


@sparrow.whitelist()
def get(module):
	"""Returns data (sections, list of reports, counts) to render module view in desk:
	`/desk/#Module/[name]`."""
	data = get_data(module)

	out = {"data": data}

	return out


@sparrow.whitelist()
def hide_module(module):
	set_hidden(module, sparrow.session.user, 1)
	clear_desktop_icons_cache()


def get_table_with_counts():
	counts = sparrow.cache().get_value("information_schema:counts")
	if counts:
		return counts
	else:
		return build_table_count_cache()


def get_data(module, build=True):
	"""Get module data for the module view `desk/#Module/[name]`"""
	doctype_info = get_doctype_info(module)
	data = build_config_from_file(module)

	if not data:
		data = build_standard_config(module, doctype_info)
	else:
		add_custom_doctypes(data, doctype_info)

	add_section(data, _("Custom Reports"), "fa fa-list-alt", get_report_list(module))

	data = combine_common_sections(data)
	data = apply_permissions(data)

	# set_last_modified(data)

	if build:
		exists_cache = get_table_with_counts()

		def doctype_contains_a_record(name):
			exists = exists_cache.get(name)
			if not exists:
				if not sparrow.db.get_value("DocType", name, "issingle"):
					exists = sparrow.db.count(name)
				else:
					exists = True
				exists_cache[name] = exists
			return exists

		for section in data:
			for item in section["items"]:
				# Onboarding

				# First disable based on exists of depends_on list
				doctype = item.get("doctype")
				dependencies = item.get("dependencies") or None
				if not dependencies and doctype:
					item["dependencies"] = [doctype]

				dependencies = item.get("dependencies")
				if dependencies:
					incomplete_dependencies = [d for d in dependencies if not doctype_contains_a_record(d)]
					if len(incomplete_dependencies):
						item["incomplete_dependencies"] = incomplete_dependencies

				if item.get("onboard"):
					# Mark Spotlights for initial
					if item.get("type") == "doctype":
						name = item.get("name")
						count = doctype_contains_a_record(name)

						item["count"] = count

	return data


def build_config_from_file(module):
	"""Build module info from `app/config/desktop.py` files."""
	data = []
	module = sparrow.scrub(module)

	for app in sparrow.get_installed_apps():
		try:
			data += get_config(app, module)
		except ImportError:
			pass

	return filter_by_restrict_to_domain(data)


def filter_by_restrict_to_domain(data):
	"""filter Pages and DocType depending on the Active Module(s)"""
	doctypes = (
            sparrow.cache().get_value("domain_restricted_doctypes") or build_domain_restriced_doctype_cache()
	)
	pages = sparrow.cache().get_value("domain_restricted_pages") or build_domain_restriced_page_cache()

	for d in data:
		_items = []
		for item in d.get("items", []):

			item_type = item.get("type")
			item_name = item.get("name")

			if (item_name in pages) or (item_name in doctypes) or item_type == "report":
				_items.append(item)

		d.update({"items": _items})

	return data


def build_standard_config(module, doctype_info):
	"""Build standard module data from DocTypes."""
	if not sparrow.db.get_value("Module Def", module):
		sparrow.throw(_("Module Not Found"))

	data = []

	add_section(
		data,
		_("Documents"),
		"fa fa-star",
		[d for d in doctype_info if d.document_type in ("Document", "Transaction")],
	)

	add_section(
		data,
		_("Setup"),
		"fa fa-cog",
		[d for d in doctype_info if d.document_type in ("Master", "Setup", "")],
	)

	add_section(data, _("Standard Reports"), "fa fa-list", get_report_list(module, is_standard="Yes"))

	return data


def add_section(data, label, icon, items):
	"""Adds a section to the module data."""
	if not items:
		return
	data.append({"label": label, "icon": icon, "items": items})


def add_custom_doctypes(data, doctype_info):
	"""Adds Custom DocTypes to modules setup via `config/desktop.py`."""
	add_section(
		data,
		_("Documents"),
		"fa fa-star",
		[d for d in doctype_info if (d.custom and d.document_type in ("Document", "Transaction"))],
	)

	add_section(
		data,
		_("Setup"),
		"fa fa-cog",
		[d for d in doctype_info if (d.custom and d.document_type in ("Setup", "Master", ""))],
	)


def get_doctype_info(module):
	"""Returns list of non child DocTypes for given module."""
	active_domains = sparrow.get_active_domains()

	doctype_info = sparrow.get_all(
		"DocType",
		filters={"module": module, "istable": 0},
		or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
		fields=["'doctype' as type", "name", "description", "document_type", "custom", "issingle"],
		order_by="custom asc, document_type desc, name asc",
	)

	for d in doctype_info:
		d.document_type = d.document_type or ""
		d.description = _(d.description or "")

	return doctype_info


def combine_common_sections(data):
	"""Combine sections declared in separate apps."""
	sections = []
	sections_dict = {}
	for each in data:
		if each["label"] not in sections_dict:
			sections_dict[each["label"]] = each
			sections.append(each)
		else:
			sections_dict[each["label"]]["items"] += each["items"]

	return sections


def apply_permissions(data):
	default_country = sparrow.db.get_default("country")

	user = sparrow.get_user()
	user.build_permissions()

	allowed_pages = get_allowed_pages()
	allowed_reports = get_allowed_reports()

	new_data = []
	for section in data:
		new_items = []

		for item in section.get("items") or []:
			item = sparrow._dict(item)

			if item.country and item.country != default_country:
				continue

			if (
				(item.type == "doctype" and item.name in user.can_read)
				or (item.type == "page" and item.name in allowed_pages)
				or (item.type == "report" and item.name in allowed_reports)
				or item.type == "help"
			):

				new_items.append(item)

		if new_items:
			new_section = section.copy()
			new_section["items"] = new_items
			new_data.append(new_section)

	return new_data


def get_disabled_reports():
	if not hasattr(sparrow.local, "disabled_reports"):
		sparrow.local.disabled_reports = {r.name for r in sparrow.get_all("Report", {"disabled": 1})}
	return sparrow.local.disabled_reports


def get_config(app, module):
	"""Load module info from `[app].config.[module]`."""
	config = sparrow.get_module(f"{app}.config.{module}")
	config = config.get_data()

	sections = [s for s in config if s.get("condition", True)]

	disabled_reports = get_disabled_reports()
	for section in sections:
		items = []
		for item in section["items"]:
			if item["type"] == "report" and item["name"] in disabled_reports:
				continue
			# some module links might not have name
			if not item.get("name"):
				item["name"] = item.get("label")
			if not item.get("label"):
				item["label"] = _(item.get("name"))
			items.append(item)
		section["items"] = items

	return sections


def config_exists(app, module):
	try:
		sparrow.get_module(f"{app}.config.{module}")
		return True
	except ImportError:
		return False


def add_setup_section(config, app, module, label, icon):
	"""Add common sections to `/desk#Module/Setup`"""
	try:
		setup_section = get_setup_section(app, module, label, icon)
		if setup_section:
			config.append(setup_section)
	except ImportError:
		pass


def get_setup_section(app, module, label, icon):
	"""Get the setup section from each module (for global Setup page)."""
	config = get_config(app, module)
	for section in config:
		if section.get("label") == _("Setup"):
			return {"label": label, "icon": icon, "items": section["items"]}


def get_onboard_items(app, module):
	try:
		sections = get_config(app, module)
	except ImportError:
		return []

	onboard_items = []
	fallback_items = []

	if not sections:
		doctype_info = get_doctype_info(module)
		sections = build_standard_config(module, doctype_info)

	for section in sections:
		for item in section["items"]:
			if item.get("onboard", 0) == 1:
				onboard_items.append(item)

			# in case onboard is not set
			fallback_items.append(item)

			if len(onboard_items) > 5:
				return onboard_items

	return onboard_items or fallback_items


@sparrow.whitelist()
def get_links_for_module(app, module):
	return [{"value": l.get("name"), "label": l.get("label")} for l in get_links(app, module)]


def get_links(app, module):
	try:
		sections = get_config(app, sparrow.scrub(module))
	except ImportError:
		return []

	links = []
	for section in sections:
		for item in section["items"]:
			links.append(item)
	return links


@sparrow.whitelist()
def get_desktop_settings():
	from sparrow.config import get_modules_from_all_apps_for_user

	all_modules = get_modules_from_all_apps_for_user()
	home_settings = get_home_settings()

	modules_by_name = {}
	for m in all_modules:
		modules_by_name[m["module_name"]] = m

	module_categories = ["Modules", "Domains", "Places", "Administration"]
	user_modules_by_category = {}

	user_saved_modules_by_category = home_settings.modules_by_category or {}
	user_saved_links_by_module = home_settings.links_by_module or {}

	def apply_user_saved_links(module):
		module = sparrow._dict(module)
		all_links = get_links(module.app, module.module_name)
		module_links_by_name = {}
		for link in all_links:
			module_links_by_name[link["name"]] = link

		if module.module_name in user_saved_links_by_module:
			user_links = sparrow.parse_json(user_saved_links_by_module[module.module_name])
			module.links = [module_links_by_name[l] for l in user_links if l in module_links_by_name]

		return module

	for category in module_categories:
		if category in user_saved_modules_by_category:
			user_modules = user_saved_modules_by_category[category]
			user_modules_by_category[category] = [
				apply_user_saved_links(modules_by_name[m]) for m in user_modules if modules_by_name.get(m)
			]
		else:
			user_modules_by_category[category] = [
				apply_user_saved_links(m) for m in all_modules if m.get("category") == category
			]

	# filter out hidden modules
	if home_settings.hidden_modules:
		for category in user_modules_by_category:
			hidden_modules = home_settings.hidden_modules or []
			modules = user_modules_by_category[category]
			user_modules_by_category[category] = [
				module for module in modules if module.module_name not in hidden_modules
			]

	return user_modules_by_category


@sparrow.whitelist()
def update_hidden_modules(category_map):
	category_map = sparrow.parse_json(category_map)
	home_settings = get_home_settings()

	saved_hidden_modules = home_settings.hidden_modules or []

	for category in category_map:
		config = sparrow._dict(category_map[category])
		saved_hidden_modules += config.removed or []
		saved_hidden_modules = [d for d in saved_hidden_modules if d not in (config.added or [])]

		if home_settings.get("modules_by_category") and home_settings.modules_by_category.get(category):
			module_placement = [
				d for d in (config.added or []) if d not in home_settings.modules_by_category[category]
			]
			home_settings.modules_by_category[category] += module_placement

	home_settings.hidden_modules = saved_hidden_modules
	set_home_settings(home_settings)

	return get_desktop_settings()


@sparrow.whitelist()
def update_global_hidden_modules(modules):
	modules = sparrow.parse_json(modules)
	sparrow.only_for("System Manager")

	doc = sparrow.get_doc("User", "Administrator")
	doc.set("block_modules", [])
	for module in modules:
		doc.append("block_modules", {"module": module})

	doc.save(ignore_permissions=True)

	return get_desktop_settings()


@sparrow.whitelist()
def update_modules_order(module_category, modules):
	modules = sparrow.parse_json(modules)
	home_settings = get_home_settings()

	home_settings.modules_by_category = home_settings.modules_by_category or {}
	home_settings.modules_by_category[module_category] = modules

	set_home_settings(home_settings)


@sparrow.whitelist()
def update_links_for_module(module_name, links):
	links = sparrow.parse_json(links)
	home_settings = get_home_settings()

	home_settings.setdefault("links_by_module", {})
	home_settings["links_by_module"].setdefault(module_name, None)
	home_settings["links_by_module"][module_name] = links

	set_home_settings(home_settings)

	return get_desktop_settings()


@sparrow.whitelist()
def get_options_for_show_hide_cards():
	global_options = []

	if "System Manager" in sparrow.get_roles():
		global_options = get_options_for_global_modules()

	return {"user_options": get_options_for_user_blocked_modules(), "global_options": global_options}


@sparrow.whitelist()
def get_options_for_global_modules():
	from sparrow.config import get_modules_from_all_apps

	all_modules = get_modules_from_all_apps()

	blocked_modules = sparrow.get_doc("User", "Administrator").get_blocked_modules()

	options = []
	for module in all_modules:
		module = sparrow._dict(module)
		options.append(
			{
				"category": module.category,
				"label": module.label,
				"value": module.module_name,
				"checked": module.module_name not in blocked_modules,
			}
		)

	return options


@sparrow.whitelist()
def get_options_for_user_blocked_modules():
	from sparrow.config import get_modules_from_all_apps_for_user

	all_modules = get_modules_from_all_apps_for_user()
	home_settings = get_home_settings()

	hidden_modules = home_settings.hidden_modules or []

	options = []
	for module in all_modules:
		module = sparrow._dict(module)
		options.append(
			{
				"category": module.category,
				"label": module.label,
				"value": module.module_name,
				"checked": module.module_name not in hidden_modules,
			}
		)

	return options


def set_home_settings(home_settings):
	sparrow.cache().hset("home_settings", sparrow.session.user, home_settings)
	sparrow.db.set_value("User", sparrow.session.user, "home_settings", json.dumps(home_settings))


@sparrow.whitelist()
def get_home_settings():
	def get_from_db():
		settings = sparrow.db.get_value("User", sparrow.session.user, "home_settings")
		return sparrow.parse_json(settings or "{}")

	home_settings = sparrow.cache().hget("home_settings", sparrow.session.user, get_from_db)
	return home_settings


def get_module_link_items_from_list(app, module, list_of_link_names):
	try:
		sections = get_config(app, sparrow.scrub(module))
	except ImportError:
		return []

	links = []
	for section in sections:
		for item in section["items"]:
			if item.get("label", "") in list_of_link_names:
				links.append(item)

	return links


def set_last_modified(data):
	for section in data:
		for item in section["items"]:
			if item["type"] == "doctype":
				item["last_modified"] = get_last_modified(item["name"])


def get_last_modified(doctype):
	def _get():
		try:
			last_modified = sparrow.get_all(
				doctype, fields=["max(modified)"], as_list=True, limit_page_length=1
			)[0][0]
		except Exception as e:
			if sparrow.db.is_table_missing(e):
				last_modified = None
			else:
				raise

		# hack: save as -1 so that it is cached
		if last_modified is None:
			last_modified = -1

		return last_modified

	last_modified = sparrow.cache().hget("last_modified", doctype, _get)

	if last_modified == -1:
		last_modified = None

	return last_modified


def get_report_list(module, is_standard="No"):
	"""Returns list on new style reports for modules."""
	reports = sparrow.get_list(
		"Report",
		fields=["name", "ref_doctype", "report_type"],
		filters={"is_standard": is_standard, "disabled": 0, "module": module},
		order_by="name",
	)

	out = []
	for r in reports:
		out.append(
			{
				"type": "report",
				"doctype": r.ref_doctype,
				"is_query_report": 1
				if r.report_type in ("Query Report", "Script Report", "Custom Report")
				else 0,
				"label": _(r.name),
				"name": r.name,
			}
		)

	return out
