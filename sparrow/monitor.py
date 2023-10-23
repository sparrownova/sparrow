# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import json
import os
import traceback
import uuid
from datetime import datetime

import rq

import sparrow

MONITOR_REDIS_KEY = "monitor-transactions"
MONITOR_MAX_ENTRIES = 1000000


def start(transaction_type="request", method=None, kwargs=None):
	if sparrow.conf.monitor:
		sparrow.local.monitor = Monitor(transaction_type, method, kwargs)


def stop(response=None):
	if hasattr(sparrow.local, "monitor"):
		sparrow.local.monitor.dump(response)


def add_data_to_monitor(**kwargs) -> None:
	"""Add additional custom key-value pairs along with monitor log.
	Note: Key-value pairs should be simple JSON exportable types."""
	if hasattr(sparrow.local, "monitor"):
		sparrow.local.monitor.add_custom_data(**kwargs)


def log_file():
	return os.path.join(sparrow.utils.get_snova_path(), "logs", "monitor.json.log")


class Monitor:
	__slots__ = ("data",)

	def __init__(self, transaction_type, method, kwargs):
		try:
			self.data = sparrow._dict(
				{
					"site": sparrow.local.site,
					"timestamp": datetime.utcnow(),
					"transaction_type": transaction_type,
					"uuid": str(uuid.uuid4()),
				}
			)

			if transaction_type == "request":
				self.collect_request_meta()
			else:
				self.collect_job_meta(method, kwargs)
		except Exception:
			traceback.print_exc()

	def collect_request_meta(self):
		self.data.request = sparrow._dict(
			{
				"ip": sparrow.local.request_ip,
				"method": sparrow.request.method,
				"path": sparrow.request.path,
			}
		)

	def collect_job_meta(self, method, kwargs):
		self.data.job = sparrow._dict({"method": method, "scheduled": False, "wait": 0})
		if "run_scheduled_job" in method:
			self.data.job.method = kwargs["job_type"]
			self.data.job.scheduled = True

		job = rq.get_current_job()
		if job:
			self.data.uuid = job.id
			waitdiff = self.data.timestamp - job.enqueued_at
			self.data.job.wait = int(waitdiff.total_seconds() * 1000000)

	def add_custom_data(self, **kwargs):
		if self.data:
			self.data.update(kwargs)

	def dump(self, response=None):
		try:
			timediff = datetime.utcnow() - self.data.timestamp
			# Obtain duration in microseconds
			self.data.duration = int(timediff.total_seconds() * 1000000)

			if self.data.transaction_type == "request":
				if response:
					self.data.request.status_code = response.status_code
					self.data.request.response_length = int(response.headers.get("Content-Length", 0))
				else:
					self.data.request.status_code = 500

				if hasattr(sparrow.local, "rate_limiter"):
					limiter = sparrow.local.rate_limiter
					self.data.request.counter = limiter.counter
					if limiter.rejected:
						self.data.request.reset = limiter.reset

			self.store()
		except Exception:
			traceback.print_exc()

	def store(self):
		if sparrow.cache().llen(MONITOR_REDIS_KEY) > MONITOR_MAX_ENTRIES:
			sparrow.cache().ltrim(MONITOR_REDIS_KEY, 1, -1)
		serialized = json.dumps(self.data, sort_keys=True, default=str, separators=(",", ":"))
		sparrow.cache().rpush(MONITOR_REDIS_KEY, serialized)


def flush():
	try:
		# Fetch all the logs without removing from cache
		logs = sparrow.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		if logs:
			logs = list(map(sparrow.safe_decode, logs))
			with open(log_file(), "a", os.O_NONBLOCK) as f:
				f.write("\n".join(logs))
				f.write("\n")
			# Remove fetched entries from cache
			sparrow.cache().ltrim(MONITOR_REDIS_KEY, len(logs) - 1, -1)
	except Exception:
		traceback.print_exc()
