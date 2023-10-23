# Copyright (c) 2015, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
from ldap3.core.exceptions import LDAPException, LDAPInappropriateAuthenticationResult

import sparrow
from sparrow.tests.utils import SparrowTestCase
from sparrow.utils.error import _is_ldap_exception

# test_records = sparrow.get_test_records('Error Log')


class TestErrorLog(SparrowTestCase):
	def test_error_log(self):
		"""let's do an error log on error log?"""
		doc = sparrow.new_doc("Error Log")
		error = doc.log_error("This is an error")
		self.assertEqual(error.doctype, "Error Log")

	def test_ldap_exceptions(self):
		exc = [LDAPException, LDAPInappropriateAuthenticationResult]

		for e in exc:
			self.assertTrue(_is_ldap_exception(e()))
