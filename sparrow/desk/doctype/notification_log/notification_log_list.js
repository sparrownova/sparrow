sparrow.listview_settings["Notification Log"] = {
	onload: function (listview) {
		sparrow.require("logtypes.bundle.js", () => {
			sparrow.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
