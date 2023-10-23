import sparrow


def execute():
	sparrow.db.change_column_type("__Auth", column="password", type="TEXT")
