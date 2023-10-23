// Copyright (c) 2015, Sparrownova Technologies and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

sparrow.start_app = function () {
	if (!sparrow.Application) return;
	sparrow.assets.check();
	sparrow.provide("sparrow.app");
	sparrow.provide("sparrow.desk");
	sparrow.app = new sparrow.Application();
};

$(document).ready(function () {
	if (!sparrow.utils.supportsES6) {
		sparrow.msgprint({
			indicator: "red",
			title: __("Browser not supported"),
			message: __(
				"Some of the features might not work in your browser. Please update your browser to the latest version."
			),
		});
	}
	sparrow.start_app();
});

sparrow.Application = class Application {
	constructor() {
		this.startup();
	}

	startup() {
		sparrow.socketio.init();
		sparrow.model.init();

		this.setup_sparrow_vue();
		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.set_favicon();
		this.setup_analytics();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();

		sparrow.ui.keys.setup();

		sparrow.ui.keys.add_shortcut({
			shortcut: "shift+ctrl+g",
			description: __("Switch Theme"),
			action: () => {
				if (sparrow.theme_switcher && sparrow.theme_switcher.dialog.is_visible) {
					sparrow.theme_switcher.hide();
				} else {
					sparrow.theme_switcher = new sparrow.ui.ThemeSwitcher();
					sparrow.theme_switcher.show();
				}
			},
		});

		sparrow.ui.add_system_theme_switch_listener();
		const root = document.documentElement;

		const observer = new MutationObserver(() => {
			sparrow.ui.set_theme();
		});
		observer.observe(root, {
			attributes: true,
			attributeFilter: ["data-theme-mode"],
		});

		sparrow.ui.set_theme();

		// page container
		this.make_page_container();
		if (
			!window.Cypress &&
			sparrow.boot.onboarding_tours &&
			sparrow.boot.user.onboarding_status != null
		) {
			let pending_tours = !sparrow.boot.onboarding_tours.every(
				(tour) => sparrow.boot.user.onboarding_status[tour[0]]?.is_complete
			);
			if (pending_tours && sparrow.boot.onboarding_tours.length > 0) {
				sparrow.require("onboarding_tours.bundle.js", () => {
					sparrow.utils.sleep(1000).then(() => {
						sparrow.ui.init_onboarding_tour();
					});
				});
			}
		}
		this.set_route();

		// trigger app startup
		$(document).trigger("startup");

		$(document).trigger("app_ready");

		if (sparrow.boot.messages) {
			sparrow.msgprint(sparrow.boot.messages);
		}

		if (sparrow.user_roles.includes("System Manager")) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!sparrow.boot.developer_mode) {
			let console_security_message = __(
				"Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand."
			);
			console.log(`%c${console_security_message}`, "font-size: large");
		}

		this.show_notes();

		if (sparrow.ui.startup_setup_dialog && !sparrow.boot.setup_complete) {
			sparrow.ui.startup_setup_dialog.pre_show();
			sparrow.ui.startup_setup_dialog.show();
		}

		sparrow.realtime.on("version-update", function () {
			var dialog = sparrow.msgprint({
				message: __(
					"The application has been updated to a new version, please refresh this page"
				),
				indicator: "green",
				title: __("Version Updated"),
			});
			dialog.set_primary_action(__("Refresh"), function () {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});

		// listen to build errors
		this.setup_build_events();

		if (sparrow.sys_defaults.email_user_password) {
			var email_list = sparrow.sys_defaults.email_user_password.split(",");
			for (var u in email_list) {
				if (email_list[u] === sparrow.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new sparrow.ui.LinkPreview();
	}

	set_route() {
		if (sparrow.boot && localStorage.getItem("session_last_route")) {
			sparrow.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			sparrow.router.route();
		}
		sparrow.router.on("change", () => {
			$(".tooltip").hide();
		});
	}

	setup_sparrow_vue() {
		Vue.prototype.__ = window.__;
		Vue.prototype.sparrow = window.sparrow;
	}

	set_password(user) {
		var me = this;
		sparrow.call({
			method: "sparrow.core.doctype.user.user.get_email_awaiting",
			args: {
				user: user,
			},
			callback: function (email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt(email_account, user, i);
					}
				}
			},
		});
	}

	email_password_prompt(email_account, user, i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new sparrow.ui.Dialog({
			title: __("Password missing in Email Account"),
			fields: [
				{
					fieldname: "password",
					fieldtype: "Password",
					label: __(
						"Please enter the password for: <b>{0}</b>",
						[email_id],
						"Email Account"
					),
					reqd: 1,
				},
				{
					fieldname: "submit",
					fieldtype: "Button",
					label: __("Submit", null, "Submit password for Email Account"),
				},
			],
		});
		d.get_input("submit").on("click", function () {
			//setup spinner
			d.hide();
			var s = new sparrow.ui.Dialog({
				title: __("Checking one moment"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "checking",
					},
				],
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			sparrow.call({
				method: "sparrow.email.doctype.email_account.email_account.set_email_password",
				args: {
					email_account: email_account[i]["email_account"],
					password: d.get_value("password"),
				},
				callback: function (passed) {
					s.hide();
					d.hide(); //hide waiting indication
					if (!passed["message"]) {
						sparrow.show_alert(
							{ message: __("Login Failed please try again"), indicator: "error" },
							5
						);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}
				},
			});
		});
		d.show();
	}
	load_bootinfo() {
		if (sparrow.boot) {
			this.setup_workspaces();
			sparrow.model.sync(sparrow.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			sparrow.router.setup();
			this.setup_moment();
			if (sparrow.boot.print_css) {
				sparrow.dom.set_style(sparrow.boot.print_css, "print-style");
			}
			sparrow.user.name = sparrow.boot.user.name;
			sparrow.router.setup();
		} else {
			this.set_as_guest();
		}
	}

	setup_workspaces() {
		sparrow.modules = {};
		sparrow.workspaces = {};
		for (let page of sparrow.boot.allowed_workspaces || []) {
			sparrow.modules[page.module] = page;
			sparrow.workspaces[sparrow.router.slug(page.name)] = page;
		}
	}

	load_user_permissions() {
		sparrow.defaults.load_user_permission_from_boot();

		sparrow.realtime.on(
			"update_user_permissions",
			sparrow.utils.debounce(() => {
				sparrow.defaults.update_user_permissions();
			}, 500)
		);
	}

	check_metadata_cache_status() {
		if (sparrow.boot.metadata_version != localStorage.metadata_version) {
			sparrow.assets.clear_local_storage();
			sparrow.assets.init_local_storage();
		}
	}

	set_globals() {
		sparrow.session.user = sparrow.boot.user.name;
		sparrow.session.logged_in_user = sparrow.boot.user.name;
		sparrow.session.user_email = sparrow.boot.user.email;
		sparrow.session.user_fullname = sparrow.user_info().fullname;

		sparrow.user_defaults = sparrow.boot.user.defaults;
		sparrow.user_roles = sparrow.boot.user.roles;
		sparrow.sys_defaults = sparrow.boot.sysdefaults;

		sparrow.ui.py_date_format = sparrow.boot.sysdefaults.date_format
			.replace("dd", "%d")
			.replace("mm", "%m")
			.replace("yyyy", "%Y");
		sparrow.boot.user.last_selected_values = {};

		// Proxy for user globals
		Object.defineProperties(window, {
			user: {
				get: function () {
					console.warn(
						"Please use `sparrow.session.user` instead of `user`. It will be deprecated soon."
					);
					return sparrow.session.user;
				},
			},
			user_fullname: {
				get: function () {
					console.warn(
						"Please use `sparrow.session.user_fullname` instead of `user_fullname`. It will be deprecated soon."
					);
					return sparrow.session.user;
				},
			},
			user_email: {
				get: function () {
					console.warn(
						"Please use `sparrow.session.user_email` instead of `user_email`. It will be deprecated soon."
					);
					return sparrow.session.user_email;
				},
			},
			user_defaults: {
				get: function () {
					console.warn(
						"Please use `sparrow.user_defaults` instead of `user_defaults`. It will be deprecated soon."
					);
					return sparrow.user_defaults;
				},
			},
			roles: {
				get: function () {
					console.warn(
						"Please use `sparrow.user_roles` instead of `roles`. It will be deprecated soon."
					);
					return sparrow.user_roles;
				},
			},
			sys_defaults: {
				get: function () {
					console.warn(
						"Please use `sparrow.sys_defaults` instead of `sys_defaults`. It will be deprecated soon."
					);
					return sparrow.user_roles;
				},
			},
		});
	}
	sync_pages() {
		// clear cached pages if timestamp is not found
		if (localStorage["page_info"]) {
			sparrow.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(sparrow.boot.page_info, function (name, p) {
				if (!page_info[name] || page_info[name].modified != p.modified) {
					delete localStorage["_page:" + name];
				}
				sparrow.boot.allowed_pages.push(name);
			});
		} else {
			sparrow.boot.allowed_pages = Object.keys(sparrow.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(sparrow.boot.page_info);
	}
	set_as_guest() {
		sparrow.session.user = "Guest";
		sparrow.session.user_email = "";
		sparrow.session.user_fullname = "Guest";

		sparrow.user_defaults = {};
		sparrow.user_roles = ["Guest"];
		sparrow.sys_defaults = {};
	}
	make_page_container() {
		if ($("#body").length) {
			$(".splash").remove();
			sparrow.temp_container = $("<div id='temp-container' style='display: none;'>").appendTo(
				"body"
			);
			sparrow.container = new sparrow.views.Container();
		}
	}
	make_nav_bar() {
		// toolbar
		if (sparrow.boot && sparrow.boot.home_page !== "setup-wizard") {
			sparrow.sparrow_toolbar = new sparrow.ui.toolbar.Toolbar();
		}
	}
	logout() {
		var me = this;
		me.logged_out = true;
		return sparrow.call({
			method: "logout",
			callback: function (r) {
				if (r.exc) {
					return;
				}
				me.redirect_to_login();
			},
		});
	}
	handle_session_expired() {
		if (!sparrow.app.session_expired_dialog) {
			var dialog = new sparrow.ui.Dialog({
				title: __("Session Expired"),
				keep_open: true,
				fields: [
					{
						fieldtype: "Password",
						fieldname: "password",
						label: __("Please Enter Your Password to Continue"),
					},
				],
				onhide: () => {
					if (!dialog.logged_in) {
						sparrow.app.redirect_to_login();
					}
				},
			});
			dialog.get_field("password").disable_password_checks();
			dialog.set_primary_action(__("Login"), () => {
				dialog.set_message(__("Authenticating..."));
				sparrow.call({
					method: "login",
					args: {
						usr: sparrow.session.user,
						pwd: dialog.get_values().password,
					},
					callback: (r) => {
						if (r.message === "Logged In") {
							dialog.logged_in = true;

							// revert backdrop
							$(".modal-backdrop").css({
								opacity: "",
								"background-color": "#334143",
							});
						}
						dialog.hide();
					},
					statusCode: () => {
						dialog.hide();
					},
				});
			});
			sparrow.app.session_expired_dialog = dialog;
		}
		if (!sparrow.app.session_expired_dialog.display) {
			sparrow.app.session_expired_dialog.show();
			// add backdrop
			$(".modal-backdrop").css({
				opacity: 1,
				"background-color": "#4B4C9D",
			});
		}
	}
	redirect_to_login() {
		window.location.href = "/";
	}
	set_favicon() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	}
	trigger_primary_action() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(":visible")) {
				cur_frm.page.btn_primary.trigger("click");
			} else if (sparrow.container.page.save_action) {
				sparrow.container.page.save_action();
			}
		}, 100);
	}

	show_change_log() {
		var me = this;
		let change_log = sparrow.boot.change_log;

		// sparrow.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "Shopper",
		// 	"version": "12.2.0"
		// }];

		if (
			!Array.isArray(change_log) ||
			!change_log.length ||
			window.Cypress ||
			cint(sparrow.boot.sysdefaults.disable_change_log_notification)
		) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = sparrow.msgprint({
			message: sparrow.render_template("change_log", { change_log: change_log }),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function () {
			sparrow.call({
				method: "sparrow.utils.change_log.update_last_known_versions",
			});
			me.show_notes();
		};
	}

	show_update_available() {
		if (sparrow.boot.sysdefaults.disable_system_update_notification) return;

		sparrow.call({
			method: "sparrow.utils.change_log.show_update_popup",
		});
	}

	setup_analytics() {
		if (window.mixpanel) {
			window.mixpanel.identify(sparrow.session.user);
			window.mixpanel.people.set({
				$first_name: sparrow.boot.user.first_name,
				$last_name: sparrow.boot.user.last_name,
				$created: sparrow.boot.user.creation,
				$email: sparrow.session.user,
			});
		}
	}

	add_browser_class() {
		$("html").addClass(sparrow.utils.get_browser().name.toLowerCase());
	}

	set_fullwidth_if_enabled() {
		sparrow.ui.toolbar.set_fullwidth_if_enabled();
	}

	show_notes() {
		var me = this;
		if (sparrow.boot.notes.length) {
			sparrow.boot.notes.forEach(function (note) {
				if (!note.seen || note.notify_on_every_login) {
					var d = sparrow.msgprint({ message: note.content, title: note.title });
					d.keep_open = true;
					d.custom_onhide = function () {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							sparrow.call({
								method: "sparrow.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name,
								},
							});
						}

						// next note
						me.show_notes();
					};
				}
			});
		}
	}

	setup_build_events() {
		if (sparrow.boot.developer_mode) {
			sparrow.require("build_events.bundle.js");
		}
	}

	setup_energy_point_listeners() {
		sparrow.realtime.on("energy_point_alert", (message) => {
			sparrow.show_alert(message);
		});
	}

	setup_copy_doc_listener() {
		$("body").on("paste", (e) => {
			try {
				let pasted_data = sparrow.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					const sleep = sparrow.utils.sleep;

					sparrow.dom.freeze(__("Creating {0}", [doc.doctype]) + "...");
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = sparrow.model.with_doctype(doc.doctype, () => {
							let newdoc = sparrow.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							sparrow.set_route("Form", newdoc.doctype, newdoc.name);
							sparrow.dom.unfreeze();
						});
						res && res.fail(sparrow.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	}

	setup_moment() {
		moment.updateLocale("en", {
			week: {
				dow: sparrow.datetime.get_first_day_of_the_week_index(),
			},
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (sparrow.boot.timezone_info) {
			moment.tz.add(sparrow.boot.timezone_info);
		}
	}
};

sparrow.get_module = function (m, default_module) {
	var module = sparrow.modules[m] || default_module;
	if (!module) {
		return;
	}

	if (module._setup) {
		return module;
	}

	if (!module.label) {
		module.label = m;
	}

	if (!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};
