import sparrow


def execute():
	if sparrow.db.db_type == "mariadb":
		sparrow.db.sql_ddl("alter table `tabSingles` modify column `value` longtext")
