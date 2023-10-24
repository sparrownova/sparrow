import sparrow
from sparrow.deferred_insert import deferred_insert, save_to_db
from sparrow.tests.utils import sparrowTestCase


class TestDeferredInsert(sparrowTestCase):
	def test_deferred_insert(self):
		route_history = {"route": sparrow.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])

		save_to_db()
		self.assertTrue(sparrow.db.exists("Route History", route_history))
