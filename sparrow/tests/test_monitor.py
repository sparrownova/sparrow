# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
import sparrow.monitor
from sparrow.monitor import MONITOR_REDIS_KEY
from sparrow.tests.utils import sparrowTestCase
from sparrow.utils import set_request
from sparrow.utils.response import build_response


class TestMonitor(sparrowTestCase):
	def setUp(self):
		sparrow.conf.monitor = 1
		sparrow.cache().delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/sparrow.ping")
		response = build_response("json")

		sparrow.monitor.start()
		sparrow.monitor.stop(response)

		logs = sparrow.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = sparrow.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_no_response(self):
		set_request(method="GET", path="/api/method/sparrow.ping")

		sparrow.monitor.start()
		sparrow.monitor.stop(response=None)

		logs = sparrow.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = sparrow.parse_json(logs[0].decode())
		self.assertEqual(log.request["status_code"], 500)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		sparrow.utils.background_jobs.execute_job(
			sparrow.local.site, "sparrow.ping", None, None, {}, is_async=False
		)

		logs = sparrow.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = sparrow.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "sparrow.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/sparrow.ping")
		response = build_response("json")
		sparrow.monitor.start()
		sparrow.monitor.stop(response)

		open(sparrow.monitor.log_file(), "w").close()
		sparrow.monitor.flush()

		with open(sparrow.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = sparrow.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def tearDown(self):
		sparrow.conf.monitor = 0
		sparrow.cache().delete_value(MONITOR_REDIS_KEY)
