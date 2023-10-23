# Copyright (c) 2022, Sparrow Technologies and Contributors
# See license.txt

import sparrow
from sparrow.core.doctype.rq_worker.rq_worker import RQWorker
from sparrow.tests.utils import FrappeTestCase


class TestRQWorker(FrappeTestCase):
	def test_get_worker_list(self):
		workers = RQWorker.get_list({})
		self.assertGreaterEqual(len(workers), 1)
		self.assertTrue(any("short" in w.queue_type for w in workers))

	def test_worker_serialization(self):
		workers = RQWorker.get_list({})
		sparrow.get_doc("RQ Worker", workers[0].pid)
