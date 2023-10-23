# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "system_settings", force=1)
	sparrow.db.set_single_value("System Settings", "password_reset_limit", 3)
