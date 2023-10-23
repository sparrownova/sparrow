// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.query_reports["Permitted Documents For User"] = {
	filters: [
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
			reqd: 1,
		},
		{
			fieldname: "doctype",
			label: __("DocType"),
			fieldtype: "Link",
			options: "DocType",
			reqd: 1,
			get_query: function () {
				return {
					query: "sparrow.core.report.permitted_documents_for_user.permitted_documents_for_user.query_doctypes",
					filters: {
						user: sparrow.query_report.get_filter_value("user"),
					},
				};
			},
		},
		{
			fieldname: "show_permissions",
			label: __("Show Permissions"),
			fieldtype: "Check",
		},
	],
};
