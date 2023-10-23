import sparrow


def execute():
	sparrow.reload_doctype("Translation")
	sparrow.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
