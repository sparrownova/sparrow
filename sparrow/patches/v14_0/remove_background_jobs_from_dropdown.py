import sparrow


def execute():
	item = sparrow.db.exists("Navbar Item", {"item_label": "Background Jobs"})
	if not item:
		return

	sparrow.delete_doc("Navbar Item", item)
