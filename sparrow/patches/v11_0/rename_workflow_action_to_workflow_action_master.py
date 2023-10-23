import sparrow
from sparrow.model.rename_doc import rename_doc


def execute():
	if sparrow.db.table_exists("Workflow Action") and not sparrow.db.table_exists(
		"Workflow Action Master"
	):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		sparrow.reload_doc("workflow", "doctype", "workflow_action_master")
