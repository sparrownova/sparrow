// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// My HTTP Request

sparrow.provide("sparrow.request");
sparrow.provide("sparrow.request.error_handlers");
sparrow.request.url = "/";
sparrow.request.ajax_count = 0;
sparrow.request.waiting_for_ajax = [];
sparrow.request.logs = {};

sparrow.xcall = function (method, params) {
	return new Promise((resolve, reject) => {
		sparrow.call({
			method: method,
			args: params,
			callback: (r) => {
				resolve(r.message);
			},
			error: (r) => {
				reject(r.message);
			},
		});
	});
};

// generic server call (call page, object)
sparrow.call = function (opts) {
	if (!sparrow.is_online()) {
		sparrow.show_alert(
			{
				indicator: "orange",
				message: __("Connection Lost"),
				subtitle: __("You are not connected to Internet. Retry after sometime."),
			},
			3
		);
		opts.always && opts.always();
		return $.ajax();
	}
	if (typeof arguments[0] === "string") {
		opts = {
			method: arguments[0],
			args: arguments[1],
			callback: arguments[2],
			headers: arguments[3],
		};
	}

	if (opts.quiet) {
		opts.no_spinner = true;
	}
	var args = $.extend({}, opts.args);

	if (args.freeze) {
		opts.freeze = opts.freeze || args.freeze;
		opts.freeze_message = opts.freeze_message || args.freeze_message;
	}

	// cmd
	if (opts.module && opts.page) {
		args.cmd = opts.module + ".page." + opts.page + "." + opts.page + "." + opts.method;
	} else if (opts.doc) {
		$.extend(args, {
			cmd: "run_doc_method",
			docs: sparrow.get_doc(opts.doc.doctype, opts.doc.name),
			method: opts.method,
			args: opts.args,
		});
	} else if (opts.method) {
		args.cmd = opts.method;
	}

	var callback = function (data, response_text) {
		if (data.task_id) {
			// async call, subscribe
			sparrow.socketio.subscribe(data.task_id, opts);

			if (opts.queued) {
				opts.queued(data);
			}
		} else if (opts.callback) {
			// ajax
			return opts.callback(data, response_text);
		}
	};

	let url = opts.url;
	if (!url) {
		url = "/api/method/" + args.cmd;
		if (window.cordova) {
			let host = sparrow.request.url;
			host = host.slice(0, host.length - 1);
			url = host + url;
		}
		delete args.cmd;
	}

	// debouce if required
	if (opts.debounce && sparrow.request.is_fresh(args, opts.debounce)) {
		return Promise.resolve();
	}

	return sparrow.request.call({
		type: opts.type || "POST",
		args: args,
		success: callback,
		error: opts.error,
		always: opts.always,
		btn: opts.btn,
		freeze: opts.freeze,
		freeze_message: opts.freeze_message,
		headers: opts.headers || {},
		error_handlers: opts.error_handlers || {},
		// show_spinner: !opts.no_spinner,
		async: opts.async,
		silent: opts.silent,
		url,
	});
};

