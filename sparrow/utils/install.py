# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import getpass

import sparrow
from sparrow.utils.password import update_password


def before_install():
	sparrow.reload_doc("core", "doctype", "doctype_state")
	sparrow.reload_doc("core", "doctype", "docfield")
	sparrow.reload_doc("core", "doctype", "docperm")
	sparrow.reload_doc("core", "doctype", "doctype_action")
	sparrow.reload_doc("core", "doctype", "doctype_link")
	sparrow.reload_doc("desk", "doctype", "form_tour_step")
	sparrow.reload_doc("desk", "doctype", "form_tour")
	sparrow.reload_doc("core", "doctype", "doctype")


def after_install():
	create_user_type()
	install_basic_docs()

	from sparrow.core.doctype.file.utils import make_home_folder

	make_home_folder()

	import_country_and_currency()

	from sparrow.core.doctype.language.language import sync_languages

	sync_languages()

	# save default print setting
	print_settings = sparrow.get_doc("Print Settings")
	print_settings.save()

	# all roles to admin
	sparrow.get_doc("User", "Administrator").add_roles(*sparrow.get_all("Role", pluck="name"))

	# update admin password
	update_password("Administrator", get_admin_password())

	if not sparrow.conf.skip_setup_wizard:
		# only set home_page if the value doesn't exist in the db
		if not sparrow.db.get_default("desktop:home_page"):
			sparrow.db.set_default("desktop:home_page", "setup-wizard")
			sparrow.db.set_single_value("System Settings", "setup_complete", 0)

	# clear test log
	with open(sparrow.get_site_path(".test_log"), "w") as f:
		f.write("")

	add_standard_navbar_items()

	sparrow.db.commit()


def create_user_type():
	for user_type in ["System User", "Website User"]:
		if not sparrow.db.exists("User Type", user_type):
			sparrow.get_doc({"doctype": "User Type", "name": user_type, "is_standard": 1}).insert(
				ignore_permissions=True
			)


