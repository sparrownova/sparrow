# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
"""
Events:
	always
	daily
	monthly
	weekly
"""

# imports - standard imports
import os
import random
import time

# imports - module imports
import sparrow
from sparrow.utils import cint, get_datetime, get_sites, now_datetime
from sparrow.utils.background_jobs import get_jobs, set_niceness

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def cprint(*args, **kwargs):
	"""Prints only if called from STDOUT"""
	try:
		os.get_terminal_size()
		print(*args, **kwargs)
	except Exception:
		pass


def start_scheduler():
	"""Run enqueue_events_for_all_sites based on scheduler tick.
	Specify scheduler_interval in seconds in common_site_config.json"""

	tick = cint(sparrow.get_conf().scheduler_tick_interval) or 60
	set_niceness()

	while True:
		time.sleep(tick)
		enqueue_events_for_all_sites()


def enqueue_events_for_all_sites():
	"""Loop through sites and enqueue events that are not already queued"""

	if os.path.exists(os.path.join(".", ".restarting")):
		# Don't add task to queue if webserver is in restart mode
		return

	with sparrow.init_site():
		sites = get_sites()

	# Sites are sorted in alphabetical order, shuffle to randomize priorities
	random.shuffle(sites)

	for site in sites:
		try:
			enqueue_events_for_site(site=site)
		except Exception as e:
			print(e.__class__, f"Failed to enqueue events for site: {site}")


def enqueue_events_for_site(site):
	def log_and_raise():
		error_message = "Exception in Enqueue Events for Site {}\n{}".format(
			site, sparrow.get_traceback()
		)
		sparrow.logger("scheduler").error(error_message)

	try:
		sparrow.init(site=site)
		sparrow.connect()
		if is_scheduler_inactive():
			return

		enqueue_events(site=site)

		sparrow.logger("scheduler").debug(f"Queued events for site {site}")
	except sparrow.db.OperationalError as e:
		if sparrow.db.is_access_denied(e):
			sparrow.logger("scheduler").debug(f"Access denied for site {site}")
		else:
			log_and_raise()
	except Exception:
		log_and_raise()

	finally:
		sparrow.destroy()


def enqueue_events(site):
	if schedule_jobs_based_on_activity():
		sparrow.flags.enqueued_jobs = []
		queued_jobs = get_jobs(site=site, key="job_type").get(site) or []
		for job_type in sparrow.get_all("Scheduled Job Type", ("name", "method"), dict(stopped=0)):
			if not job_type.method in queued_jobs:
				# don't add it to queue if still pending
				sparrow.get_doc("Scheduled Job Type", job_type.name).enqueue()


def is_scheduler_inactive(verbose=True) -> bool:
	if sparrow.local.conf.maintenance_mode:
		if verbose:
			cprint(f"{sparrow.local.site}: Maintenance mode is ON")
		return True

	if sparrow.local.conf.pause_scheduler:
		if verbose:
			cprint(f"{sparrow.local.site}: sparrow.conf.pause_scheduler is SET")
		return True

	if is_scheduler_disabled(verbose=verbose):
		return True

	return False


def is_scheduler_disabled(verbose=True) -> bool:
	if sparrow.conf.disable_scheduler:
		if verbose:
			cprint(f"{sparrow.local.site}: sparrow.conf.disable_scheduler is SET")
		return True

	scheduler_disabled = not sparrow.utils.cint(
		sparrow.db.get_single_value("System Settings", "enable_scheduler")
	)
	if scheduler_disabled:
		if verbose:
			cprint(f"{sparrow.local.site}: SystemSettings.enable_scheduler is UNSET")
	return scheduler_disabled


def toggle_scheduler(enable):
	sparrow.db.set_single_value("System Settings", "enable_scheduler", int(enable))


def enable_scheduler():
	toggle_scheduler(True)


def disable_scheduler():
	toggle_scheduler(False)


def schedule_jobs_based_on_activity(check_time=None):
	"""Returns True for active sites defined by Activity Log
	Returns True for inactive sites once in 24 hours"""
	if is_dormant(check_time=check_time):
		# ensure last job is one day old
		last_job_timestamp = _get_last_modified_timestamp("Scheduled Job Log")
		if not last_job_timestamp:
			return True
		else:
			if ((check_time or now_datetime()) - last_job_timestamp).total_seconds() >= 86400:
				# one day is passed since jobs are run, so lets do this
				return True
			else:
				# schedulers run in the last 24 hours, do nothing
				return False
	else:
		# site active, lets run the jobs
		return True


def is_dormant(check_time=None):
	last_activity_log_timestamp = _get_last_modified_timestamp("Activity Log")
	since = (sparrow.get_system_settings("dormant_days") or 4) * 86400
	if not last_activity_log_timestamp:
		return True
	if ((check_time or now_datetime()) - last_activity_log_timestamp).total_seconds() >= since:
		return True
	return False


def _get_last_modified_timestamp(doctype):
	timestamp = sparrow.db.get_value(
		doctype, filters={}, fieldname="modified", order_by="modified desc"
	)
	if timestamp:
		return get_datetime(timestamp)


@sparrow.whitelist()
def activate_scheduler():
	from sparrow.installer import update_site_config

	sparrow.only_for("Administrator")

	if sparrow.local.conf.maintenance_mode:
		sparrow.throw(sparrow._("Scheduler can not be re-enabled when maintenance mode is active."))

	if is_scheduler_disabled():
		enable_scheduler()
	if sparrow.conf.pause_scheduler:
		update_site_config("pause_scheduler", 0)


@sparrow.whitelist()
def get_scheduler_status():
	if is_scheduler_inactive():
		return {"status": "inactive"}
	return {"status": "active"}
