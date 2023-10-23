# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json
from datetime import datetime

import click
from croniter import croniter

import sparrow
from sparrow.model.document import Document
from sparrow.utils import get_datetime, now_datetime
from sparrow.utils.background_jobs import enqueue, is_job_enqueued


class ScheduledJobType(Document):
	def autoname(self):
		self.name = ".".join(self.method.split(".")[-2:])

	def validate(self):
		if self.frequency != "All":
			# force logging for all events other than continuous ones (ALL)
			self.create_log = 1

	def enqueue(self, force=False):
		# enqueue event if last execution is done
		if self.is_event_due() or force:
			if sparrow.flags.enqueued_jobs:
				sparrow.flags.enqueued_jobs.append(self.method)

			if sparrow.flags.execute_job:
				self.execute()
			else:
				if not self.is_job_in_queue():
					enqueue(
						"sparrow.core.doctype.scheduled_job_type.scheduled_job_type.run_scheduled_job",
						queue=self.get_queue_name(),
						job_type=self.method,
						job_id=self.rq_job_id,
					)
					return True
				else:
					sparrow.logger("scheduler").error(
						f"Skipped queueing {self.method} because it was found in queue for {sparrow.local.site}"
					)
		return False

	def is_event_due(self, current_time=None):
		"""Return true if event is due based on time lapsed since last execution"""
		# if the next scheduled event is before NOW, then its due!
		return self.get_next_execution() <= (current_time or now_datetime())

	def is_job_in_queue(self) -> bool:
		return is_job_enqueued(self.rq_job_id)

	@property
	def rq_job_id(self):
		"""Unique ID created to deduplicate jobs with single RQ call."""
		return f"scheduled_job::{self.method}"

	@property
	def next_execution(self):
		return self.get_next_execution()

	def get_next_execution(self):
		CRON_MAP = {
			"Yearly": "0 0 1 1 *",
			"Annual": "0 0 1 1 *",
			"Monthly": "0 0 1 * *",
			"Monthly Long": "0 0 1 * *",
			"Weekly": "0 0 * * 0",
			"Weekly Long": "0 0 * * 0",
			"Daily": "0 0 * * *",
			"Daily Long": "0 0 * * *",
			"Hourly": "0 * * * *",
			"Hourly Long": "0 * * * *",
			"All": "0/" + str((sparrow.get_conf().scheduler_interval or 240) // 60) + " * * * *",
		}

		if not self.cron_format:
			self.cron_format = CRON_MAP[self.frequency]

		return croniter(
			self.cron_format, get_datetime(self.last_execution or datetime(2000, 1, 1))
		).get_next(datetime)

	def execute(self):
		self.scheduler_log = None
		try:
			self.log_status("Start")
			if self.server_script:
				script_name = sparrow.db.get_value("Server Script", self.server_script)
				if script_name:
					sparrow.get_doc("Server Script", script_name).execute_scheduled_method()
			else:
				sparrow.get_attr(self.method)()
			sparrow.db.commit()
			self.log_status("Complete")
		except Exception:
			sparrow.db.rollback()
			self.log_status("Failed")

	def log_status(self, status):
		# log file
		sparrow.logger("scheduler").info(f"Scheduled Job {status}: {self.method} for {sparrow.local.site}")
		self.update_scheduler_log(status)

	def update_scheduler_log(self, status):
		if not self.create_log:
			# self.get_next_execution will work properly iff self.last_execution is properly set
			if self.frequency == "All" and status == "Start":
				self.db_set("last_execution", now_datetime(), update_modified=False)
				sparrow.db.commit()
			return
		if not self.scheduler_log:
			self.scheduler_log = sparrow.get_doc(
				dict(doctype="Scheduled Job Log", scheduled_job_type=self.name)
			).insert(ignore_permissions=True)
		self.scheduler_log.db_set("status", status)
		if status == "Failed":
			self.scheduler_log.db_set("details", sparrow.get_traceback())
		if status == "Start":
			self.db_set("last_execution", now_datetime(), update_modified=False)
		sparrow.db.commit()

	def get_queue_name(self):
		return "long" if ("Long" in self.frequency) else "default"

	def on_trash(self):
		sparrow.db.delete("Scheduled Job Log", {"scheduled_job_type": self.name})


@sparrow.whitelist()
def execute_event(doc: str):
	sparrow.only_for("System Manager")
	doc = json.loads(doc)
	sparrow.get_doc("Scheduled Job Type", doc.get("name")).enqueue(force=True)
	return doc


def run_scheduled_job(job_type: str):
	"""This is a wrapper function that runs a hooks.scheduler_events method"""
	try:
		sparrow.get_doc("Scheduled Job Type", dict(method=job_type)).execute()
	except Exception:
		print(sparrow.get_traceback())


def sync_jobs(hooks: dict = None):
	sparrow.reload_doc("core", "doctype", "scheduled_job_type")
	scheduler_events = hooks or sparrow.get_hooks("scheduler_events")
	all_events = insert_events(scheduler_events)
	clear_events(all_events)


def insert_events(scheduler_events: dict) -> list:
	cron_jobs, event_jobs = [], []
	for event_type in scheduler_events:
		events = scheduler_events.get(event_type)
		if isinstance(events, dict):
			cron_jobs += insert_cron_jobs(events)
		else:
			# hourly, daily etc
			event_jobs += insert_event_jobs(events, event_type)
	return cron_jobs + event_jobs


def insert_cron_jobs(events: dict) -> list:
	cron_jobs = []
	for cron_format in events:
		for event in events.get(cron_format):
			cron_jobs.append(event)
			insert_single_event("Cron", event, cron_format)
	return cron_jobs


def insert_event_jobs(events: list, event_type: str) -> list:
	event_jobs = []
	for event in events:
		event_jobs.append(event)
		frequency = event_type.replace("_", " ").title()
		insert_single_event(frequency, event)
	return event_jobs


def insert_single_event(frequency: str, event: str, cron_format: str = None):
	cron_expr = {"cron_format": cron_format} if cron_format else {}

	try:
		sparrow.get_attr(event)
	except Exception as e:
		click.secho(f"{event} is not a valid method: {e}", fg="yellow")

	doc = sparrow.get_doc(
		{
			"doctype": "Scheduled Job Type",
			"method": event,
			"cron_format": cron_format,
			"frequency": frequency,
		}
	)

	if not sparrow.db.exists(
		"Scheduled Job Type", {"method": event, "frequency": frequency, **cron_expr}
	):
		savepoint = "scheduled_job_type_creation"
		try:
			sparrow.db.savepoint(savepoint)
			doc.insert()
		except sparrow.DuplicateEntryError:
			sparrow.db.rollback(save_point=savepoint)
			doc.delete()
			doc.insert()


def clear_events(all_events: list):
	for event in sparrow.get_all("Scheduled Job Type", fields=["name", "method", "server_script"]):
		is_server_script = event.server_script
		is_defined_in_hooks = event.method in all_events

		if not (is_defined_in_hooks or is_server_script):
			sparrow.delete_doc("Scheduled Job Type", event.name)
