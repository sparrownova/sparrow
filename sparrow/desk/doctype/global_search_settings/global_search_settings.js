// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Global Search Settings", {
	refresh: function (frm) {
		sparrow.realtime.on("global_search_settings", (data) => {
			if (data.progress) {
				frm.dashboard.show_progress(
					"Setting up Global Search",
					(data.progress / data.total) * 100,
					data.msg
				);
				if (data.progress === data.total) {
					frm.dashboard.hide_progress("Setting up Global Search");
				}
			}
		});

		frm.add_custom_button(__("Reset"), function () {
			sparrow.call({
				method: "sparrow.desk.doctype.global_search_settings.global_search_settings.reset_global_search_settings_doctypes",
				callback: function () {
					sparrow.show_alert({
						message: __("Global Search Document Types Reset."),
						indicator: "green",
					});
					frm.refresh();
				},
			});
		});
	},
});
