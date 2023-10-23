# Copyright (c) 2021, Sparrow Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "web_form_list_column")
	sparrow.reload_doctype("Web Form")

	for web_form in sparrow.get_all("Web Form", fields=["*"]):
		if web_form.allow_multiple and not web_form.show_list:
			sparrow.db.set_value("Web Form", web_form.name, "show_list", True)
