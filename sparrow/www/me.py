# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
import sparrow.www.list
from sparrow import _

no_cache = 1


def get_context(context):
	if sparrow.session.user == "Guest":
		sparrow.throw(_("You need to be logged in to access this page"), sparrow.PermissionError)

	context.current_user = sparrow.get_doc("User", sparrow.session.user)
	context.show_sidebar = True
