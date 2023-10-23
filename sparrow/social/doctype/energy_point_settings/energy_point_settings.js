// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Energy Point Settings", {
	refresh: function (frm) {
		if (frm.doc.enabled) {
			frm.add_custom_button(__("Give Review Points"), show_review_points_dialog);
		}
	},
});

function show_review_points_dialog() {
	const dialog = new sparrow.ui.Dialog({
		title: __("Give Review Points"),
		fields: [
			{
				label: "User",
				fieldname: "user",
				fieldtype: "Link",
				options: "User",
				reqd: 1,
			},
			{
				label: "Points",
				fieldname: "points",
				fieldtype: "Int",
				reqd: 1,
			},
		],
		primary_action: function (values) {
			sparrow
				.xcall(
					"sparrow.social.doctype.energy_point_log.energy_point_log.add_review_points",
					{
						user: values.user,
						points: values.points,
					}
				)
				.then(() => {
					sparrow.show_alert({
						message: __("Successfully Done"),
						indicator: "green",
					});
				})
				.finally(() => dialog.hide());
		},
		primary_action_label: __("Submit"),
	});
	dialog.show();
}
