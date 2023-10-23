# Copyright (c) 2020, Sparrow Technologies and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.core.doctype.installed_applications.installed_applications import (
	InvalidAppOrder,
	update_installed_apps_order,
)
from sparrow.tests.utils import FrappeTestCase


class TestInstalledApplications(FrappeTestCase):
	def test_order_change(self):
		update_installed_apps_order(["sparrow"])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, [])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, ["sparrow", "deepmind"])
