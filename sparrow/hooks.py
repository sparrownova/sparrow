from . import __version__ as app_version

app_name = "sparrow"
app_title = "Sparrow Framework"
app_publisher = "Sparrow Technologies"
app_description = "Full stack web framework with Python, Javascript, MariaDB, Redis, Node"
source_link = "https://github.com/sparrownova/sparrow"
app_license = "MIT"
app_logo_url = "/assets/sparrow/images/sparrow-framework-logo.svg"

develop_version = "14.x.x-develop"

app_email = "developers@sparrow.io"

docs_app = "sparrow_docs"

translator_url = "https://translate.shopper.com"

before_install = "sparrow.utils.install.before_install"
after_install = "sparrow.utils.install.after_install"

page_js = {"setup-wizard": "public/js/sparrow/setup_wizard.js"}

# website
app_include_js = [
	"libs.bundle.js",
	"desk.bundle.js",
	"list.bundle.js",
	"form.bundle.js",
	"controls.bundle.js",
	"report.bundle.js",
	"telemetry.bundle.js",
]
app_include_css = [
	"desk.bundle.css",
	"report.bundle.css",
]

doctype_js = {
	"Web Page": "public/js/sparrow/utils/web_template.js",
	"Website Settings": "public/js/sparrow/utils/web_template.js",
}

web_include_js = ["website_script.js"]

web_include_css = []

email_css = ["email.bundle.css"]

website_route_rules = [
	{"from_route": "/blog/<category>", "to_route": "Blog Post"},
	{"from_route": "/kb/<category>", "to_route": "Help Article"},
	{"from_route": "/newsletters", "to_route": "Newsletter"},
	{"from_route": "/profile", "to_route": "me"},
	{"from_route": "/app/<path:app_path>", "to_route": "app"},
]

website_redirects = [
	{"source": r"/desk(.*)", "target": r"/app\1"},
]

base_template = "templates/base.html"

write_file_keys = ["file_url", "file_name"]

notification_config = "sparrow.core.notifications.get_notification_config"

before_tests = "sparrow.utils.install.before_tests"

email_append_to = ["Event", "ToDo", "Communication"]

calendars = ["Event"]

leaderboards = "sparrow.desk.leaderboard.get_leaderboards"

# login

on_session_creation = [
	"sparrow.core.doctype.activity_log.feed.login_feed",
	"sparrow.core.doctype.user.user.notify_admin_access_to_system_manager",
]

on_logout = (
	"sparrow.core.doctype.session_default_settings.session_default_settings.clear_session_defaults"
)

# permissions

permission_query_conditions = {
	"Event": "sparrow.desk.doctype.event.event.get_permission_query_conditions",
	"ToDo": "sparrow.desk.doctype.todo.todo.get_permission_query_conditions",
	"User": "sparrow.core.doctype.user.user.get_permission_query_conditions",
	"Dashboard Settings": "sparrow.desk.doctype.dashboard_settings.dashboard_settings.get_permission_query_conditions",
	"Notification Log": "sparrow.desk.doctype.notification_log.notification_log.get_permission_query_conditions",
	"Dashboard": "sparrow.desk.doctype.dashboard.dashboard.get_permission_query_conditions",
	"Dashboard Chart": "sparrow.desk.doctype.dashboard_chart.dashboard_chart.get_permission_query_conditions",
	"Number Card": "sparrow.desk.doctype.number_card.number_card.get_permission_query_conditions",
	"Notification Settings": "sparrow.desk.doctype.notification_settings.notification_settings.get_permission_query_conditions",
	"Note": "sparrow.desk.doctype.note.note.get_permission_query_conditions",
	"Kanban Board": "sparrow.desk.doctype.kanban_board.kanban_board.get_permission_query_conditions",
	"Contact": "sparrow.contacts.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "sparrow.contacts.address_and_contact.get_permission_query_conditions_for_address",
	"Communication": "sparrow.core.doctype.communication.communication.get_permission_query_conditions_for_communication",
	"Workflow Action": "sparrow.workflow.doctype.workflow_action.workflow_action.get_permission_query_conditions",
	"Prepared Report": "sparrow.core.doctype.prepared_report.prepared_report.get_permission_query_condition",
	"File": "sparrow.core.doctype.file.file.get_permission_query_conditions",
}

