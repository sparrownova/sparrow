# Copyright (c) 2023, Sparrow Technologies and contributors
# For license information, please see license.txt

import sparrow
from sparrow.model.document import Document
from sparrow.query_builder.utils import DocType


class CustomHTMLBlock(Document):
	pass


@sparrow.whitelist()
def get_custom_blocks_for_user(doctype, txt, searchfield, start, page_len, filters):
	# return logged in users private blocks and all public blocks
	customHTMLBlock = DocType("Custom HTML Block")

	condition_query = sparrow.qb.get_query(customHTMLBlock)

	return (
		condition_query.select(customHTMLBlock.name).where(
			(customHTMLBlock.private == 0)
			| ((customHTMLBlock.owner == sparrow.session.user) & (customHTMLBlock.private == 1))
		)
	).run()
