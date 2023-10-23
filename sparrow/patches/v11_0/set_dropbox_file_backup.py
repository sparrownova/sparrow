import sparrow
from sparrow.utils import cint


def execute():
	sparrow.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(sparrow.db.get_single_value("Dropbox Settings", "enabled"))
	if check_dropbox_enabled == 1:
		sparrow.db.set_single_value("Dropbox Settings", "file_backup", 1)
