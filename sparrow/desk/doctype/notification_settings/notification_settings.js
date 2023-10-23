// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Notification Settings", {
	onload: (frm) => {
		sparrow.breadcrumbs.add({
			label: __("Settings"),
			route: "#modules/Settings",
			type: "Custom",
		});
		frm.set_query("subscribed_documents", () => {
			return {
				filters: {
					istable: 0,
				},
			};
		});
	},

	refresh: (frm) => {
		if (sparrow.user.has_role("System Manager")) {
			frm.add_custom_button(__("Go to Notification Settings List"), () => {
				sparrow.set_route("List", "Notification Settings");
			});
		}
	},
});
