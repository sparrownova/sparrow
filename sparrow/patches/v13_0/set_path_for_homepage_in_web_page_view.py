import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "web_page_view", force=True)
	sparrow.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")
