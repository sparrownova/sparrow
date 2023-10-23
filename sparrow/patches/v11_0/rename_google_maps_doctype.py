import sparrow
from sparrow.model.rename_doc import rename_doc


def execute():
	if sparrow.db.exists("DocType", "Google Maps") and not sparrow.db.exists(
		"DocType", "Google Maps Settings"
	):
		rename_doc("DocType", "Google Maps", "Google Maps Settings")
