# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

"""docfield utililtes"""

import frappe


def supports_translation(fieldtype):
	return fieldtype in ["Data", "Select", "Text", "Small Text", "Text Editor"]