sparrow.request.call = function (opts) {
	sparrow.request.prepare(opts);

	var statusCode = {
		200: function (data, xhr) {
			opts.success_callback && opts.success_callback(data, xhr.responseText);
		},
		401: function (xhr) {
			if (sparrow.app.session_expired_dialog && sparrow.app.session_expired_dialog.display) {
				sparrow.app.redirect_to_login();
			} else {
				sparrow.app.handle_session_expired();
			}
		},
		404: function (xhr) {
			sparrow.msgprint({
				title: __("Not found"),
				indicator: "red",
				message: __("The resource you are looking for is not available"),
			});
		},
		403: function (xhr) {
			if (sparrow.session.user === "Guest" && sparrow.session.logged_in_user !== "Guest") {
				// session expired
				sparrow.app.handle_session_expired();
			} else if (xhr.responseJSON && xhr.responseJSON._error_message) {
				sparrow.msgprint({
					title: __("Not permitted"),
					indicator: "red",
					message: xhr.responseJSON._error_message,
				});

				xhr.responseJSON._server_messages = null;
			} else if (xhr.responseJSON && xhr.responseJSON._server_messages) {
				var _server_messages = JSON.parse(xhr.responseJSON._server_messages);

				// avoid double messages
				if (_server_messages.indexOf(__("Not permitted")) !== -1) {
					return;
				}
			} else {
				sparrow.msgprint({
					title: __("Not permitted"),
					indicator: "red",
					message: __(
						"You do not have enough permissions to access this resource. Please contact your manager to get access."
					),
				});
			}
		},
		508: function (xhr) {
			sparrow.utils.play_sound("error");
			sparrow.msgprint({
				title: __("Please try again"),
				indicator: "red",
				message: __(
					"Another transaction is blocking this one. Please try again in a few seconds."
				),
			});
		},
		413: function (data, xhr) {
			sparrow.msgprint({
				indicator: "red",
				title: __("File too big"),
				message: __("File size exceeded the maximum allowed size of {0} MB", [
					(sparrow.boot.max_file_size || 5242880) / 1048576,
				]),
			});
		},
		417: function (xhr) {
			var r = xhr.responseJSON;
			if (!r) {
				try {
					r = JSON.parse(xhr.responseText);
				} catch (e) {
					r = xhr.responseText;
				}
			}

			opts.error_callback && opts.error_callback(r);
		},
		501: function (data, xhr) {
			if (typeof data === "string") data = JSON.parse(data);
			opts.error_callback && opts.error_callback(data, xhr.responseText);
		},
		500: function (xhr) {
			sparrow.utils.play_sound("error");
			try {
				opts.error_callback && opts.error_callback();
				sparrow.request.report_error(xhr, opts);
			} catch (e) {
				sparrow.request.report_error(xhr, opts);
			}
		},
		504: function (xhr) {
			sparrow.msgprint(__("Request Timed Out"));
			opts.error_callback && opts.error_callback();
		},
		502: function (xhr) {
			sparrow.msgprint(__("Internal Server Error"));
		},
	};

	var exception_handlers = {
		QueryTimeoutError: function () {
			sparrow.utils.play_sound("error");
			sparrow.msgprint({
				title: __("Request Timeout"),
				indicator: "red",
				message: __("Server was too busy to process this request. Please try again."),
			});
		},
		QueryDeadlockError: function () {
			sparrow.utils.play_sound("error");
			sparrow.msgprint({
				title: __("Deadlock Occurred"),
				indicator: "red",
				message: __("Server was too busy to process this request. Please try again."),
			});
		},
	};

	var ajax_args = {
		url: opts.url || sparrow.request.url,
		data: opts.args,
		type: opts.type,
		dataType: opts.dataType || "json",
		async: opts.async,
		headers: Object.assign(
			{
				"X-Sparrow-CSRF-Token": sparrow.csrf_token,
				Accept: "application/json",
				"X-Sparrow-CMD": (opts.args && opts.args.cmd) || "" || "",
			},
			opts.headers
		),
		cache: false,
	};

	if (opts.args && opts.args.doctype) {
		ajax_args.headers["X-Sparrow-Doctype"] = encodeURIComponent(opts.args.doctype);
	}

	sparrow.last_request = ajax_args.data;

	return $.ajax(ajax_args)
		.done(function (data, textStatus, xhr) {
			try {
				if (typeof data === "string") data = JSON.parse(data);

				// sync attached docs
				if (data.docs || data.docinfo) {
					sparrow.model.sync(data);
				}

				// sync translated messages
				if (data.__messages) {
					$.extend(sparrow._messages, data.__messages);
				}

				// sync link titles
				if (data._link_titles) {
					if (!sparrow._link_titles) {
						sparrow._link_titles = {};
					}
					$.extend(sparrow._link_titles, data._link_titles);
				}

				// callbacks
				var status_code_handler = statusCode[xhr.statusCode().status];
				if (status_code_handler) {
					status_code_handler(data, xhr);
				}
			} catch (e) {
				console.log("Unable to handle success response", data); // eslint-disable-line
				console.error(e); // eslint-disable-line
			}
		})
		.always(function (data, textStatus, xhr) {
			try {
				if (typeof data === "string") {
					data = JSON.parse(data);
				}
				if (data.responseText) {
					var xhr = data;
					data = JSON.parse(data.responseText);
				}
			} catch (e) {
				data = null;
				// pass
			}
			sparrow.request.cleanup(opts, data);
			if (opts.always) {
				opts.always(data);
			}
		})
		.fail(function (xhr, textStatus) {
			try {
				if (
					xhr.getResponseHeader("content-type") == "application/json" &&
					xhr.responseText
				) {
					var data;
					try {
						data = JSON.parse(xhr.responseText);
					} catch (e) {
						console.log("Unable to parse reponse text");
						console.log(xhr.responseText);
						console.log(e);
					}
					if (data && data.exception) {
						// sparrow.exceptions.CustomError: (1024, ...) -> CustomError
						var exception = data.exception.split(".").at(-1).split(":").at(0);
						var exception_handler = exception_handlers[exception];
						if (exception_handler) {
							exception_handler(data);
							return;
						}
					}
				}
				var status_code_handler = statusCode[xhr.statusCode().status];
				if (status_code_handler) {
					status_code_handler(xhr);
					return;
				}
				// if not handled by error handler!
				opts.error_callback && opts.error_callback(xhr);
			} catch (e) {
				console.log("Unable to handle failed response"); // eslint-disable-line
				console.error(e); // eslint-disable-line
			}
		});
};

