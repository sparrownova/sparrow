sparrow.listview_settings["Integration Request"] = {
	onload: function (list_view) {
		sparrow.require("logtypes.bundle.js", () => {
			sparrow.utils.logtypes.show_log_retention_message(list_view.doctype);
		});
	},
};