def install_basic_docs():
	# core users / roles
	install_docs = [
		{
			"doctype": "User",
			"name": "Administrator",
			"first_name": "Administrator",
			"email": "admin@example.com",
			"enabled": 1,
			"is_admin": 1,
			"roles": [{"role": "Administrator"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{
			"doctype": "User",
			"name": "Guest",
			"first_name": "Guest",
			"email": "guest@example.com",
			"enabled": 1,
			"is_guest": 1,
			"roles": [{"role": "Guest"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{"doctype": "Role", "role_name": "Report Manager"},
		{"doctype": "Role", "role_name": "Translator"},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Pending",
			"icon": "question-sign",
			"style": "",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Approved",
			"icon": "ok-sign",
			"style": "Success",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Rejected",
			"icon": "remove",
			"style": "Danger",
		},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Approve"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Reject"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Review"},
		{
			"doctype": "Email Domain",
			"domain_name": "example.com",
			"email_id": "account@example.com",
			"password": "pass",
			"email_server": "imap.example.com",
			"use_imap": 1,
			"smtp_server": "smtp.example.com",
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "notifications@example.com",
			"default_outgoing": 1,
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "replies@example.com",
			"default_incoming": 1,
		},
	]

	for d in install_docs:
		try:
			sparrow.get_doc(d).insert(ignore_if_duplicate=True)
		except sparrow.NameError:
			pass


def get_admin_password():
	def ask_admin_password():
		admin_password = getpass.getpass("Set Administrator password: ")
		admin_password2 = getpass.getpass("Re-enter Administrator password: ")
		if not admin_password == admin_password2:
			print("\nPasswords do not match")
			return ask_admin_password()
		return admin_password

	admin_password = sparrow.conf.get("admin_password")
	if not admin_password:
		return ask_admin_password()
	return admin_password


def before_tests():
	if len(sparrow.get_installed_apps()) > 1:
		# don't run before tests if any other app is installed
		return

	sparrow.db.truncate("Custom Field")
	sparrow.db.truncate("Event")

	sparrow.clear_cache()

	# complete setup if missing
	if not int(sparrow.db.get_single_value("System Settings", "setup_complete") or 0):
		complete_setup_wizard()

	sparrow.db.set_single_value("Website Settings", "disable_signup", 0)
	sparrow.db.commit()
	sparrow.clear_cache()


def complete_setup_wizard():
	from sparrow.desk.page.setup_wizard.setup_wizard import setup_complete

	setup_complete(
		{
			"language": "English",
			"email": "test@shopper.com",
			"full_name": "Test User",
			"password": "test",
			"country": "United States",
			"timezone": "America/New_York",
			"currency": "USD",
		}
	)


def import_country_and_currency():
	from sparrow.geo.country_info import get_all
	from sparrow.utils import update_progress_bar

	data = get_all()

	for i, name in enumerate(data):
		update_progress_bar("Updating country info", i, len(data))
		country = sparrow._dict(data[name])
		add_country_and_currency(name, country)

	print("")

	# enable frequently used currencies
	for currency in ("INR", "USD", "GBP", "EUR", "AED", "AUD", "JPY", "CNY", "CHF"):
		sparrow.db.set_value("Currency", currency, "enabled", 1)


def add_country_and_currency(name, country):
	if not sparrow.db.exists("Country", name):
		sparrow.get_doc(
			{
				"doctype": "Country",
				"country_name": name,
				"code": country.code,
				"date_format": country.date_format or "dd-mm-yyyy",
				"time_format": country.time_format or "HH:mm:ss",
				"time_zones": "\n".join(country.timezones or []),
				"docstatus": 0,
			}
		).db_insert()

	if country.currency and not sparrow.db.exists("Currency", country.currency):
		sparrow.get_doc(
			{
				"doctype": "Currency",
				"currency_name": country.currency,
				"fraction": country.currency_fraction,
				"symbol": country.currency_symbol,
				"fraction_units": country.currency_fraction_units,
				"smallest_currency_fraction_value": country.smallest_currency_fraction_value,
				"number_format": country.number_format,
				"docstatus": 0,
			}
		).db_insert()


def add_standard_navbar_items():
	navbar_settings = sparrow.get_single("Navbar Settings")

	# don't add settings/help options if they're already present
	if navbar_settings.settings_dropdown and navbar_settings.help_dropdown:
		return

	standard_navbar_items = [
		{
			"item_label": "My Profile",
			"item_type": "Route",
			"route": "/app/user-profile",
			"is_standard": 1,
		},
		{
			"item_label": "My Settings",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.route_to_user()",
			"is_standard": 1,
		},
		{
			"item_label": "Session Defaults",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.setup_session_defaults()",
			"is_standard": 1,
		},
		{
			"item_label": "Reload",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.clear_cache()",
			"is_standard": 1,
		},
		{
			"item_label": "View Website",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.view_website()",
			"is_standard": 1,
		},
		{
			"item_label": "Toggle Full Width",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.toggle_full_width()",
			"is_standard": 1,
		},
		{
			"item_label": "Toggle Theme",
			"item_type": "Action",
			"action": "new sparrow.ui.ThemeSwitcher().show()",
			"is_standard": 1,
		},
		{
			"item_type": "Separator",
			"is_standard": 1,
			"item_label": "",
		},
		{
			"item_label": "Log out",
			"item_type": "Action",
			"action": "sparrow.app.logout()",
			"is_standard": 1,
		},
	]

	standard_help_items = [
		{
			"item_label": "About",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.show_about()",
			"is_standard": 1,
		},
		{
			"item_label": "Keyboard Shortcuts",
			"item_type": "Action",
			"action": "sparrow.ui.toolbar.show_shortcuts(event)",
			"is_standard": 1,
		},
		{
			"item_label": "Sparrow Support",
			"item_type": "Route",
			"route": "https://sparrow.io/support",
			"is_standard": 1,
		},
	]

	navbar_settings.settings_dropdown = []
	navbar_settings.help_dropdown = []

	for item in standard_navbar_items:
		navbar_settings.append("settings_dropdown", item)

	for item in standard_help_items:
		navbar_settings.append("help_dropdown", item)

	navbar_settings.save()
