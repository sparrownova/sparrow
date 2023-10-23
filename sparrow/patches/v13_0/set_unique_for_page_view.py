import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = sparrow.utils.get_site_url(sparrow.local.site)
	sparrow.db.sql(f"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{site_url}%'""")
