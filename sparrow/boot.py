# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
"""
bootstrap client session
"""

import sparrow
import sparrow.defaults
import sparrow.desk.desk_page
from sparrow.core.doctype.navbar_settings.navbar_settings import get_app_logo, get_navbar_settings
from sparrow.desk.doctype.form_tour.form_tour import get_onboarding_ui_tours
from sparrow.desk.doctype.route_history.route_history import frequently_visited_links
from sparrow.desk.form.load import get_meta_bundle
from sparrow.email.inbox import get_email_accounts
from sparrow.model.base_document import get_controller
from sparrow.permissions import has_permission
from sparrow.query_builder import DocType
from sparrow.query_builder.functions import Count
from sparrow.query_builder.terms import ParameterizedValueWrapper, SubQuery
from sparrow.social.doctype.energy_point_log.energy_point_log import get_energy_points
from sparrow.social.doctype.energy_point_settings.energy_point_settings import (
	is_energy_point_enabled,
)
from sparrow.utils import add_user_info, cstr, get_system_timezone
from sparrow.utils.change_log import get_versions
from sparrow.website.doctype.web_page_view.web_page_view import is_tracking_enabled


def get_bootinfo():
	"""build and return boot info"""
	from sparrow.translate import get_lang_dict, get_translated_doctypes

	sparrow.set_user_lang(sparrow.session.user)
	bootinfo = sparrow._dict()
	hooks = sparrow.get_hooks()
	doclist = []

	# user
	get_user(bootinfo)

	# system info
	bootinfo.sitename = sparrow.local.site
	bootinfo.sysdefaults = sparrow.defaults.get_defaults()
	bootinfo.server_date = sparrow.utils.nowdate()

	if sparrow.session["user"] != "Guest":
		bootinfo.user_info = get_user_info()
		bootinfo.sid = sparrow.session["sid"]

	bootinfo.modules = {}
	bootinfo.module_list = []
	load_desktop_data(bootinfo)
	bootinfo.letter_heads = get_letter_heads()
	bootinfo.active_domains = sparrow.get_active_domains()
	bootinfo.all_domains = [d.get("name") for d in sparrow.get_all("Domain")]
	add_layouts(bootinfo)

	bootinfo.module_app = sparrow.local.module_app
	bootinfo.single_types = [d.name for d in sparrow.get_all("DocType", {"issingle": 1})]
	bootinfo.nested_set_doctypes = [
		d.parent for d in sparrow.get_all("DocField", {"fieldname": "lft"}, ["parent"])
	]
	add_home_page(bootinfo, doclist)
	bootinfo.page_info = get_allowed_pages()
	load_translations(bootinfo)
	add_timezone_info(bootinfo)
	load_conf_settings(bootinfo)
	load_print(bootinfo, doclist)
	doclist.extend(get_meta_bundle("Page"))
	bootinfo.home_folder = sparrow.db.get_value("File", {"is_home_folder": 1})
	bootinfo.navbar_settings = get_navbar_settings()
	bootinfo.notification_settings = get_notification_settings()
	bootinfo.onboarding_tours = get_onboarding_ui_tours()
	set_time_zone(bootinfo)

	# ipinfo
	if sparrow.session.data.get("ipinfo"):
		bootinfo.ipinfo = sparrow.session["data"]["ipinfo"]

	# add docs
	bootinfo.docs = doclist
	load_country_doc(bootinfo)
	load_currency_docs(bootinfo)

	for method in hooks.boot_session or []:
		sparrow.get_attr(method)(bootinfo)

	if bootinfo.lang:
		bootinfo.lang = str(bootinfo.lang)
	bootinfo.versions = {k: v["version"] for k, v in get_versions().items()}

	bootinfo.error_report_email = sparrow.conf.error_report_email
	bootinfo.calendars = sorted(sparrow.get_hooks("calendars"))
	bootinfo.treeviews = sparrow.get_hooks("treeviews") or []
	bootinfo.lang_dict = get_lang_dict()
	bootinfo.success_action = get_success_action()
	bootinfo.update(get_email_accounts(user=sparrow.session.user))
	bootinfo.energy_points_enabled = is_energy_point_enabled()
	bootinfo.website_tracking_enabled = is_tracking_enabled()
	bootinfo.points = get_energy_points(sparrow.session.user)
	bootinfo.frequently_visited_links = frequently_visited_links()
	bootinfo.link_preview_doctypes = get_link_preview_doctypes()
	bootinfo.additional_filters_config = get_additional_filters_from_hooks()
	bootinfo.desk_settings = get_desk_settings()
	bootinfo.app_logo_url = get_app_logo()
	bootinfo.link_title_doctypes = get_link_title_doctypes()
	bootinfo.translated_doctypes = get_translated_doctypes()
	bootinfo.subscription_conf = add_subscription_conf()

	return bootinfo


def get_letter_heads():
	letter_heads = {}
	for letter_head in sparrow.get_all("Letter Head", fields=["name", "content", "footer"]):
		letter_heads.setdefault(
			letter_head.name, {"header": letter_head.content, "footer": letter_head.footer}
		)

	return letter_heads


