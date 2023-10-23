# Copyright (c) 2019, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sqlparse

import sparrow
import sparrow.recorder
from sparrow.recorder import normalize_query
from sparrow.tests.utils import SparrowTestCase
from sparrow.utils import set_request
from sparrow.website.serve import get_response_content


class TestRecorder(SparrowTestCase):
	def setUp(self):
		sparrow.recorder.stop()
		sparrow.recorder.delete()
		set_request()
		sparrow.recorder.start()
		sparrow.recorder.record()

	def test_start(self):
		sparrow.recorder.dump()
		requests = sparrow.recorder.get()
		self.assertEqual(len(requests), 1)

	def test_do_not_record(self):
		sparrow.recorder.do_not_record(sparrow.get_all)("DocType")
		sparrow.recorder.dump()
		requests = sparrow.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_get(self):
		sparrow.recorder.dump()

		requests = sparrow.recorder.get()
		self.assertEqual(len(requests), 1)

		request = sparrow.recorder.get(requests[0]["uuid"])
		self.assertTrue(request)

	def test_delete(self):
		sparrow.recorder.dump()

		requests = sparrow.recorder.get()
		self.assertEqual(len(requests), 1)

		sparrow.recorder.delete()

		requests = sparrow.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_record_without_sql_queries(self):
		sparrow.recorder.dump()

		requests = sparrow.recorder.get()
		request = sparrow.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), 0)

	def test_record_with_sql_queries(self):
		sparrow.get_all("DocType")
		sparrow.recorder.dump()

		requests = sparrow.recorder.get()
		request = sparrow.recorder.get(requests[0]["uuid"])

		self.assertNotEqual(len(request["calls"]), 0)

	def test_explain(self):
		sparrow.db.sql("SELECT * FROM tabDocType")
		sparrow.db.sql("COMMIT")
		sparrow.recorder.dump()
		sparrow.recorder.post_process()

		requests = sparrow.recorder.get()
		request = sparrow.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"][0]["explain_result"]), 1)
		self.assertEqual(len(request["calls"][1]["explain_result"]), 0)

	def test_multiple_queries(self):
		queries = [
			{"mariadb": "SELECT * FROM tabDocType", "postgres": 'SELECT * FROM "tabDocType"'},
			{"mariadb": "SELECT COUNT(*) FROM tabDocType", "postgres": 'SELECT COUNT(*) FROM "tabDocType"'},
			{"mariadb": "COMMIT", "postgres": "COMMIT"},
		]

		sql_dialect = sparrow.db.db_type or "mariadb"
		for query in queries:
			sparrow.db.sql(query[sql_dialect])

		sparrow.recorder.dump()
		sparrow.recorder.post_process()

		requests = sparrow.recorder.get()
		request = sparrow.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), len(queries))

		for query, call in zip(queries, request["calls"]):
			self.assertEqual(
				call["query"], sqlparse.format(query[sql_dialect].strip(), keyword_case="upper", reindent=True)
			)

	def test_duplicate_queries(self):
		queries = [
			("SELECT * FROM tabDocType", 2),
			("SELECT COUNT(*) FROM tabDocType", 1),
			("select * from tabDocType", 2),
			("COMMIT", 3),
			("COMMIT", 3),
			("COMMIT", 3),
		]
		for query in queries:
			sparrow.db.sql(query[0])

		sparrow.recorder.dump()
		sparrow.recorder.post_process()

		requests = sparrow.recorder.get()
		request = sparrow.recorder.get(requests[0]["uuid"])

		for query, call in zip(queries, request["calls"]):
			self.assertEqual(call["exact_copies"], query[1])

	def test_error_page_rendering(self):
		content = get_response_content("error")
		self.assertIn("Error", content)


class TestRecorderDeco(SparrowTestCase):
	def test_recorder_flag(self):
		sparrow.recorder.delete()

		@sparrow.recorder.record_queries
		def test():
			sparrow.get_all("User")

		test()
		self.assertTrue(sparrow.recorder.get())


class TestQueryNormalization(SparrowTestCase):
	def test_query_normalization(self):
		test_cases = {
			"select * from user where name = 'x'": "select * from user where name = ?",
			"select * from user where a > 5": "select * from user where a > ?",
			"select * from `user` where a > 5": "select * from `user` where a > ?",
			"select `name` from `user`": "select `name` from `user`",
			"select `name` from `user` limit 10": "select `name` from `user` limit ?",
		}

		for query, normalized in test_cases.items():
			self.assertEqual(normalize_query(query), normalized)
