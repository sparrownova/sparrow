import sparrow


def execute():
	sparrow.reload_doc("workflow", "doctype", "workflow_transition")
	sparrow.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
