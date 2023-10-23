import sparrow
from sparrow.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for Shopper in Navbar Settings
	sparrow.reload_doc("core", "doctype", "navbar_settings")
	sparrow.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
