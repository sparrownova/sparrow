let imports_in_progress = [];

sparrow.listview_settings["Data Import"] = {
	onload(listview) {
		sparrow.realtime.on("data_import_progress", (data) => {
			if (!imports_in_progress.includes(data.data_import)) {
				imports_in_progress.push(data.data_import);
			}
		});
		sparrow.realtime.on("data_import_refresh", (data) => {
			imports_in_progress = imports_in_progress.filter((d) => d !== data.data_import);
			listview.refresh();
		});
	},
	get_indicator: function (doc) {
		var colors = {
			Pending: "orange",
			"Not Started": "orange",
			"Partial Success": "orange",
			Success: "green",
			"In Progress": "orange",
			Error: "red",
		};
		let status = doc.status;

		if (imports_in_progress.includes(doc.name)) {
			status = "In Progress";
		}
		if (status == "Pending") {
			status = "Not Started";
		}

		return [__(status), colors[status], "status,=," + doc.status];
	},
	formatters: {
		import_type(value) {
			return {
				"Insert New Records": __("Insert"),
				"Update Existing Records": __("Update"),
			}[value];
		},
	},
	hide_name_column: true,
};