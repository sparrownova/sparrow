# Copyright (c) 2018, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	signatures = sparrow.db.get_list(
		"User", {"email_signature": ["!=", ""]}, ["name", "email_signature"]
	)
	sparrow.reload_doc("core", "doctype", "user")
	for d in signatures:
		signature = d.get("email_signature")
		signature = signature.replace("\n", "<br>")
		signature = "<div>" + signature + "</div>"
		sparrow.db.set_value("User", d.get("name"), "email_signature", signature)
