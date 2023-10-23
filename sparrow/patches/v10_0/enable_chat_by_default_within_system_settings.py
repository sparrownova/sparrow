import sparrow


def execute():
	sparrow.reload_doctype("System Settings")
	doc = sparrow.get_single("System Settings")
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabin@sparrow.io)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True

	doc.save()
