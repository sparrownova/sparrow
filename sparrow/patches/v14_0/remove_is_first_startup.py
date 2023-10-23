import sparrow


def execute():
	singles = sparrow.qb.Table("tabSingles")
	sparrow.qb.from_(singles).delete().where(
		(singles.doctype == "System Settings") & (singles.field == "is_first_startup")
	).run()
