# Copyright (c) 2015, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import time

import sparrow
from sparrow.auth import CookieManager, LoginManager
from sparrow.tests.utils import SparrowTestCase


class TestActivityLog(SparrowTestCase):
	def test_activity_log(self):

		# test user login log
		sparrow.local.form_dict = sparrow._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": sparrow.conf.admin_password or "admin",
				"usr": "Administrator",
			}
		)

		sparrow.local.cookie_manager = CookieManager()
		sparrow.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(sparrow.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		sparrow.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		sparrow.form_dict.update({"pwd": "password"})
		self.assertRaises(sparrow.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		sparrow.local.form_dict = sparrow._dict()

	def get_auth_log(self, operation="Login"):
		names = sparrow.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		auth_log = sparrow.get_doc("Activity Log", name)
		return auth_log

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		sparrow.local.form_dict = sparrow._dict(
			{"cmd": "login", "sid": "Guest", "pwd": "admin", "usr": "Administrator"}
		)

		sparrow.local.cookie_manager = CookieManager()
		sparrow.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		sparrow.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		sparrow.form_dict.update({"pwd": "password"})
		self.assertRaises(sparrow.AuthenticationError, LoginManager)
		self.assertRaises(sparrow.AuthenticationError, LoginManager)
		self.assertRaises(sparrow.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(sparrow.AuthenticationError, LoginManager)
		self.assertRaises(sparrow.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(sparrow.AuthenticationError, LoginManager)

		sparrow.local.form_dict = sparrow._dict()


def update_system_settings(args):
	doc = sparrow.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