has_permission = {
	"Event": "sparrow.desk.doctype.event.event.has_permission",
	"ToDo": "sparrow.desk.doctype.todo.todo.has_permission",
	"User": "sparrow.core.doctype.user.user.has_permission",
	"Note": "sparrow.desk.doctype.note.note.has_permission",
	"Dashboard Chart": "sparrow.desk.doctype.dashboard_chart.dashboard_chart.has_permission",
	"Number Card": "sparrow.desk.doctype.number_card.number_card.has_permission",
	"Kanban Board": "sparrow.desk.doctype.kanban_board.kanban_board.has_permission",
	"Contact": "sparrow.contacts.address_and_contact.has_permission",
	"Address": "sparrow.contacts.address_and_contact.has_permission",
	"Communication": "sparrow.core.doctype.communication.communication.has_permission",
	"Workflow Action": "sparrow.workflow.doctype.workflow_action.workflow_action.has_permission",
	"File": "sparrow.core.doctype.file.file.has_permission",
	"Prepared Report": "sparrow.core.doctype.prepared_report.prepared_report.has_permission",
}

has_website_permission = {
	"Address": "sparrow.contacts.doctype.address.address.has_website_permission"
}

jinja = {
	"methods": "sparrow.utils.jinja_globals",
	"filters": [
		"sparrow.utils.data.global_date_format",
		"sparrow.utils.markdown",
		"sparrow.website.utils.get_shade",
		"sparrow.website.utils.abs_url",
	],
}

standard_queries = {"User": "sparrow.core.doctype.user.user.user_query"}

doc_events = {
	"*": {
		"after_insert": [
			"sparrow.event_streaming.doctype.event_update_log.event_update_log.notify_consumers"
		],
		"on_update": [
			"sparrow.desk.notifications.clear_doctype_notifications",
			"sparrow.core.doctype.activity_log.feed.update_feed",
			"sparrow.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"sparrow.core.doctype.file.utils.attach_files_to_document",
			"sparrow.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
			"sparrow.automation.doctype.assignment_rule.assignment_rule.apply",
			"sparrow.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"sparrow.core.doctype.user_type.user_type.apply_permissions_for_non_standard_user_type",
		],
		"after_rename": "sparrow.desk.notifications.clear_doctype_notifications",
		"on_cancel": [
			"sparrow.desk.notifications.clear_doctype_notifications",
			"sparrow.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"sparrow.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
			"sparrow.automation.doctype.assignment_rule.assignment_rule.apply",
		],
		"on_trash": [
			"sparrow.desk.notifications.clear_doctype_notifications",
			"sparrow.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"sparrow.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
		],
		"on_update_after_submit": [
			"sparrow.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"sparrow.automation.doctype.assignment_rule.assignment_rule.apply",
			"sparrow.automation.doctype.assignment_rule.assignment_rule.update_due_date",
		],
		"on_change": [
			"sparrow.social.doctype.energy_point_rule.energy_point_rule.process_energy_points",
			"sparrow.automation.doctype.milestone_tracker.milestone_tracker.evaluate_milestone",
		],
	},
	"Event": {
		"after_insert": "sparrow.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar",
		"on_update": "sparrow.integrations.doctype.google_calendar.google_calendar.update_event_in_google_calendar",
		"on_trash": "sparrow.integrations.doctype.google_calendar.google_calendar.delete_event_from_google_calendar",
	},
	"Contact": {
		"after_insert": "sparrow.integrations.doctype.google_contacts.google_contacts.insert_contacts_to_google_contacts",
		"on_update": "sparrow.integrations.doctype.google_contacts.google_contacts.update_contacts_to_google_contacts",
	},
	"DocType": {
		"on_update": "sparrow.cache_manager.build_domain_restriced_doctype_cache",
	},
	"Page": {
		"on_update": "sparrow.cache_manager.build_domain_restriced_page_cache",
	},
}

