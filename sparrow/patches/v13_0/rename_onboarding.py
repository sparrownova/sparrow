# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	if sparrow.db.exists("DocType", "Onboarding"):
		sparrow.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
