# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.utils import strip_html_tags
from sparrow.utils.html_utils import clean_html

no_cache = 1


def get_context(context):
	message_context = sparrow._dict()
	if hasattr(sparrow.local, "message"):
		message_context["header"] = sparrow.local.message_title
		message_context["title"] = strip_html_tags(sparrow.local.message_title)
		message_context["message"] = sparrow.local.message
		if hasattr(sparrow.local, "message_success"):
			message_context["success"] = sparrow.local.message_success

	elif sparrow.local.form_dict.id:
		message_id = sparrow.local.form_dict.id
		key = f"message_id:{message_id}"
		message = sparrow.cache().get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				sparrow.local.response["http_status_code"] = message["http_status_code"]

	if not message_context.title:
		message_context.title = clean_html(sparrow.form_dict.title)

	if not message_context.message:
		message_context.message = clean_html(sparrow.form_dict.message)

	return message_context
