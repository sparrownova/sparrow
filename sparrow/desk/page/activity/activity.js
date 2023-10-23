// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// License: See license.txt

sparrow.provide("sparrow.activity");

sparrow.pages["activity"].on_page_load = function (wrapper) {
	var me = this;

	sparrow.ui.make_app_page({
		parent: wrapper,
		single_column: true,
	});

	me.page = wrapper.page;
	me.page.set_title(__("Activity"));

	sparrow.model.with_doctype("Communication", function () {
		me.page.list = new sparrow.views.Activity({
			doctype: "Communication",
			parent: wrapper,
		});
	});

	sparrow.activity.render_heatmap(me.page);

	me.page.main.on("click", ".activity-message", function () {
		var link_doctype = $(this).attr("data-link-doctype"),
			link_name = $(this).attr("data-link-name"),
			doctype = $(this).attr("data-doctype"),
			docname = $(this).attr("data-docname");

		[link_doctype, link_name, doctype, docname] = [
			link_doctype,
			link_name,
			doctype,
			docname,
		].map(decodeURIComponent);

		link_doctype = link_doctype && link_doctype !== "null" ? link_doctype : null;
		link_name = link_name && link_name !== "null" ? link_name : null;

		if (doctype && docname) {
			if (link_doctype && link_name) {
				sparrow.route_options = {
					scroll_to: { doctype: doctype, name: docname },
				};
			}

			sparrow.set_route(["Form", link_doctype || doctype, link_name || docname]);
		}
	});

	// Build Report Button
	if (sparrow.boot.user.can_get_report.indexOf("Feed") != -1) {
		this.page.add_menu_item(
			__("Build Report"),
			function () {
				sparrow.set_route("List", "Feed", "Report");
			},
			"fa fa-th"
		);
	}

	this.page.add_menu_item(
		__("Activity Log"),
		function () {
			sparrow.route_options = {
				user: sparrow.session.user,
			};

			sparrow.set_route("List", "Activity Log", "Report");
		},
		"fa fa-th"
	);
};

sparrow.pages["activity"].on_page_show = function () {
	sparrow.breadcrumbs.add("Desk");
};

sparrow.activity.last_feed_date = false;
sparrow.activity.Feed = class Feed {
	constructor(row, data) {
		this.scrub_data(data);
		this.add_date_separator(row, data);
		if (!data.add_class) data.add_class = "label-default";

		data.link = "";
		if (data.link_doctype && data.link_name) {
			data.link = sparrow.format(
				data.link_name,
				{ fieldtype: "Link", options: data.link_doctype },
				{ label: __(data.link_doctype) + " " + __(data.link_name) }
			);
		} else if (data.feed_type === "Comment" && data.comment_type === "Comment") {
			// hack for backward compatiblity
			data.link_doctype = data.reference_doctype;
			data.link_name = data.reference_name;
			data.reference_doctype = "Communication";
			data.reference_name = data.name;

			data.link = sparrow.format(
				data.link_name,
				{ fieldtype: "Link", options: data.link_doctype },
				{ label: __(data.link_doctype) + " " + __(data.link_name) }
			);
		} else if (data.reference_doctype && data.reference_name) {
			data.link = sparrow.format(
				data.reference_name,
				{ fieldtype: "Link", options: data.reference_doctype },
				{ label: __(data.reference_doctype) + " " + __(data.reference_name) }
			);
		}

		$(row).append(sparrow.render_template("activity_row", data)).find("a").addClass("grey");
	}

	scrub_data(data) {
		data.by = sparrow.user.full_name(data.owner);
		data.avatar = sparrow.avatar(data.owner);

		data.icon = "fa fa-flag";

		// color for comment
		data.add_class =
			{
				Comment: "label-danger",
				Assignment: "label-warning",
				Login: "label-default",
			}[data.comment_type || data.communication_medium] || "label-info";

		data.when = comment_when(data.creation);
		data.feed_type = data.comment_type || data.communication_medium;
	}

	add_date_separator(row, data) {
		var date = sparrow.datetime.str_to_obj(data.creation);
		var last = sparrow.activity.last_feed_date;

		if (
			(last && sparrow.datetime.obj_to_str(last) != sparrow.datetime.obj_to_str(date)) ||
			!last
		) {
			var diff = sparrow.datetime.get_day_diff(
				sparrow.datetime.get_today(),
				sparrow.datetime.obj_to_str(date)
			);
			var pdate;
			if (diff < 1) {
				pdate = "Today";
			} else if (diff < 2) {
				pdate = "Yesterday";
			} else {
				pdate = sparrow.datetime.global_date_format(date);
			}
			data.date_sep = pdate;
			data.date_class = pdate == "Today" ? "date-indicator blue" : "date-indicator";
		} else {
			data.date_sep = null;
			data.date_class = "";
		}
		sparrow.activity.last_feed_date = date;
	}
};

sparrow.activity.render_heatmap = function (page) {
	$(
		'<div class="heatmap-container" style="text-align:center">\
		<div class="heatmap" style="display:inline-block;"></div></div>\
		<hr style="margin-bottom: 0px;">'
	).prependTo(page.main);

	sparrow.call({
		method: "sparrow.desk.page.activity.activity.get_heatmap_data",
		callback: function (r) {
			if (r.message) {
				new sparrow.Chart(".heatmap", {
					type: "heatmap",
					start: new Date(moment().subtract(1, "year").toDate()),
					countLabel: "actions",
					discreteDomains: 1,
					radius: 3, // default 0
					data: {
						dataPoints: r.message,
					},
				});
			}
		},
	});
};

sparrow.views.Activity = class Activity extends sparrow.views.BaseList {
	constructor(opts) {
		super(opts);
		this.show();
	}

	setup_defaults() {
		super.setup_defaults();

		this.page_title = __("Activity");
		this.doctype = "Communication";
		this.method = "sparrow.desk.page.activity.activity.get_feed";
	}

	setup_filter_area() {
		//
	}

	setup_view_menu() {
		//
	}

	setup_sort_selector() {}

	setup_side_bar() {}

	get_args() {
		return {
			start: this.start,
			page_length: this.page_length,
		};
	}

	update_data(r) {
		let data = r.message || [];

		if (this.start === 0) {
			this.data = data;
		} else {
			this.data = this.data.concat(data);
		}
	}

	render() {
		this.data.map((value) => {
			const row = $('<div class="list-row">')
				.data("data", value)
				.appendTo(this.$result)
				.get(0);
			new sparrow.activity.Feed(row, value);
		});
	}
};
