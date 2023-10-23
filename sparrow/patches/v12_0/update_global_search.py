import sparrow
from sparrow.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	sparrow.reload_doc("desk", "doctype", "global_search_doctype")
	sparrow.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
