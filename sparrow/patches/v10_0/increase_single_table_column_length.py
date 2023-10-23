"""
Run this after updating country_info.json and or
"""
import sparrow


def execute():
	for col in ("field", "doctype"):
		sparrow.db.sql_ddl(f"alter table `tabSingles` modify column `{col}` varchar(255)")
