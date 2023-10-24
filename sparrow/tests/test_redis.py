import functools
from unittest.mock import patch

import redis

import sparrow
from sparrow.tests.utils import sparrowTestCase
from sparrow.utils import get_bench_id
from sparrow.utils.background_jobs import get_redis_conn
from sparrow.utils.redis_queue import RedisQueue


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


class TestRedisAuth(sparrowTestCase):
	@skip_if_redis_version_lt("6.0")
	@patch.dict(sparrow.conf, {"bench_id": "test_bench", "use_rq_auth": False})
	def test_rq_gen_acllist(self):
		"""Make sure that ACL list is genrated"""
		acl_list = RedisQueue.gen_acl_list()
		self.assertEqual(acl_list[1]["snova"][0], get_bench_id())

	@skip_if_redis_version_lt("6.0")
	@patch.dict(sparrow.conf, {"bench_id": "test_bench", "use_rq_auth": False})
	def test_adding_redis_user(self):
		acl_list = RedisQueue.gen_acl_list()
		username, password = acl_list[1]["snova"]
		conn = get_redis_conn()

		conn.acl_deluser(username)
		_ = RedisQueue(conn).add_user(username, password)
		self.assertTrue(conn.acl_getuser(username))
		conn.acl_deluser(username)

	@skip_if_redis_version_lt("6.0")
	@patch.dict(sparrow.conf, {"bench_id": "test_bench", "use_rq_auth": False})
	def test_rq_namespace(self):
		"""Make sure that user can access only their respective namespace."""
		# Current snova ID
		bench_id = sparrow.conf.get("bench_id")
		conn = get_redis_conn()
		conn.set("rq:queue:test_bench1:abc", "value")
		conn.set(f"rq:queue:{bench_id}:abc", "value")

		# Create new Redis Queue user
		tmp_bench_id = "test_bench1"
		username, password = tmp_bench_id, "password1"
		conn.acl_deluser(username)
		sparrow.conf.update({"bench_id": tmp_bench_id})
		_ = RedisQueue(conn).add_user(username, password)
		test_bench1_conn = RedisQueue.get_connection(username, password)

		self.assertEqual(test_bench1_conn.get("rq:queue:test_bench1:abc"), b"value")

		# User should not be able to access queues apart from their snova queues
		with self.assertRaises(redis.exceptions.NoPermissionError):
			test_bench1_conn.get(f"rq:queue:{bench_id}:abc")

		sparrow.conf.update({"bench_id": bench_id})
		conn.acl_deluser(username)