sparrow.request.is_fresh = function (args, threshold) {
	// return true if a request with similar args has been sent recently
	if (!sparrow.request.logs[args.cmd]) {
		sparrow.request.logs[args.cmd] = [];
	}

	for (let past_request of sparrow.request.logs[args.cmd]) {
		// check if request has same args and was made recently
		if (
			new Date() - past_request.timestamp < threshold &&
			sparrow.utils.deep_equal(args, past_request.args)
		) {
			// eslint-disable-next-line no-console
			console.log("throttled");
			return true;
		}
	}

	// log the request
	sparrow.request.logs[args.cmd].push({ args: args, timestamp: new Date() });
	return false;
};

// call execute serverside request
sparrow.request.prepare = function (opts) {
	$("body").attr("data-ajax-state", "triggered");

	// btn indicator
	if (opts.btn) $(opts.btn).prop("disabled", true);

	// freeze page
	if (opts.freeze) sparrow.dom.freeze(opts.freeze_message);

	// stringify args if required
	for (var key in opts.args) {
		if (opts.args[key] && ($.isPlainObject(opts.args[key]) || $.isArray(opts.args[key]))) {
			opts.args[key] = JSON.stringify(opts.args[key]);
		}
	}

	// no cmd?
	if (!opts.args.cmd && !opts.url) {
		console.log(opts);
		throw "Incomplete Request";
	}

	opts.success_callback = opts.success;
	opts.error_callback = opts.error;
	delete opts.success;
	delete opts.error;
};

sparrow.request.cleanup = function (opts, r) {
	// stop button indicator
	if (opts.btn) {
		$(opts.btn).prop("disabled", false);
	}

	$("body").attr("data-ajax-state", "complete");

	// un-freeze page
	if (opts.freeze) sparrow.dom.unfreeze();

	if (r) {
		// session expired? - Guest has no business here!
		if (
			r.session_expired ||
			(sparrow.session.user === "Guest" && sparrow.session.logged_in_user !== "Guest")
		) {
			sparrow.app.handle_session_expired();
			return;
		}

		// error handlers
		let global_handlers = sparrow.request.error_handlers[r.exc_type] || [];
		let request_handler = opts.error_handlers ? opts.error_handlers[r.exc_type] : null;
		let handlers = [].concat(global_handlers, request_handler).filter(Boolean);

		if (r.exc_type) {
			handlers.forEach((handler) => {
				handler(r);
			});
		}

		// show messages
		if (r._server_messages && !opts.silent) {
			// show server messages if no handlers exist
			if (handlers.length === 0) {
				r._server_messages = JSON.parse(r._server_messages);
				sparrow.hide_msgprint();
				sparrow.msgprint(r._server_messages);
			}
		}

		// show errors
		if (r.exc) {
			r.exc = JSON.parse(r.exc);
			if (r.exc instanceof Array) {
				r.exc.forEach((exc) => {
					if (exc) {
						console.error(exc);
					}
				});
			} else {
				console.error(r.exc);
			}
		}

		// debug messages
		if (r._debug_messages) {
			if (opts.args) {
				console.log("======== arguments ========");
				console.log(opts.args);
				console.log("========");
			}
			$.each(JSON.parse(r._debug_messages), function (i, v) {
				console.log(v);
			});
			console.log("======== response ========");
			delete r._debug_messages;
			console.log(r);
			console.log("========");
		}
	}

	sparrow.last_response = r;
};

sparrow.after_server_call = () => {
	if (sparrow.request.ajax_count) {
		return new Promise((resolve) => {
			sparrow.request.waiting_for_ajax.push(() => {
				resolve();
			});
		});
	} else {
		return null;
	}
};

sparrow.after_ajax = function (fn) {
	return new Promise((resolve) => {
		if (sparrow.request.ajax_count) {
			sparrow.request.waiting_for_ajax.push(() => {
				if (fn) return resolve(fn());
				resolve();
			});
		} else {
			if (fn) return resolve(fn());
			resolve();
		}
	});
};

