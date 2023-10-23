# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.model.document import Document


class SessionDefaultSettings(Document):
	pass


@sparrow.whitelist()
def get_session_default_values():
	settings = sparrow.get_single("Session Default Settings")
	fields = []
	for default_values in settings.session_defaults:
		reference_doctype = sparrow.scrub(default_values.ref_doctype)
		fields.append(
			{
				"fieldname": reference_doctype,
				"fieldtype": "Link",
				"options": default_values.ref_doctype,
				"label": _("Default {0}").format(_(default_values.ref_doctype)),
				"default": sparrow.defaults.get_user_default(reference_doctype),
			}
		)
	return json.dumps(fields)


@sparrow.whitelist()
def set_session_default_values(default_values):
	default_values = sparrow.parse_json(default_values)
	for entry in default_values:
		try:
			sparrow.defaults.set_user_default(entry, default_values.get(entry))
		except Exception:
			return
	return "success"


# called on hook 'on_logout' to clear defaults for the session
def clear_session_defaults():
	settings = sparrow.get_single("Session Default Settings").session_defaults
	for entry in settings:
		sparrow.defaults.clear_user_default(sparrow.scrub(entry.ref_doctype))
