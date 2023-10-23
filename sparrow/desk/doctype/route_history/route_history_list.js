sparrow.listview_settings["Route History"] = {
	onload: function (listview) {
		sparrow.require("logtypes.bundle.js", () => {
			sparrow.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
