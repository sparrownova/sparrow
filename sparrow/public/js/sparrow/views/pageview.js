// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.views.pageview");
sparrow.provide("sparrow.standard_pages");

sparrow.views.pageview = {
	with_page: function (name, callback) {
		if (sparrow.standard_pages[name]) {
			if (!sparrow.pages[name]) {
				sparrow.standard_pages[name]();
			}
			callback();
			return;
		}

		if (
			(locals.Page && locals.Page[name] && locals.Page[name].script) ||
			name == window.page_name
		) {
			// already loaded
			callback();
		} else if (localStorage["_page:" + name] && sparrow.boot.developer_mode != 1) {
			// cached in local storage
			sparrow.model.sync(JSON.parse(localStorage["_page:" + name]));
			callback();
		} else if (name) {
			// get fresh
			return sparrow.call({
				method: "sparrow.desk.desk_page.getpage",
				args: { name: name },
				callback: function (r) {
					if (!r.docs._dynamic_page) {
						localStorage["_page:" + name] = JSON.stringify(r.docs);
					}
					callback();
				},
				freeze: true,
			});
		}
	},

	show: function (name) {
		if (!name) {
			name = sparrow.boot ? sparrow.boot.home_page : window.page_name;
		}
		sparrow.model.with_doctype("Page", function () {
			sparrow.views.pageview.with_page(name, function (r) {
				if (r && r.exc) {
					if (!r["403"]) sparrow.show_not_found(name);
				} else if (!sparrow.pages[name]) {
					new sparrow.views.Page(name);
				}
				sparrow.container.change_to(name);
			});
		});
	},
};

sparrow.views.Page = class Page {
	constructor(name) {
		this.name = name;
		var me = this;

		// web home page
		if (name == window.page_name) {
			this.wrapper = document.getElementById("page-" + name);
			this.wrapper.label = document.title || window.page_name;
			this.wrapper.page_name = window.page_name;
			sparrow.pages[window.page_name] = this.wrapper;
		} else {
			this.pagedoc = locals.Page[this.name];
			if (!this.pagedoc) {
				sparrow.show_not_found(name);
				return;
			}
			this.wrapper = sparrow.container.add_page(this.name);
			this.wrapper.page_name = this.pagedoc.name;

			// set content, script and style
			if (this.pagedoc.content) this.wrapper.innerHTML = this.pagedoc.content;
			sparrow.dom.eval(this.pagedoc.__script || this.pagedoc.script || "");
			sparrow.dom.set_style(this.pagedoc.style || "");

			// set breadcrumbs
			sparrow.breadcrumbs.add(this.pagedoc.module || null);
		}

		this.trigger_page_event("on_page_load");

		// set events
		$(this.wrapper).on("show", function () {
			window.cur_frm = null;
			me.trigger_page_event("on_page_show");
			me.trigger_page_event("refresh");
		});
	}

	trigger_page_event(eventname) {
		var me = this;
		if (me.wrapper[eventname]) {
			me.wrapper[eventname](me.wrapper);
		}
	}
};

sparrow.show_not_found = function (page_name) {
	sparrow.show_message_page({
		page_name: page_name,
		message: __("Sorry! I could not find what you were looking for."),
		img: "/assets/sparrow/images/ui/bubble-tea-sorry.svg",
	});
};

sparrow.show_not_permitted = function (page_name) {
	sparrow.show_message_page({
		page_name: page_name,
		message: __("Sorry! You are not permitted to view this page."),
		img: "/assets/sparrow/images/ui/bubble-tea-sorry.svg",
		// icon: "octicon octicon-circle-slash"
	});
};

sparrow.show_message_page = function (opts) {
	// opts can include `page_name`, `message`, `icon` or `img`
	if (!opts.page_name) {
		opts.page_name = sparrow.get_route_str();
	}

	if (opts.icon) {
		opts.img = repl('<span class="%(icon)s message-page-icon"></span> ', opts);
	} else if (opts.img) {
		opts.img = repl('<img src="%(img)s" class="message-page-image">', opts);
	}

	var page = sparrow.pages[opts.page_name] || sparrow.container.add_page(opts.page_name);
	$(page).html(
		repl(
			'<div class="page message-page">\
			<div class="text-center message-page-content">\
				%(img)s\
				<p class="lead">%(message)s</p>\
				<a class="btn btn-default btn-sm btn-home" href="/app">%(home)s</a>\
			</div>\
		</div>',
			{
				img: opts.img || "",
				message: opts.message || "",
				home: __("Home"),
			}
		)
	);

	sparrow.container.change_to(opts.page_name);
};
