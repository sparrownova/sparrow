# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import time

from werkzeug.wrappers import Response

import sparrow
import sparrow.rate_limiter
from sparrow.rate_limiter import RateLimiter
from sparrow.tests.utils import sparrowTestCase
from sparrow.utils import cint


class TestRateLimiter(sparrowTestCase):
	def test_apply_with_limit(self):
		sparrow.conf.rate_limit = {"window": 86400, "limit": 1}
		sparrow.rate_limiter.apply()

		self.assertTrue(hasattr(sparrow.local, "rate_limiter"))
		self.assertIsInstance(sparrow.local.rate_limiter, RateLimiter)

		sparrow.cache().delete(sparrow.local.rate_limiter.key)
		delattr(sparrow.local, "rate_limiter")

	def test_apply_without_limit(self):
		sparrow.conf.rate_limit = None
		sparrow.rate_limiter.apply()

		self.assertFalse(hasattr(sparrow.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		sparrow.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(sparrow.TooManyRequestsError, sparrow.rate_limiter.apply)
		sparrow.rate_limiter.update()

		response = sparrow.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = sparrow.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertNotIn("X-RateLimit-Used", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		sparrow.cache().delete(limiter.key)
		sparrow.cache().delete(sparrow.local.rate_limiter.key)
		delattr(sparrow.local, "rate_limiter")

	def test_respond_under_limit(self):
		sparrow.conf.rate_limit = {"window": 86400, "limit": 0.01}
		sparrow.rate_limiter.apply()
		sparrow.rate_limiter.update()
		response = sparrow.rate_limiter.respond()
		self.assertEqual(response, None)

		sparrow.cache().delete(sparrow.local.rate_limiter.key)
		delattr(sparrow.local, "rate_limiter")

	def test_headers_under_limit(self):
		sparrow.conf.rate_limit = {"window": 86400, "limit": 0.01}
		sparrow.rate_limiter.apply()
		sparrow.rate_limiter.update()
		headers = sparrow.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Used"]), sparrow.local.rate_limiter.duration)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		sparrow.cache().delete(sparrow.local.rate_limiter.key)
		delattr(sparrow.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(sparrow.TooManyRequestsError, limiter.apply)

		sparrow.cache().delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		sparrow.cache().delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(sparrow.cache().get(limiter.key)))

		sparrow.cache().delete(limiter.key)
