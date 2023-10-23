# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "system_settings")
	sparrow.db.set_single_value("System Settings", "allow_login_after_fail", 60)
