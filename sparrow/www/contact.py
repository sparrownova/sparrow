# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from contextlib import suppress

import sparrow
from sparrow import _
from sparrow.rate_limiter import rate_limit
from sparrow.utils import validate_email_address

sitemap = 1


def get_context(context):
	doc = sparrow.get_doc("Contact Us Settings", "Contact Us Settings")

	if doc.query_options:
		query_options = [opt.strip() for opt in doc.query_options.replace(",", "\n").split("\n") if opt]
	else:
		query_options = ["Sales", "Support", "General"]

	out = {"query_options": query_options, "parents": [{"name": _("Home"), "route": "/"}]}
	out.update(doc.as_dict())

	return out


@sparrow.whitelist(allow_guest=True)
@rate_limit(limit=1000, seconds=60 * 60)
def send_message(sender, message, subject="Website Query"):
	sender = validate_email_address(sender, throw=True)

	with suppress(sparrow.OutgoingEmailError):
		if forward_to_email := sparrow.db.get_single_value("Contact Us Settings", "forward_to_email"):
			sparrow.sendmail(recipients=forward_to_email, reply_to=sender, content=message, subject=subject)

		sparrow.sendmail(
			recipients=sender,
			content=f"<div style='white-space: pre-wrap'>Thank you for reaching out to us. We will get back to you at the earliest.\n\n\nYour query:\n\n{message}</div>",
			subject="We've received your query!",
		)

	# for clearing outgoing email error message
	sparrow.clear_last_message()

	# add to to-do ?
	sparrow.get_doc(
		dict(
			doctype="Communication",
			sender=sender,
			subject=_("New Message from Website Contact Page"),
			sent_or_received="Received",
			content=message,
			status="Open",
		)
	).insert(ignore_permissions=True)
