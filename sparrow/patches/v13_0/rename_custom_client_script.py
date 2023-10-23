import sparrow
from sparrow.model.rename_doc import rename_doc


def execute():
	if sparrow.db.exists("DocType", "Client Script"):
		return

	sparrow.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	sparrow.flags.ignore_route_conflict_validation = False

	sparrow.reload_doctype("Client Script", force=True)
