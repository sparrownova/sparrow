import { io } from "socket.io-client";
sparrow.socketio = {
	open_tasks: {},
	open_docs: [],
	emit_queue: [],

	init: function (port = 3000) {
		if (sparrow.boot.disable_async) {
			return;
		}

		if (sparrow.socketio.socket) {
			return;
		}

		// Enable secure option when using HTTPS
		if (window.location.protocol == "https:") {
			sparrow.socketio.socket = io.connect(sparrow.socketio.get_host(port), {
				secure: true,
				withCredentials: true,
				reconnectionAttempts: 3,
			});
		} else if (window.location.protocol == "http:") {
			sparrow.socketio.socket = io.connect(sparrow.socketio.get_host(port), {
				withCredentials: true,
				reconnectionAttempts: 3,
			});
		}

		if (!sparrow.socketio.socket) {
			console.log("Unable to connect to " + sparrow.socketio.get_host(port));
			return;
		}

		sparrow.socketio.socket.on("msgprint", function (message) {
			sparrow.msgprint(message);
		});

		sparrow.socketio.socket.on("progress", function (data) {
			if (data.progress) {
				data.percent = (flt(data.progress[0]) / data.progress[1]) * 100;
			}
			if (data.percent) {
				sparrow.show_progress(
					data.title || __("Progress"),
					data.percent,
					100,
					data.description,
					true
				);
			}
		});

		sparrow.socketio.setup_listeners();
		sparrow.socketio.setup_reconnect();

		$(document).on("form-load form-rename", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			for (var i = 0, l = sparrow.socketio.open_docs.length; i < l; i++) {
				var d = sparrow.socketio.open_docs[i];
				if (frm.doctype == d.doctype && frm.docname == d.name) {
					// already subscribed
					return false;
				}
			}

			sparrow.socketio.doc_subscribe(frm.doctype, frm.docname);
		});

		$(document).on("form-refresh", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			sparrow.socketio.doc_open(frm.doctype, frm.docname);
		});

		$(document).on("form-unload", function (e, frm) {
			if (!frm.doc || frm.is_new()) {
				return;
			}

			// sparrow.socketio.doc_unsubscribe(frm.doctype, frm.docname);
			sparrow.socketio.doc_close(frm.doctype, frm.docname);
		});

		$(document).on("form-typing", function (e, frm) {
			sparrow.socketio.form_typing(frm.doctype, frm.docname);
		});

		$(document).on("form-stopped-typing", function (e, frm) {
			sparrow.socketio.form_stopped_typing(frm.doctype, frm.docname);
		});

		window.addEventListener("beforeunload", () => {
			if (!cur_frm || !cur_frm.doc || cur_frm.is_new()) {
				return;
			}

			sparrow.socketio.doc_close(cur_frm.doctype, cur_frm.docname);
		});
	},
	get_host: function (port = 3000) {
		var host = window.location.origin;
		if (window.dev_server) {
			var parts = host.split(":");
			port = sparrow.boot.socketio_port || port.toString() || "3000";
			if (parts.length > 2) {
				host = parts[0] + ":" + parts[1];
			}
			host = host + ":" + port;
		}
		return host;
	},
	subscribe: function (task_id, opts) {
		// TODO DEPRECATE

		sparrow.socketio.socket.emit("task_subscribe", task_id);
		sparrow.socketio.socket.emit("progress_subscribe", task_id);

		sparrow.socketio.open_tasks[task_id] = opts;
	},
	task_subscribe: function (task_id) {
		sparrow.socketio.socket.emit("task_subscribe", task_id);
	},
	task_unsubscribe: function (task_id) {
		sparrow.socketio.socket.emit("task_unsubscribe", task_id);
	},
	doctype_subscribe: function (doctype) {
		sparrow.socketio.socket.emit("doctype_subscribe", doctype);
	},
	doctype_unsubscribe: function (doctype) {
		sparrow.socketio.socket.emit("doctype_unsubscribe", doctype);
	},
	doc_subscribe: function (doctype, docname) {
		if (sparrow.flags.doc_subscribe) {
			console.log("throttled");
			return;
		}

		sparrow.flags.doc_subscribe = true;

		// throttle to 1 per sec
		setTimeout(function () {
			sparrow.flags.doc_subscribe = false;
		}, 1000);

		sparrow.socketio.socket.emit("doc_subscribe", doctype, docname);
		sparrow.socketio.open_docs.push({ doctype: doctype, docname: docname });
	},
	doc_unsubscribe: function (doctype, docname) {
		sparrow.socketio.socket.emit("doc_unsubscribe", doctype, docname);
		sparrow.socketio.open_docs = $.filter(sparrow.socketio.open_docs, function (d) {
			if (d.doctype === doctype && d.name === docname) {
				return null;
			} else {
				return d;
			}
		});
	},
	doc_open: function (doctype, docname) {
		// notify that the user has opened this doc, if not already notified
		if (
			!sparrow.socketio.last_doc ||
			sparrow.socketio.last_doc[0] != doctype ||
			sparrow.socketio.last_doc[1] != docname
		) {
			sparrow.socketio.socket.emit("doc_open", doctype, docname);

			sparrow.socketio.last_doc &&
				sparrow.socketio.doc_close(
					sparrow.socketio.last_doc[0],
					sparrow.socketio.last_doc[1]
				);
		}
		sparrow.socketio.last_doc = [doctype, docname];
	},
	doc_close: function (doctype, docname) {
		// notify that the user has closed this doc
		sparrow.socketio.socket.emit("doc_close", doctype, docname);

		// if the doc is closed the user has also stopped typing
		sparrow.socketio.socket.emit("doc_typing_stopped", doctype, docname);
	},
	form_typing: function (doctype, docname) {
		// notifiy that the user is typing on the doc
		sparrow.socketio.socket.emit("doc_typing", doctype, docname);
	},
	form_stopped_typing: function (doctype, docname) {
		// notifiy that the user has stopped typing
		sparrow.socketio.socket.emit("doc_typing_stopped", doctype, docname);
	},
	setup_listeners: function () {
		sparrow.socketio.socket.on("task_status_change", function (data) {
			sparrow.socketio.process_response(data, data.status.toLowerCase());
		});
		sparrow.socketio.socket.on("task_progress", function (data) {
			sparrow.socketio.process_response(data, "progress");
		});
	},
	setup_reconnect: function () {
		// subscribe again to open_tasks
		sparrow.socketio.socket.on("connect", function () {
			// wait for 5 seconds before subscribing again
			// because it takes more time to start python server than nodejs server
			// and we use validation requests to python server for subscribing
			setTimeout(function () {
				$.each(sparrow.socketio.open_tasks, function (task_id, opts) {
					sparrow.socketio.subscribe(task_id, opts);
				});

				// re-connect open docs
				$.each(sparrow.socketio.open_docs, function (d) {
					if (locals[d.doctype] && locals[d.doctype][d.name]) {
						sparrow.socketio.doc_subscribe(d.doctype, d.name);
					}
				});

				if (cur_frm && cur_frm.doc && !cur_frm.is_new()) {
					sparrow.socketio.doc_open(cur_frm.doc.doctype, cur_frm.doc.name);
				}
			}, 5000);
		});
	},
	process_response: function (data, method) {
		if (!data) {
			return;
		}

		// success
		var opts = sparrow.socketio.open_tasks[data.task_id];
		if (opts[method]) {
			opts[method](data);
		}

		// "callback" is std sparrow term
		if (method === "success") {
			if (opts.callback) opts.callback(data);
		}

		// always
		sparrow.request.cleanup(opts, data);
		if (opts.always) {
			opts.always(data);
		}

		// error
		if (data.status_code && data.status_code > 400 && opts.error) {
			opts.error(data);
		}
	},
};

sparrow.provide("sparrow.realtime");
sparrow.realtime.on = function (event, callback) {
	sparrow.socketio.socket && sparrow.socketio.socket.on(event, callback);
};

sparrow.realtime.off = function (event, callback) {
	sparrow.socketio.socket && sparrow.socketio.socket.off(event, callback);
};

sparrow.realtime.publish = function (event, message) {
	if (sparrow.socketio.socket) {
		sparrow.socketio.socket.emit(event, message);
	}
};