scheduler_events = {
	"cron": {
		"0/15 * * * *": [
			"sparrow.oauth.delete_oauth2_data",
			"sparrow.website.doctype.web_page.web_page.check_publish_status",
			"sparrow.twofactor.delete_all_barcodes_for_users",
		],
		"0/10 * * * *": [
			"sparrow.email.doctype.email_account.email_account.pull",
		],
		# Hourly but offset by 30 minutes
		# "30 * * * *": [
		#
		# ],
		# Daily but offset by 45 minutes
		"45 0 * * *": [
			"sparrow.core.doctype.log_settings.log_settings.run_log_clean_up",
		],
	},
	"all": [
		"sparrow.email.queue.flush",
		"sparrow.email.doctype.email_account.email_account.notify_unreplied",
		"sparrow.utils.global_search.sync_global_search",
		"sparrow.monitor.flush",
	],
	"hourly": [
		"sparrow.model.utils.link_count.update_link_count",
		"sparrow.model.utils.user_settings.sync_user_settings",
		"sparrow.utils.error.collect_error_snapshots",
		"sparrow.desk.page.backups.backups.delete_downloadable_backups",
		"sparrow.deferred_insert.save_to_db",
		"sparrow.desk.form.document_follow.send_hourly_updates",
		"sparrow.integrations.doctype.google_calendar.google_calendar.sync",
		"sparrow.email.doctype.newsletter.newsletter.send_scheduled_email",
		"sparrow.website.doctype.personal_data_deletion_request.personal_data_deletion_request.process_data_deletion_request",
	],
	"daily": [
		"sparrow.email.queue.set_expiry_for_email_queue",
		"sparrow.desk.notifications.clear_notifications",
		"sparrow.desk.doctype.event.event.send_event_digest",
		"sparrow.sessions.clear_expired_sessions",
		"sparrow.email.doctype.notification.notification.trigger_daily_alerts",
		"sparrow.website.doctype.personal_data_deletion_request.personal_data_deletion_request.remove_unverified_record",
		"sparrow.desk.form.document_follow.send_daily_updates",
		"sparrow.social.doctype.energy_point_settings.energy_point_settings.allocate_review_points",
		"sparrow.integrations.doctype.google_contacts.google_contacts.sync",
		"sparrow.automation.doctype.auto_repeat.auto_repeat.make_auto_repeat_entry",
		"sparrow.automation.doctype.auto_repeat.auto_repeat.set_auto_repeat_as_completed",
		"sparrow.email.doctype.unhandled_email.unhandled_email.remove_old_unhandled_emails",
	],
	"daily_long": [
		"sparrow.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_daily",
		"sparrow.utils.change_log.check_for_update",
		"sparrow.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_daily",
		"sparrow.email.doctype.auto_email_report.auto_email_report.send_daily",
		"sparrow.integrations.doctype.google_drive.google_drive.daily_backup",
	],
	"weekly_long": [
		"sparrow.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_weekly",
		"sparrow.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_weekly",
		"sparrow.desk.form.document_follow.send_weekly_updates",
		"sparrow.social.doctype.energy_point_log.energy_point_log.send_weekly_summary",
		"sparrow.integrations.doctype.google_drive.google_drive.weekly_backup",
	],
	"monthly": [
		"sparrow.email.doctype.auto_email_report.auto_email_report.send_monthly",
		"sparrow.social.doctype.energy_point_log.energy_point_log.send_monthly_summary",
	],
	"monthly_long": [
		"sparrow.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_monthly"
	],
}

get_translated_dict = {
	("doctype", "System Settings"): "sparrow.geo.country_info.get_translated_dict",
	("page", "setup-wizard"): "sparrow.geo.country_info.get_translated_dict",
}

sounds = [
	{"name": "email", "src": "/assets/sparrow/sounds/email.mp3", "volume": 0.1},
	{"name": "submit", "src": "/assets/sparrow/sounds/submit.mp3", "volume": 0.1},
	{"name": "cancel", "src": "/assets/sparrow/sounds/cancel.mp3", "volume": 0.1},
	{"name": "delete", "src": "/assets/sparrow/sounds/delete.mp3", "volume": 0.05},
	{"name": "click", "src": "/assets/sparrow/sounds/click.mp3", "volume": 0.05},
	{"name": "error", "src": "/assets/sparrow/sounds/error.mp3", "volume": 0.1},
	{"name": "alert", "src": "/assets/sparrow/sounds/alert.mp3", "volume": 0.2},
	# {"name": "chime", "src": "/assets/sparrow/sounds/chime.mp3"},
]

setup_wizard_exception = [
	"sparrow.desk.page.setup_wizard.setup_wizard.email_setup_wizard_exception",
	"sparrow.desk.page.setup_wizard.setup_wizard.log_setup_wizard_exception",
]

before_migrate = []
after_migrate = ["sparrow.website.doctype.website_theme.website_theme.after_migrate"]

otp_methods = ["OTP App", "Email", "SMS"]