sparrow.request.report_error = function (xhr, request_opts) {
	var data = JSON.parse(xhr.responseText);
	var exc;
	if (data.exc) {
		try {
			exc = (JSON.parse(data.exc) || []).join("\n");
		} catch (e) {
			exc = data.exc;
		}
		delete data.exc;
	} else {
		exc = "";
	}

	const copy_markdown_to_clipboard = () => {
		const code_block = (snippet) => "```\n" + snippet + "\n```";
		const traceback_info = [
			"### App Versions",
			code_block(JSON.stringify(sparrow.boot.versions, null, "\t")),
			"### Route",
			code_block(sparrow.get_route_str()),
			"### Traceback",
			code_block(exc),
			"### Request Data",
			code_block(JSON.stringify(request_opts, null, "\t")),
			"### Response Data",
			code_block(JSON.stringify(data, null, "\t")),
		].join("\n");
		sparrow.utils.copy_to_clipboard(traceback_info);
	};

	var show_communication = function () {
		var error_report_message = [
			"<h5>Please type some additional information that could help us reproduce this issue:</h5>",
			'<div style="min-height: 100px; border: 1px solid #bbb; \
				border-radius: 5px; padding: 15px; margin-bottom: 15px;"></div>',
			"<hr>",
			"<h5>App Versions</h5>",
			"<pre>" + JSON.stringify(sparrow.boot.versions, null, "\t") + "</pre>",
			"<h5>Route</h5>",
			"<pre>" + sparrow.get_route_str() + "</pre>",
			"<hr>",
			"<h5>Error Report</h5>",
			"<pre>" + exc + "</pre>",
			"<hr>",
			"<h5>Request Data</h5>",
			"<pre>" + JSON.stringify(request_opts, null, "\t") + "</pre>",
			"<hr>",
			"<h5>Response JSON</h5>",
			"<pre>" + JSON.stringify(data, null, "\t") + "</pre>",
		].join("\n");

		var communication_composer = new sparrow.views.CommunicationComposer({
			subject: "Error Report [" + sparrow.datetime.nowdate() + "]",
			recipients: error_report_email,
			message: error_report_message,
			doc: {
				doctype: "User",
				name: sparrow.session.user,
			},
		});
		communication_composer.dialog.$wrapper.css(
			"z-index",
			cint(sparrow.msg_dialog.$wrapper.css("z-index")) + 1
		);
	};

	if (exc) {
		var error_report_email = sparrow.boot.error_report_email;

		request_opts = sparrow.request.cleanup_request_opts(request_opts);

		// window.msg_dialog = sparrow.msgprint({message:error_message, indicator:'red', big: true});

		if (!sparrow.error_dialog) {
			sparrow.error_dialog = new sparrow.ui.Dialog({
				title: __("Server Error"),
				primary_action_label: __("Report"),
				primary_action: () => {
					if (error_report_email) {
						show_communication();
					} else {
						sparrow.msgprint(__("Support Email Address Not Specified"));
					}
					sparrow.error_dialog.hide();
				},
				secondary_action_label: __("Copy error to clipboard"),
				secondary_action: () => {
					copy_markdown_to_clipboard();
					sparrow.error_dialog.hide();
				},
			});
			sparrow.error_dialog.wrapper.classList.add("msgprint-dialog");
		}

		let parts = strip(exc).split("\n");

		sparrow.error_dialog.$body.html(parts[parts.length - 1]);
		sparrow.error_dialog.show();
	}
};

sparrow.request.cleanup_request_opts = function (request_opts) {
	var doc = (request_opts.args || {}).doc;
	if (doc) {
		doc = JSON.parse(doc);
		$.each(Object.keys(doc), function (i, key) {
			if (key.indexOf("password") !== -1 && doc[key]) {
				// mask the password
				doc[key] = "*****";
			}
		});
		request_opts.args.doc = JSON.stringify(doc);
	}
	return request_opts;
};

sparrow.request.on_error = function (error_type, handler) {
	sparrow.request.error_handlers[error_type] = sparrow.request.error_handlers[error_type] || [];
	sparrow.request.error_handlers[error_type].push(handler);
};

$(document).ajaxSend(function () {
	sparrow.request.ajax_count++;
});

$(document).ajaxComplete(function () {
	sparrow.request.ajax_count--;
	if (!sparrow.request.ajax_count) {
		$.each(sparrow.request.waiting_for_ajax || [], function (i, fn) {
			fn();
		});
		sparrow.request.waiting_for_ajax = [];
	}
});
