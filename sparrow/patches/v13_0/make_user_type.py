import sparrow
from sparrow.utils.install import create_user_type


def execute():
	sparrow.reload_doc("core", "doctype", "role")
	sparrow.reload_doc("core", "doctype", "user_document_type")
	sparrow.reload_doc("core", "doctype", "user_type_module")
	sparrow.reload_doc("core", "doctype", "user_select_document_type")
	sparrow.reload_doc("core", "doctype", "user_type")

	create_user_type()