user_data_fields = [
	{"doctype": "Access Log", "strict": True},
	{"doctype": "Activity Log", "strict": True},
	{"doctype": "Comment", "strict": True},
	{
		"doctype": "Contact",
		"filter_by": "email_id",
		"redact_fields": ["first_name", "last_name", "phone", "mobile_no"],
		"rename": True,
	},
	{"doctype": "Contact Email", "filter_by": "email_id"},
	{
		"doctype": "Address",
		"filter_by": "email_id",
		"redact_fields": [
			"address_title",
			"address_line1",
			"address_line2",
			"city",
			"county",
			"state",
			"pincode",
			"phone",
			"fax",
		],
	},
	{
		"doctype": "Communication",
		"filter_by": "sender",
		"redact_fields": ["sender_full_name", "phone_no", "content"],
	},
	{"doctype": "Communication", "filter_by": "recipients"},
	{"doctype": "Email Group Member", "filter_by": "email"},
	{"doctype": "Email Unsubscribe", "filter_by": "email", "partial": True},
	{"doctype": "Email Queue", "filter_by": "sender"},
	{"doctype": "Email Queue Recipient", "filter_by": "recipient"},
	{
		"doctype": "File",
		"filter_by": "attached_to_name",
		"redact_fields": ["file_name", "file_url"],
	},
	{
		"doctype": "User",
		"filter_by": "name",
		"redact_fields": [
			"email",
			"username",
			"first_name",
			"middle_name",
			"last_name",
			"full_name",
			"birth_date",
			"user_image",
			"phone",
			"mobile_no",
			"location",
			"banner_image",
			"interest",
			"bio",
			"email_signature",
		],
	},
	{"doctype": "Version", "strict": True},
]

global_search_doctypes = {
	"Default": [
		{"doctype": "Contact"},
		{"doctype": "Address"},
		{"doctype": "ToDo"},
		{"doctype": "Note"},
		{"doctype": "Event"},
		{"doctype": "Blog Post"},
		{"doctype": "Dashboard"},
		{"doctype": "Country"},
		{"doctype": "Currency"},
		{"doctype": "Newsletter"},
		{"doctype": "Letter Head"},
		{"doctype": "Workflow"},
		{"doctype": "Web Page"},
		{"doctype": "Web Form"},
	]
}

override_whitelisted_methods = {
	# Legacy File APIs
	"sparrow.core.doctype.file.file.download_file": "download_file",
	"sparrow.core.doctype.file.file.unzip_file": "sparrow.core.api.file.unzip_file",
	"sparrow.core.doctype.file.file.get_attached_images": "sparrow.core.api.file.get_attached_images",
	"sparrow.core.doctype.file.file.get_files_in_folder": "sparrow.core.api.file.get_files_in_folder",
	"sparrow.core.doctype.file.file.get_files_by_search_text": "sparrow.core.api.file.get_files_by_search_text",
	"sparrow.core.doctype.file.file.get_max_file_size": "sparrow.core.api.file.get_max_file_size",
	"sparrow.core.doctype.file.file.create_new_folder": "sparrow.core.api.file.create_new_folder",
	"sparrow.core.doctype.file.file.move_file": "sparrow.core.api.file.move_file",
	"sparrow.core.doctype.file.file.zip_files": "sparrow.core.api.file.zip_files",
	# Legacy (& Consistency) OAuth2 APIs
	"sparrow.www.login.login_via_google": "sparrow.integrations.oauth2_logins.login_via_google",
	"sparrow.www.login.login_via_github": "sparrow.integrations.oauth2_logins.login_via_github",
	"sparrow.www.login.login_via_facebook": "sparrow.integrations.oauth2_logins.login_via_facebook",
	"sparrow.www.login.login_via_sparrow": "sparrow.integrations.oauth2_logins.login_via_sparrow",
	"sparrow.www.login.login_via_office365": "sparrow.integrations.oauth2_logins.login_via_office365",
	"sparrow.www.login.login_via_salesforce": "sparrow.integrations.oauth2_logins.login_via_salesforce",
	"sparrow.www.login.login_via_fairlogin": "sparrow.integrations.oauth2_logins.login_via_fairlogin",
}

ignore_links_on_delete = [
	"Communication",
	"ToDo",
	"DocShare",
	"Email Unsubscribe",
	"Activity Log",
	"File",
	"Version",
	"Document Follow",
	"Comment",
	"View Log",
	"Tag Link",
	"Notification Log",
	"Email Queue",
	"Document Share Key",
	"Integration Request",
	"Unhandled Email",
	"Webhook Request Log",
]

# Request Hooks
before_request = [
	"sparrow.recorder.record",
	"sparrow.monitor.start",
	"sparrow.rate_limiter.apply",
]
after_request = ["sparrow.rate_limiter.update", "sparrow.monitor.stop", "sparrow.recorder.dump"]

# Background Job Hooks
before_job = [
	"sparrow.monitor.start",
]
after_job = [
	"sparrow.monitor.stop",
	"sparrow.utils.file_lock.release_document_locks",
]

extend_bootinfo = [
	"sparrow.utils.telemetry.add_bootinfo",
	"sparrow.core.doctype.user_permission.user_permission.send_user_permissions",
]
