# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow.geo.country_info import get_country_info
from sparrow.translate import get_messages_for_boot, send_translations, set_default_language
from sparrow.utils import cint, strip
from sparrow.utils.password import update_password

from . import install_fixtures


def get_setup_stages(args):

	# App setup stage functions should not include sparrow.db.commit
	# That is done by sparrow after successful completion of all stages
	stages = [
		{
			"status": "Updating global settings",
			"fail_msg": "Failed to update global settings",
			"tasks": [
				{"fn": update_global_settings, "args": args, "fail_msg": "Failed to update global settings"}
			],
		}
	]

	stages += get_stages_hooks(args) + get_setup_complete_hooks(args)

	stages.append(
		{
			# post executing hooks
			"status": "Wrapping up",
			"fail_msg": "Failed to complete setup",
			"tasks": [
				{"fn": run_post_setup_complete, "args": args, "fail_msg": "Failed to complete setup"}
			],
		}
	)

	return stages


@sparrow.whitelist()
def setup_complete(args):
	"""Calls hooks for `setup_wizard_complete`, sets home page as `desktop`
	and clears cache. If wizard breaks, calls `setup_wizard_exception` hook"""

	# Setup complete: do not throw an exception, let the user continue to desk
	if cint(sparrow.db.get_single_value("System Settings", "setup_complete")):
		return {"status": "ok"}

	args = parse_args(args)
	stages = get_setup_stages(args)
	is_background_task = sparrow.conf.get("trigger_site_setup_in_background")

	if is_background_task:
		process_setup_stages.enqueue(stages=stages, user_input=args, is_background_task=True)
		return {"status": "registered"}
	else:
		return process_setup_stages(stages, args)


@sparrow.task()
def process_setup_stages(stages, user_input, is_background_task=False):
	from sparrow.utils.telemetry import capture

	capture("initated_server_side", "setup")
	try:
		sparrow.flags.in_setup_wizard = True
		current_task = None
		for idx, stage in enumerate(stages):
			sparrow.publish_realtime(
				"setup_task",
				{"progress": [idx, len(stages)], "stage_status": stage.get("status")},
				user=sparrow.session.user,
			)

			for task in stage.get("tasks"):
				current_task = task
				task.get("fn")(task.get("args"))
	except Exception:
		handle_setup_exception(user_input)
		if not is_background_task:
			return {"status": "fail", "fail": current_task.get("fail_msg")}
		sparrow.publish_realtime(
			"setup_task",
			{"status": "fail", "fail_msg": current_task.get("fail_msg")},
			user=sparrow.session.user,
		)
	else:
		run_setup_success(user_input)
		capture("completed_server_side", "setup")
		if not is_background_task:
			return {"status": "ok"}
		sparrow.publish_realtime("setup_task", {"status": "ok"}, user=sparrow.session.user)
	finally:
		sparrow.flags.in_setup_wizard = False


def update_global_settings(args):
	if args.language and args.language != "English":
		set_default_language(get_language_code(args.lang))
		sparrow.db.commit()
	sparrow.clear_cache()

	update_system_settings(args)
	update_user_name(args)


def run_post_setup_complete(args):
	disable_future_access()
	sparrow.db.commit()
	sparrow.clear_cache()


def run_setup_success(args):
	for hook in sparrow.get_hooks("setup_wizard_success"):
		sparrow.get_attr(hook)(args)
	install_fixtures.install()


def get_stages_hooks(args):
	stages = []
	for method in sparrow.get_hooks("setup_wizard_stages"):
		stages += sparrow.get_attr(method)(args)
	return stages


def get_setup_complete_hooks(args):
	stages = []
	for method in sparrow.get_hooks("setup_wizard_complete"):
		stages.append(
			{
				"status": "Executing method",
				"fail_msg": "Failed to execute method",
				"tasks": [
					{"fn": sparrow.get_attr(method), "args": args, "fail_msg": "Failed to execute method"}
				],
			}
		)
	return stages


def handle_setup_exception(args):
	sparrow.db.rollback()
	if args:
		traceback = sparrow.get_traceback()
		print(traceback)
		for hook in sparrow.get_hooks("setup_wizard_exception"):
			sparrow.get_attr(hook)(traceback, args)