def load_conf_settings(bootinfo):
	from sparrow import conf

	bootinfo.max_file_size = conf.get("max_file_size") or 10485760
	for key in ("developer_mode", "socketio_port", "file_watcher_port"):
		if key in conf:
			bootinfo[key] = conf.get(key)


def load_desktop_data(bootinfo):
	from sparrow.desk.desktop import get_workspace_sidebar_items

	bootinfo.allowed_workspaces = get_workspace_sidebar_items().get("pages")
	bootinfo.module_wise_workspaces = get_controller("Workspace").get_module_wise_workspaces()
	bootinfo.dashboards = sparrow.get_all("Dashboard")


def get_allowed_pages(cache=False):
	return get_user_pages_or_reports("Page", cache=cache)


def get_allowed_reports(cache=False):
	return get_user_pages_or_reports("Report", cache=cache)


def get_allowed_report_names(cache=False) -> set[str]:
	return {cstr(report) for report in get_allowed_reports(cache).keys() if report}


def get_user_pages_or_reports(parent, cache=False):
	_cache = sparrow.cache()

	if cache:
		has_role = _cache.get_value("has_role:" + parent, user=sparrow.session.user)
		if has_role:
			return has_role

	roles = sparrow.get_roles()
	has_role = {}

	page = DocType("Page")
	report = DocType("Report")

	if parent == "Report":
		columns = (report.name.as_("title"), report.ref_doctype, report.report_type)
	else:
		columns = (page.title.as_("title"),)

	customRole = DocType("Custom Role")
	hasRole = DocType("Has Role")
	parentTable = DocType(parent)

	# get pages or reports set on custom role
	pages_with_custom_roles = (
		sparrow.qb.from_(customRole)
		.from_(hasRole)
		.from_(parentTable)
		.select(
			customRole[parent.lower()].as_("name"), customRole.modified, customRole.ref_doctype, *columns
		)
		.where(
			(hasRole.parent == customRole.name)
			& (parentTable.name == customRole[parent.lower()])
			& (customRole[parent.lower()].isnotnull())
			& (hasRole.role.isin(roles))
		)
	).run(as_dict=True)

	for p in pages_with_custom_roles:
		has_role[p.name] = {"modified": p.modified, "title": p.title, "ref_doctype": p.ref_doctype}

	subq = (
		sparrow.qb.from_(customRole)
		.select(customRole[parent.lower()])
		.where(customRole[parent.lower()].isnotnull())
	)

	pages_with_standard_roles = (
		sparrow.qb.from_(hasRole)
		.from_(parentTable)
		.select(parentTable.name.as_("name"), parentTable.modified, *columns)
		.where(
			(hasRole.role.isin(roles))
			& (hasRole.parent == parentTable.name)
			& (parentTable.name.notin(subq))
		)
		.distinct()
	)

	if parent == "Report":
		pages_with_standard_roles = pages_with_standard_roles.where(report.disabled == 0)

	pages_with_standard_roles = pages_with_standard_roles.run(as_dict=True)

	for p in pages_with_standard_roles:
		if p.name not in has_role:
			has_role[p.name] = {"modified": p.modified, "title": p.title}
			if parent == "Report":
				has_role[p.name].update({"ref_doctype": p.ref_doctype})

	no_of_roles = SubQuery(
		sparrow.qb.from_(hasRole).select(Count("*")).where(hasRole.parent == parentTable.name)
	)

	# pages with no role are allowed
	if parent == "Page":

		pages_with_no_roles = (
			sparrow.qb.from_(parentTable)
			.select(parentTable.name, parentTable.modified, *columns)
			.where(no_of_roles == 0)
		).run(as_dict=True)

		for p in pages_with_no_roles:
			if p.name not in has_role:
				has_role[p.name] = {"modified": p.modified, "title": p.title}

	elif parent == "Report":
		if not has_permission("Report", raise_exception=False):
			return {}

		reports = sparrow.get_list(
			"Report",
			fields=["name", "report_type"],
			filters={"name": ("in", has_role.keys())},
			ignore_ifnull=True,
		)
		for report in reports:
			has_role[report.name]["report_type"] = report.report_type

		non_permitted_reports = set(has_role.keys()) - {r.name for r in reports}
		for r in non_permitted_reports:
			has_role.pop(r, None)

	# Expire every six hours
	_cache.set_value("has_role:" + parent, has_role, sparrow.session.user, 21600)
	return has_role


def load_translations(bootinfo):
	from sparrow.translate import get_messages_for_boot

	bootinfo["lang"] = sparrow.lang
	bootinfo["__messages"] = get_messages_for_boot()


def get_user_info():
	# get info for current user
	user_info = sparrow._dict()
	add_user_info(sparrow.session.user, user_info)

	if sparrow.session.user == "Administrator" and user_info.Administrator.email:
		user_info[user_info.Administrator.email] = user_info.Administrator

	return user_info


