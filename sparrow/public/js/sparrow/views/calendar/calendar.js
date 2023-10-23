// Copyright (c) 2018, Sparrownova Technologies and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.views.calendar");
sparrow.provide("sparrow.views.calendars");

sparrow.views.CalendarView = class CalendarView extends sparrow.views.ListView {
	static load_last_view() {
		const route = sparrow.get_route();
		if (route.length === 3) {
			const doctype = route[1];
			const user_settings = sparrow.get_user_settings(doctype)["Calendar"] || {};
			route.push(user_settings.last_calendar || "default");
			sparrow.set_route(route);
			return true;
		} else {
			return false;
		}
	}

	toggle_result_area() {}

	get view_name() {
		return "Calendar";
	}

	setup_defaults() {
		return super.setup_defaults().then(() => {
			this.page_title = __("{0} Calendar", [this.page_title]);
			this.calendar_settings = sparrow.views.calendar[this.doctype] || {};
			this.calendar_name = sparrow.get_route()[3];
		});
	}

	setup_page() {
		this.hide_page_form = true;
		super.setup_page();
	}

	setup_view() {}

	before_render() {
		super.before_render();
		this.save_view_user_settings({
			last_calendar: this.calendar_name,
		});
	}

	render() {
		if (this.calendar) {
			this.calendar.refresh();
			return;
		}

		this.load_lib
			.then(() => this.get_calendar_preferences())
			.then((options) => {
				this.calendar = new sparrow.views.Calendar(options);
			});
	}

	get_calendar_preferences() {
		const options = {
			doctype: this.doctype,
			parent: this.$result,
			page: this.page,
			list_view: this,
		};
		const calendar_name = this.calendar_name;

		return new Promise((resolve) => {
			if (calendar_name === "default") {
				Object.assign(options, sparrow.views.calendar[this.doctype]);
				resolve(options);
			} else {
				sparrow.model.with_doc("Calendar View", calendar_name, () => {
					const doc = sparrow.get_doc("Calendar View", calendar_name);
					if (!doc) {
						sparrow.show_alert(
							__("{0} is not a valid Calendar. Redirecting to default Calendar.", [
								calendar_name.bold(),
							])
						);
						sparrow.set_route("List", this.doctype, "Calendar", "default");
						return;
					}
					Object.assign(options, {
						field_map: {
							id: "name",
							start: doc.start_date_field,
							end: doc.end_date_field,
							title: doc.subject_field,
							allDay: doc.all_day ? 1 : 0,
						},
					});
					resolve(options);
				});
			}
		});
	}

	get required_libs() {
		let assets = [
			"assets/sparrow/js/lib/fullcalendar/fullcalendar.min.css",
			"assets/sparrow/js/lib/fullcalendar/fullcalendar.min.js",
		];
		let user_language = sparrow.boot.user.language;
		if (user_language && user_language !== "en") {
			assets.push("assets/sparrow/js/lib/fullcalendar/locale-all.js");
		}
		return assets;
	}
};