def update_system_settings(args):
	number_format = get_country_info(args.get("country")).get("number_format", "#,###.##")

	# replace these as float number formats, as they have 0 precision
	# and are currency number formats and not for floats
	if number_format == "#.###":
		number_format = "#.###,##"
	elif number_format == "#,###":
		number_format = "#,###.##"

	system_settings = sparrow.get_doc("System Settings", "System Settings")
	system_settings.update(
		{
			"country": args.get("country"),
			"language": get_language_code(args.get("language")) or "en",
			"time_zone": args.get("timezone"),
			"float_precision": 3,
			"date_format": sparrow.db.get_value("Country", args.get("country"), "date_format"),
			"time_format": sparrow.db.get_value("Country", args.get("country"), "time_format"),
			"number_format": number_format,
			"enable_scheduler": 1 if not sparrow.flags.in_test else 0,
			"backup_limit": 3,  # Default for downloadable backups
			"enable_telemetry": cint(args.get("enable_telemetry")),
		}
	)
	system_settings.save()


def update_user_name(args):
	first_name, last_name = args.get("full_name", ""), ""
	if " " in first_name:
		first_name, last_name = first_name.split(" ", 1)

	if args.get("email"):
		if sparrow.db.exists("User", args.get("email")):
			# running again
			return

		args["name"] = args.get("email")

		_mute_emails, sparrow.flags.mute_emails = sparrow.flags.mute_emails, True
		doc = sparrow.get_doc(
			{
				"doctype": "User",
				"email": args.get("email"),
				"first_name": first_name,
				"last_name": last_name,
			}
		)
		doc.flags.no_welcome_mail = True
		doc.insert()
		sparrow.flags.mute_emails = _mute_emails
		update_password(args.get("email"), args.get("password"))

	elif first_name:
		args.update({"name": sparrow.session.user, "first_name": first_name, "last_name": last_name})

		sparrow.db.sql(
			"""update `tabUser` SET first_name=%(first_name)s,
			last_name=%(last_name)s WHERE name=%(name)s""",
			args,
		)

	if args.get("attach_user"):
		attach_user = args.get("attach_user").split(",")
		if len(attach_user) == 3:
			filename, filetype, content = attach_user
			_file = sparrow.get_doc(
				{
					"doctype": "File",
					"file_name": filename,
					"attached_to_doctype": "User",
					"attached_to_name": args.get("name"),
					"content": content,
					"decode": True,
				}
			)
			_file.save()
			fileurl = _file.file_url
			sparrow.db.set_value("User", args.get("name"), "user_image", fileurl)

	if args.get("name"):
		add_all_roles_to(args.get("name"))


def parse_args(args):
	if not args:
		args = sparrow.local.form_dict
	if isinstance(args, str):
		args = json.loads(args)

	args = sparrow._dict(args)

	# strip the whitespace
	for key, value in args.items():
		if isinstance(value, str):
			args[key] = strip(value)

	return args


def add_all_roles_to(name):
	user = sparrow.get_doc("User", name)
	for role in sparrow.db.sql("""select name from tabRole"""):
		if role[0] not in [
			"Administrator",
			"Guest",
			"All",
			"Customer",
			"Supplier",
			"Partner",
			"Employee",
		]:
			d = user.append("roles")
			d.role = role[0]
	user.save()


def disable_future_access():
	sparrow.db.set_default("desktop:home_page", "workspace")
	sparrow.db.set_single_value("System Settings", "setup_complete", 1)

	# Enable onboarding after install
	sparrow.db.set_single_value("System Settings", "enable_onboarding", 1)

	if not sparrow.flags.in_test:
		# remove all roles and add 'Administrator' to prevent future access
		page = sparrow.get_doc("Page", "setup-wizard")
		page.roles = []
		page.append("roles", {"role": "Administrator"})
		page.flags.do_not_update_json = True
		page.flags.ignore_permissions = True
		page.save()