def get_user(bootinfo):
	"""get user info"""
	bootinfo.user = sparrow.get_user().load_user()


def add_home_page(bootinfo, docs):
	"""load home page"""
	if sparrow.session.user == "Guest":
		return
	home_page = sparrow.db.get_default("desktop:home_page")

	if home_page == "setup-wizard":
		bootinfo.setup_wizard_requires = sparrow.get_hooks("setup_wizard_requires")

	try:
		page = sparrow.desk.desk_page.get(home_page)
		docs.append(page)
		bootinfo["home_page"] = page.name
	except (sparrow.DoesNotExistError, sparrow.PermissionError):
		if sparrow.message_log:
			sparrow.message_log.pop()
		bootinfo["home_page"] = "Workspaces"


def add_timezone_info(bootinfo):
	system = bootinfo.sysdefaults.get("time_zone")
	import sparrow.utils.momentjs

	bootinfo.timezone_info = {"zones": {}, "rules": {}, "links": {}}
	sparrow.utils.momentjs.update(system, bootinfo.timezone_info)


def load_print(bootinfo, doclist):
	print_settings = sparrow.db.get_singles_dict("Print Settings")
	print_settings.doctype = ":Print Settings"
	doclist.append(print_settings)
	load_print_css(bootinfo, print_settings)


def load_print_css(bootinfo, print_settings):
	import sparrow.www.printview

	bootinfo.print_css = sparrow.www.printview.get_print_style(
		print_settings.print_style or "Redesign", for_legacy=True
	)


def get_unseen_notes():
	note = DocType("Note")
	nsb = DocType("Note Seen By").as_("nsb")

	return (
		sparrow.qb.from_(note)
		.select(note.name, note.title, note.content, note.notify_on_every_login)
		.where(
			(note.notify_on_login == 1)
			& (note.expire_notification_on > sparrow.utils.now())
			& (
				ParameterizedValueWrapper(sparrow.session.user).notin(
					SubQuery(sparrow.qb.from_(nsb).select(nsb.user).where(nsb.parent == note.name))
				)
			)
		)
	).run(as_dict=1)


def get_success_action():
	return sparrow.get_all("Success Action", fields=["*"])


def get_link_preview_doctypes():
	from sparrow.utils import cint

	link_preview_doctypes = [d.name for d in sparrow.get_all("DocType", {"show_preview_popup": 1})]
	customizations = sparrow.get_all(
		"Property Setter", fields=["doc_type", "value"], filters={"property": "show_preview_popup"}
	)

	for custom in customizations:
		if not cint(custom.value) and custom.doc_type in link_preview_doctypes:
			link_preview_doctypes.remove(custom.doc_type)
		else:
			link_preview_doctypes.append(custom.doc_type)

	return link_preview_doctypes


def get_additional_filters_from_hooks():
	filter_config = sparrow._dict()
	filter_hooks = sparrow.get_hooks("filters_config")
	for hook in filter_hooks:
		filter_config.update(sparrow.get_attr(hook)())

	return filter_config


def add_layouts(bootinfo):
	# add routes for readable doctypes
	bootinfo.doctype_layouts = sparrow.get_all("DocType Layout", ["name", "route", "document_type"])


def get_desk_settings():
	role_list = sparrow.get_all("Role", fields=["*"], filters=dict(name=["in", sparrow.get_roles()]))
	desk_settings = {}

	from sparrow.core.doctype.role.role import desk_properties

	for role in role_list:
		for key in desk_properties:
			desk_settings[key] = desk_settings.get(key) or role.get(key)

	return desk_settings


def get_notification_settings():
	return sparrow.get_cached_doc("Notification Settings", sparrow.session.user)


def get_link_title_doctypes():
	dts = sparrow.get_all("DocType", {"show_title_field_in_link": 1})
	custom_dts = sparrow.get_all(
		"Property Setter",
		{"property": "show_title_field_in_link", "value": "1"},
		["doc_type as name"],
	)
	return [d.name for d in dts + custom_dts if d]


def set_time_zone(bootinfo):
	bootinfo.time_zone = {
		"system": get_system_timezone(),
		"user": bootinfo.get("user_info", {}).get(sparrow.session.user, {}).get("time_zone", None)
		or get_system_timezone(),
	}


def load_country_doc(bootinfo):
	country = sparrow.db.get_default("country")
	if not country:
		return
	try:
		bootinfo.docs.append(sparrow.get_cached_doc("Country", country))
	except Exception:
		pass


def load_currency_docs(bootinfo):
	currency = sparrow.qb.DocType("Currency")

	currency_docs = (
		sparrow.qb.from_(currency)
		.select(
			currency.name,
			currency.fraction,
			currency.fraction_units,
			currency.number_format,
			currency.smallest_currency_fraction_value,
			currency.symbol,
			currency.symbol_on_right,
		)
		.where(currency.enabled == 1)
		.run(as_dict=1, update={"doctype": ":Currency"})
	)

	bootinfo.docs += currency_docs


def add_subscription_conf():
	try:
		return sparrow.conf.subscription
	except Exception:
		return ""
