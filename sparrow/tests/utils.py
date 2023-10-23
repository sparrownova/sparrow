import copy
import datetime
import signal
import unittest
from contextlib import contextmanager
from typing import Sequence
from unittest.mock import patch

import sparrow
from sparrow.model.base_document import BaseDocument
from sparrow.utils import cint

datetime_like_types = (datetime.datetime, datetime.date, datetime.time, datetime.timedelta)


class FrappeTestCase(unittest.TestCase):
	"""Base test class for Sparrow tests.


	If you specify `setUpClass` then make sure to call `super().setUpClass`
	otherwise this class will become ineffective.
	"""

	TEST_SITE = "test_site"

	SHOW_TRANSACTION_COMMIT_WARNINGS = False

	@classmethod
	def setUpClass(cls) -> None:
		cls.TEST_SITE = getattr(sparrow.local, "site", None) or cls.TEST_SITE
		cls.ADMIN_PASSWORD = sparrow.get_conf(cls.TEST_SITE).admin_password
		# flush changes done so far to avoid flake
		sparrow.db.commit()
		if cls.SHOW_TRANSACTION_COMMIT_WARNINGS:
			sparrow.db.add_before_commit(_commit_watcher)

		# enqueue teardown actions (executed in LIFO order)
		cls.addClassCleanup(_restore_thread_locals, copy.deepcopy(sparrow.local.flags))
		cls.addClassCleanup(_rollback_db)

		return super().setUpClass()

	def assertSequenceSubset(self, larger: Sequence, smaller: Sequence, msg=None):
		"""Assert that `expected` is a subset of `actual`."""
		self.assertTrue(set(smaller).issubset(set(larger)), msg=msg)

	# --- Sparrow Framework specific assertions
	def assertDocumentEqual(self, expected, actual):
		"""Compare a (partial) expected document with actual Document."""

		if isinstance(expected, BaseDocument):
			expected = expected.as_dict()

		for field, value in expected.items():
			if isinstance(value, list):
				actual_child_docs = actual.get(field)
				self.assertEqual(len(value), len(actual_child_docs), msg=f"{field} length should be same")
				for exp_child, actual_child in zip(value, actual_child_docs):
					self.assertDocumentEqual(exp_child, actual_child)
			else:
				self._compare_field(value, actual.get(field), actual, field)

	def _compare_field(self, expected, actual, doc: BaseDocument, field: str):
		msg = f"{field} should be same."

		if isinstance(expected, float):
			precision = doc.precision(field)
			self.assertAlmostEqual(
				expected, actual, places=precision, msg=f"{field} should be same to {precision} digits"
			)
		elif isinstance(expected, (bool, int)):
			self.assertEqual(expected, cint(actual), msg=msg)
		elif isinstance(expected, datetime_like_types):
			self.assertEqual(str(expected), str(actual), msg=msg)
		else:
			self.assertEqual(expected, actual, msg=msg)

	@contextmanager
	def assertQueryCount(self, count):
		queries = []

		def _sql_with_count(*args, **kwargs):
			ret = orig_sql(*args, **kwargs)
			queries.append(sparrow.db.last_query)
			return ret

		try:
			orig_sql = sparrow.db.sql
			sparrow.db.sql = _sql_with_count
			yield
			self.assertLessEqual(len(queries), count, msg="Queries executed: " + "\n\n".join(queries))
		finally:
			sparrow.db.sql = orig_sql

	@contextmanager
	def assertRowsRead(self, count):
		rows_read = 0

		def _sql_with_count(*args, **kwargs):
			nonlocal rows_read

			ret = orig_sql(*args, **kwargs)
			# count of last touched rows as per DB-API 2.0 https://peps.python.org/pep-0249/#rowcount
			rows_read += cint(sparrow.db._cursor.rowcount)
			return ret

		try:
			orig_sql = sparrow.db.sql
			sparrow.db.sql = _sql_with_count
			yield
			self.assertLessEqual(rows_read, count, msg="Queries read more rows than expected")
		finally:
			sparrow.db.sql = orig_sql


def _commit_watcher():
	import traceback

	print("Warning:, transaction committed during tests.")
	traceback.print_stack(limit=5)


def _rollback_db():
	sparrow.local.before_commit = []
	sparrow.local.rollback_observers = []
	sparrow.db.value_cache = {}
	sparrow.db.rollback()


def _restore_thread_locals(flags):
	sparrow.local.flags = flags
	sparrow.local.error_log = []
	sparrow.local.message_log = []
	sparrow.local.debug_log = []
	sparrow.local.realtime_log = []
	sparrow.local.conf = sparrow._dict(sparrow.get_site_config())
	sparrow.local.cache = {}
	sparrow.local.lang = "en"
	sparrow.local.preload_assets = {"style": [], "script": []}


@contextmanager
def change_settings(doctype, settings_dict):
	"""A context manager to ensure that settings are changed before running
	function and restored after running it regardless of exceptions occured.
	This is useful in tests where you want to make changes in a function but
	don't retain those changes.
	import and use as decorator to cover full function or using `with` statement.

	example:
	@change_settings("Print Settings", {"send_print_as_pdf": 1})
	def test_case(self):
	        ...
	"""

	try:
		settings = sparrow.get_doc(doctype)
		# remember setting
		previous_settings = copy.deepcopy(settings_dict)
		for key in previous_settings:
			previous_settings[key] = getattr(settings, key)

		# change setting
		for key, value in settings_dict.items():
			setattr(settings, key, value)
		settings.save(ignore_permissions=True)
		# singles are cached by default, clear to avoid flake
		sparrow.db.value_cache[settings] = {}
		yield  # yield control to calling function

	finally:
		# restore settings
		settings = sparrow.get_doc(doctype)
		for key, value in previous_settings.items():
			setattr(settings, key, value)
		settings.save(ignore_permissions=True)


def timeout(seconds=30, error_message="Test timed out."):
	"""Timeout decorator to ensure a test doesn't run for too long.

	adapted from https://stackoverflow.com/a/2282656"""

	def decorator(func):
		def _handle_timeout(signum, frame):
			raise Exception(error_message)

		def wrapper(*args, **kwargs):
			signal.signal(signal.SIGALRM, _handle_timeout)
			signal.alarm(seconds)
			try:
				result = func(*args, **kwargs)
			finally:
				signal.alarm(0)
			return result

		return wrapper

	return decorator


@contextmanager
def patch_hooks(overridden_hoooks):
	get_hooks = sparrow.get_hooks

	def patched_hooks(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
		if hook in overridden_hoooks:
			return overridden_hoooks[hook]
		return get_hooks(hook, default, app_name)

	with patch.object(sparrow, "get_hooks", patched_hooks):
		yield