@sparrow.whitelist()
def load_messages(language):
	"""Load translation messages for given language from all `setup_wizard_requires`
	javascript files"""
	sparrow.clear_cache()
	set_default_language(get_language_code(language))
	sparrow.db.commit()
	send_translations(get_messages_for_boot())
	return sparrow.local.lang


@sparrow.whitelist()
def load_languages():
	language_codes = sparrow.db.sql(
		"select language_code, language_name from tabLanguage order by name", as_dict=True
	)
	codes_to_names = {}
	for d in language_codes:
		codes_to_names[d.language_code] = d.language_name
	return {
		"default_language": sparrow.db.get_value("Language", sparrow.local.lang, "language_name")
                            or sparrow.local.lang,
		"languages": sorted(sparrow.db.sql_list("select language_name from tabLanguage order by name")),
		"codes_to_names": codes_to_names,
	}


@sparrow.whitelist()
def load_country():
	from sparrow.sessions import get_geo_ip_country

	return get_geo_ip_country(sparrow.local.request_ip) if sparrow.local.request_ip else None


@sparrow.whitelist()
def load_user_details():
	return {
		"full_name": sparrow.cache().hget("full_name", "signup"),
		"email": sparrow.cache().hget("email", "signup"),
	}


def prettify_args(args):
	# remove attachments
	for key, val in args.items():
		if isinstance(val, str) and "data:image" in val:
			filename = val.split("data:image", 1)[0].strip(", ")
			size = round((len(val) * 3 / 4) / 1048576.0, 2)
			args[key] = f"Image Attached: '{filename}' of size {size} MB"

	pretty_args = []
	for key in sorted(args):
		pretty_args.append(f"{key} = {args[key]}")
	return pretty_args


def email_setup_wizard_exception(traceback, args):
	if not sparrow.conf.setup_wizard_exception_email:
		return

	pretty_args = prettify_args(args)
	message = """

#### Traceback

<pre>{traceback}</pre>

---

#### Setup Wizard Arguments

<pre>{args}</pre>

---

#### Request Headers

<pre>{headers}</pre>

---

#### Basic Information

- **Site:** {site}
- **User:** {user}""".format(
		site=sparrow.local.site,
		traceback=traceback,
		args="\n".join(pretty_args),
		user=sparrow.session.user,
		headers=sparrow.request.headers if sparrow.request else "[no request]",
	)

	sparrow.sendmail(
		recipients=sparrow.conf.setup_wizard_exception_email,
		sender=sparrow.session.user,
		subject=f"Setup failed: {sparrow.local.site}",
		message=message,
		delayed=False,
	)


def log_setup_wizard_exception(traceback, args):
	with open("../logs/setup-wizard.log", "w+") as setup_log:
		setup_log.write(traceback)
		setup_log.write(json.dumps(args))


def get_language_code(lang):
	return sparrow.db.get_value("Language", {"language_name": lang})


def enable_twofactor_all_roles():
	all_role = sparrow.get_doc("Role", {"role_name": "All"})
	all_role.two_factor_auth = True
	all_role.save(ignore_permissions=True)


def make_records(records, debug=False):
	from sparrow import _dict
	from sparrow.modules import scrub

	if debug:
		print("make_records: in DEBUG mode")

	# LOG every success and failure
	for record in records:
		doctype = record.get("doctype")
		condition = record.get("__condition")

		if condition and not condition():
			continue

		doc = sparrow.new_doc(doctype)
		doc.update(record)

		# ignore mandatory for root
		parent_link_field = "parent_" + scrub(doc.doctype)
		if doc.meta.get_field(parent_link_field) and not doc.get(parent_link_field):
			doc.flags.ignore_mandatory = True

		savepoint = "setup_fixtures_creation"
		try:
			sparrow.db.savepoint(savepoint)
			doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
		except Exception as e:
			sparrow.clear_last_message()
			sparrow.db.rollback(save_point=savepoint)
			exception = record.get("__exception")
			if exception:
				config = _dict(exception)
				if isinstance(e, config.exception):
					config.handler()
				else:
					show_document_insert_error()
			else:
				show_document_insert_error()


def show_document_insert_error():
	print("Document Insert Error")
	print(sparrow.get_traceback())
	sparrow.log_error("Exception during Setup")
