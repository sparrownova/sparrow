import os
import time
from unittest import TestCase
from unittest.mock import patch

import sparrow
from sparrow.core.doctype.scheduled_job_type.scheduled_job_type import ScheduledJobType, sync_jobs
from sparrow.utils import add_days, get_datetime
from sparrow.utils.doctor import purge_pending_jobs
from sparrow.utils.scheduler import (
	_get_last_modified_timestamp,
	enqueue_events,
	is_dormant,
	schedule_jobs_based_on_activity,
)


def test_timeout_10():
	time.sleep(10)


def test_method():
	pass


class TestScheduler(TestCase):
	def setUp(self):
		sparrow.db.rollback()

		if not os.environ.get("CI"):
			return

		purge_pending_jobs()
		if not sparrow.get_all("Scheduled Job Type", limit=1):
			sync_jobs()

	def test_enqueue_jobs(self):
		sparrow.db.sql("update `tabScheduled Job Type` set last_execution = '2010-01-01 00:00:00'")

		sparrow.flags.execute_job = True
		enqueue_events(site=sparrow.local.site)
		sparrow.flags.execute_job = False

		self.assertTrue("sparrow.email.queue.set_expiry_for_email_queue", sparrow.flags.enqueued_jobs)
		self.assertTrue("sparrow.utils.change_log.check_for_update", sparrow.flags.enqueued_jobs)
		self.assertTrue(
			"sparrow.email.doctype.auto_email_report.auto_email_report.send_monthly",
			sparrow.flags.enqueued_jobs,
		)

	def test_queue_peeking(self):
		job = get_test_job()

		with patch.object(job, "is_job_in_queue", return_value=True):
			# 1st job is in the queue (or running), don't enqueue it again
			self.assertFalse(job.enqueue())

	def test_is_dormant(self):
		self.assertTrue(is_dormant(check_time=get_datetime("2100-01-01 00:00:00")))
		self.assertTrue(is_dormant(check_time=add_days(sparrow.db.get_last_created("Activity Log"), 5)))
		self.assertFalse(is_dormant(check_time=sparrow.db.get_last_created("Activity Log")))

	def test_once_a_day_for_dormant(self):
		sparrow.db.truncate("Scheduled Job Log")
		self.assertTrue(schedule_jobs_based_on_activity(check_time=get_datetime("2100-01-01 00:00:00")))
		self.assertTrue(
			schedule_jobs_based_on_activity(
				check_time=add_days(sparrow.db.get_last_created("Activity Log"), 5)
			)
		)

		# create a fake job executed 5 days from now
		job = get_test_job(method="sparrow.tests.test_scheduler.test_method", frequency="Daily")
		job.execute()
		job_log = sparrow.get_doc("Scheduled Job Log", dict(scheduled_job_type=job.name))
		job_log.db_set(
			"modified", add_days(_get_last_modified_timestamp("Activity Log"), 5), update_modified=False
		)

		# inactive site with recent job, don't run
		self.assertFalse(
			schedule_jobs_based_on_activity(
				check_time=add_days(_get_last_modified_timestamp("Activity Log"), 5)
			)
		)

		# one more day has passed
		self.assertTrue(
			schedule_jobs_based_on_activity(
				check_time=add_days(_get_last_modified_timestamp("Activity Log"), 6)
			)
		)


def get_test_job(
	method="sparrow.tests.test_scheduler.test_timeout_10", frequency="All"
) -> ScheduledJobType:
	if not sparrow.db.exists("Scheduled Job Type", dict(method=method)):
		job = sparrow.get_doc(
			dict(
				doctype="Scheduled Job Type",
				method=method,
				last_execution="2010-01-01 00:00:00",
				frequency=frequency,
			)
		).insert()
	else:
		job = sparrow.get_doc("Scheduled Job Type", dict(method=method))
		job.db_set("last_execution", "2010-01-01 00:00:00")
		job.db_set("frequency", frequency)
	sparrow.db.commit()

	return job
