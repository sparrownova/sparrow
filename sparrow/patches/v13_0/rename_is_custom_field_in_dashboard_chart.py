import sparrow
from sparrow.model.utils.rename_field import rename_field


def execute():
	if not sparrow.db.table_exists("Dashboard Chart"):
		return

	sparrow.reload_doc("desk", "doctype", "dashboard_chart")

	if sparrow.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
