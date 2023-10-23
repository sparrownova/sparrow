import sparrow


def execute():
	if sparrow.db.table_exists("Prepared Report"):
		sparrow.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = sparrow.get_all("Prepared Report")
		for report in prepared_reports:
			sparrow.delete_doc("Prepared Report", report.name)
