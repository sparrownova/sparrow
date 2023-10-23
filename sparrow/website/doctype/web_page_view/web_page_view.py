# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class WebPageView(Document):
	pass


@sparrow.whitelist(allow_guest=True)
def make_view_log(path, referrer=None, browser=None, version=None, url=None, user_tz=None):
	if not is_tracking_enabled():
		return

	request_dict = sparrow.request.__dict__
	user_agent = request_dict.get("environ", {}).get("HTTP_USER_AGENT")

	if referrer:
		referrer = referrer.split("?", 1)[0]

	is_unique = True
	if referrer.startswith(url):
		is_unique = False

	if path != "/" and path.startswith("/"):
		path = path[1:]

	view = sparrow.new_doc("Web Page View")
	view.path = path
	view.referrer = referrer
	view.browser = browser
	view.browser_version = version
	view.time_zone = user_tz
	view.user_agent = user_agent
	view.is_unique = is_unique

	try:
		if sparrow.flags.read_only:
			view.deferred_insert()
		else:
			view.insert(ignore_permissions=True)
	except Exception:
		if sparrow.message_log:
			sparrow.message_log.pop()


@sparrow.whitelist()
def get_page_view_count(path):
	return sparrow.db.count("Web Page View", filters={"path": path})


def is_tracking_enabled():
	return sparrow.db.get_single_value("Website Settings", "enable_view_tracking")
