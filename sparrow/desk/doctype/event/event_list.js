sparrow.listview_settings["Event"] = {
	add_fields: ["starts_on", "ends_on"],
	onload: function () {
		sparrow.route_options = {
			status: "Open",
		};
	},
};