sparrow.views.Calendar = class Calendar {
	constructor(options) {
		$.extend(this, options);
		this.field_map = this.field_map || {
			id: "name",
			start: "start",
			end: "end",
			allDay: "all_day",
			convertToUserTz: "convert_to_user_tz",
		};
		this.color_map = {
			danger: "red",
			success: "green",
			warning: "orange",
			default: "blue",
		};
		this.get_default_options();
	}
	get_default_options() {
		return new Promise((resolve) => {
			let defaultView = localStorage.getItem("cal_defaultView");
			let weekends = localStorage.getItem("cal_weekends");
			let defaults = {
				defaultView: defaultView ? defaultView : "month",
				weekends: weekends ? weekends : true,
			};
			resolve(defaults);
		}).then((defaults) => {
			this.make_page();
			this.setup_options(defaults);
			this.make();
			this.setup_view_mode_button(defaults);
			this.bind();
		});
	}
	make_page() {
		var me = this;

		// add links to other calendars
		me.page.clear_user_actions();
		$.each(sparrow.boot.calendars, function (i, doctype) {
			if (sparrow.model.can_read(doctype)) {
				me.page.add_menu_item(__(doctype), function () {
					sparrow.set_route("List", doctype, "Calendar");
				});
			}
		});

		$(this.parent).on("show", function () {
			me.$cal.fullCalendar("refetchEvents");
		});
	}

	make() {
		this.$wrapper = this.parent;
		this.$cal = $("<div>").appendTo(this.$wrapper);
		this.footnote_area = sparrow.utils.set_footnote(
			this.footnote_area,
			this.$wrapper,
			__("Select or drag across time slots to create a new event.")
		);
		this.footnote_area.css({ "border-top": "0px" });

		this.$cal.fullCalendar(this.cal_options);
		this.set_css();
	}
	setup_view_mode_button(defaults) {
		var me = this;
		$(me.footnote_area).find(".btn-weekend").detach();
		let btnTitle = defaults.weekends ? __("Hide Weekends") : __("Show Weekends");
		const btn = `<button class="btn btn-default btn-xs btn-weekend">${btnTitle}</button>`;
		me.footnote_area.append(btn);
	}
	set_localStorage_option(option, value) {
		localStorage.removeItem(option);
		localStorage.setItem(option, value);
	}
	bind() {
		const me = this;
		let btn_group = me.$wrapper.find(".fc-button-group");
		btn_group.on("click", ".btn", function () {
			let value = $(this).hasClass("fc-agendaWeek-button")
				? "agendaWeek"
				: $(this).hasClass("fc-agendaDay-button")
				? "agendaDay"
				: "month";
			me.set_localStorage_option("cal_defaultView", value);
		});

		me.$wrapper.on("click", ".btn-weekend", function () {
			me.cal_options.weekends = !me.cal_options.weekends;
			me.$cal.fullCalendar("option", "weekends", me.cal_options.weekends);
			me.set_localStorage_option("cal_weekends", me.cal_options.weekends);
			me.set_css();
			me.setup_view_mode_button(me.cal_options);
		});
	}
	set_css() {
		// flatify buttons
		this.$wrapper
			.find("button.fc-state-default")
			.removeClass("fc-state-default")
			.addClass("btn btn-default");

		this.$wrapper
			.find(".fc-month-button, .fc-agendaWeek-button, .fc-agendaDay-button")
			.wrapAll('<div class="btn-group" />');

		this.$wrapper
			.find(".fc-prev-button span")
			.attr("class", "")
			.html(sparrow.utils.icon("left"));
		this.$wrapper
			.find(".fc-next-button span")
			.attr("class", "")
			.html(sparrow.utils.icon("right"));

		this.$wrapper.find(".fc-today-button").prepend(sparrow.utils.icon("today"));

		this.$wrapper.find(".fc-day-number").wrap('<div class="fc-day"></div>');

		var btn_group = this.$wrapper.find(".fc-button-group");
		btn_group.find(".fc-state-active").addClass("active");

		btn_group.find(".btn").on("click", function () {
			btn_group.find(".btn").removeClass("active");
			$(this).addClass("active");
		});
	}

	get_system_datetime(date) {
		date._offset = moment(date).tz(sparrow.sys_defaults.time_zone)._offset;
		return sparrow.datetime.convert_to_system_tz(date);
	}
	setup_options(defaults) {
		var me = this;
		defaults.meridiem = "false";
		this.cal_options = {
			locale: sparrow.boot.user.language || "en",
			header: {
				left: "prev, title, next",
				right: "today, month, agendaWeek, agendaDay",
			},
			editable: true,
			selectable: true,
			selectHelper: true,
			forceEventDuration: true,
			displayEventTime: true,
			defaultView: defaults.defaultView,
			weekends: defaults.weekends,
			nowIndicator: true,
			buttonText: {
				today: __("Today"),
				month: __("Month"),
				week: __("Week"),
				day: __("Day"),
			},
			events: function (start, end, timezone, callback) {
				return sparrow.call({
					method: me.get_events_method || "sparrow.desk.calendar.get_events",
					type: "GET",
					args: me.get_args(start, end),
					callback: function (r) {
						var events = r.message || [];
						events = me.prepare_events(events);
						callback(events);
					},
				});
			},
			displayEventEnd: true,
			eventRender: function (event, element) {
				element.attr("title", event.tooltip);
			},
			eventClick: function (event) {
				// edit event description or delete
				var doctype = event.doctype || me.doctype;
				if (sparrow.model.can_read(doctype)) {
					sparrow.set_route("Form", doctype, event.name);
				}
			},
			eventDrop: function (event, delta, revertFunc) {
				me.update_event(event, revertFunc);
			},
			eventResize: function (event, delta, revertFunc) {
				me.update_event(event, revertFunc);
			},
			select: function (startDate, endDate, jsEvent, view) {
				if (view.name === "month" && endDate - startDate === 86400000) {
					// detect single day click in month view
					return;
				}

				var event = sparrow.model.get_new_doc(me.doctype);

				event[me.field_map.start] = me.get_system_datetime(startDate);

				if (me.field_map.end) event[me.field_map.end] = me.get_system_datetime(endDate);

				if (me.field_map.allDay) {
					var all_day = startDate._ambigTime && endDate._ambigTime ? 1 : 0;

					event[me.field_map.allDay] = all_day;

					if (all_day)
						event[me.field_map.end] = me.get_system_datetime(
							moment(endDate).subtract(1, "s")
						);
				}

				sparrow.set_route("Form", me.doctype, event.name);
			},
			dayClick: function (date, jsEvent, view) {
				if (view.name === "month") {
					const $date_cell = $("td[data-date=" + date.format("YYYY-MM-DD") + "]");

					if ($date_cell.hasClass("date-clicked")) {
						me.$cal.fullCalendar("changeView", "agendaDay");
						me.$cal.fullCalendar("gotoDate", date);
						me.$wrapper.find(".date-clicked").removeClass("date-clicked");

						// update "active view" btn
						me.$wrapper.find(".fc-month-button").removeClass("active");
						me.$wrapper.find(".fc-agendaDay-button").addClass("active");
					}

					me.$wrapper.find(".date-clicked").removeClass("date-clicked");
					$date_cell.addClass("date-clicked");
				}
				return false;
			},
		};

		if (this.options) {
			$.extend(this.cal_options, this.options);
		}
	}
	get_args(start, end) {
		var args = {
			doctype: this.doctype,
			start: this.get_system_datetime(start),
			end: this.get_system_datetime(end),
			fields: this.fields,
			filters: this.list_view.filter_area.get(),
			field_map: this.field_map,
		};
		return args;
	}
	refresh() {
		this.$cal.fullCalendar("refetchEvents");
	}
	prepare_events(events) {
		var me = this;

		return (events || []).map((d) => {
			d.id = d.name;
			d.editable = sparrow.model.can_write(d.doctype || me.doctype);

			// do not allow submitted/cancelled events to be moved / extended
			if (d.docstatus && d.docstatus > 0) {
				d.editable = false;
			}

			$.each(me.field_map, function (target, source) {
				d[target] = d[source];
			});

			if (!me.field_map.allDay) d.allDay = 1;
			if (!me.field_map.convertToUserTz) d.convertToUserTz = 1;

			// convert to user tz
			if (d.convertToUserTz) {
				d.start = sparrow.datetime.convert_to_user_tz(d.start);
				d.end = sparrow.datetime.convert_to_user_tz(d.end);
			}

			// show event on single day if start or end date is invalid
			if (!sparrow.datetime.validate(d.start) && d.end) {
				d.start = sparrow.datetime.add_days(d.end, -1);
			}

			if (d.start && !sparrow.datetime.validate(d.end)) {
				d.end = sparrow.datetime.add_days(d.start, 1);
			}

			me.fix_end_date_for_event_render(d);
			me.prepare_colors(d);

			d.title = sparrow.utils.html2text(d.title);

			return d;
		});
	}
	prepare_colors(d) {
		let color, color_name;
		if (this.get_css_class) {
			color_name = this.color_map[this.get_css_class(d)] || "blue";

			if (color_name.startsWith("#")) {
				color_name = sparrow.ui.color.validate_hex(color_name) ? color_name : "blue";
			}

			d.backgroundColor = sparrow.ui.color.get(color_name, "extra-light");
			d.textColor = sparrow.ui.color.get(color_name, "dark");
		} else {
			color = d.color;
			if (!sparrow.ui.color.validate_hex(color) || !color) {
				color = sparrow.ui.color.get("blue", "extra-light");
			}
			d.backgroundColor = color;
			d.textColor = sparrow.ui.color.get_contrast_color(color);
		}
		return d;
	}
	update_event(event, revertFunc) {
		var me = this;
		sparrow.model.remove_from_locals(me.doctype, event.name);
		return sparrow.call({
			method: me.update_event_method || "sparrow.desk.calendar.update_event",
			args: me.get_update_args(event),
			callback: function (r) {
				if (r.exc) {
					sparrow.show_alert(__("Unable to update event"));
					revertFunc();
				}
			},
			error: function () {
				revertFunc();
			},
		});
	}
	get_update_args(event) {
		var me = this;
		var args = {
			name: event[this.field_map.id],
		};

		args[this.field_map.start] = me.get_system_datetime(event.start);

		if (this.field_map.allDay)
			args[this.field_map.allDay] = event.start._ambigTime && event.end._ambigTime ? 1 : 0;

		if (this.field_map.end) {
			if (!event.end) {
				event.end = event.start.add(1, "hour");
			}

			args[this.field_map.end] = me.get_system_datetime(event.end);

			if (args[this.field_map.allDay]) {
				args[this.field_map.end] = me.get_system_datetime(
					moment(event.end).subtract(1, "s")
				);
			}
		}

		args.doctype = event.doctype || this.doctype;

		return { args: args, field_map: this.field_map };
	}

	fix_end_date_for_event_render(event) {
		if (event.allDay) {
			// We use inclusive end dates. This workaround fixes the rendering of events
			event.start = event.start ? $.fullCalendar.moment(event.start).stripTime() : null;
			event.end = event.end
				? $.fullCalendar.moment(event.end).add(1, "day").stripTime()
				: null;
		}
	}
};
