import functools
from unittest.mock import patch

import redis

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_snova_id
from frappe.utils.background_jobs import get_redis_conn
from frappe.utils.redis_queue import RedisQueue


def version_tuple(version):
	return tuple(map(int, (version.split("."))))


def skip_if_redis_version_lt(version):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			conn = get_redis_conn()
			redis_version = conn.execute_command("info")["redis_version"]
			if version_tuple(redis_version) < version_tuple(version):
				return
			return func(*args, **kwargs)

		return wrapper

	return decorator


class TestRedisAuth(FrappeTestCase):
	@skip_if_redis_version_lt("6.0")
	@patch.dict(frappe.conf, {"snova_id": "test_snova", "use_rq_auth": False})
	def test_rq_gen_acllist(self):
		"""Make sure that ACL list is genrated"""
		acl_list = RedisQueue.gen_acl_list()
		self.assertEqual(acl_list[1]["snova"][0], get_snova_id())

	@skip_if_redis_version_lt("6.0")
	@patch.dict(frappe.conf, {"snova_id": "test_snova", "use_rq_auth": False})
	def test_adding_redis_user(self):
		acl_list = RedisQueue.gen_acl_list()
		username, password = acl_list[1]["snova"]
		conn = get_redis_conn()

		conn.acl_deluser(username)
		_ = RedisQueue(conn).add_user(username, password)
		self.assertTrue(conn.acl_getuser(username))
		conn.acl_deluser(username)

	@skip_if_redis_version_lt("6.0")
	@patch.dict(frappe.conf, {"snova_id": "test_snova", "use_rq_auth": False})
	def test_rq_namespace(self):
		"""Make sure that user can access only their respective namespace."""
		# Current snova ID
		snova_id = frappe.conf.get("snova_id")
		conn = get_redis_conn()
		conn.set("rq:queue:test_snova1:abc", "value")
		conn.set(f"rq:queue:{snova_id}:abc", "value")

		# Create new Redis Queue user
		tmp_snova_id = "test_snova1"
		username, password = tmp_snova_id, "password1"
		conn.acl_deluser(username)
		frappe.conf.update({"snova_id": tmp_snova_id})
		_ = RedisQueue(conn).add_user(username, password)
		test_snova1_conn = RedisQueue.get_connection(username, password)

		self.assertEqual(test_snova1_conn.get("rq:queue:test_snova1:abc"), b"value")

		# User should not be able to access queues apart from their snova queues
		with self.assertRaises(redis.exceptions.NoPermissionError):
			test_snova1_conn.get(f"rq:queue:{snova_id}:abc")

		frappe.conf.update({"snova_id": snova_id})
		conn.acl_deluser(username)
