import "../lib/posthog.js";

class TelemetryManager {
	constructor() {
		this.enabled = false;

		this.project_id = sparrow.boot.posthog_project_id;
		this.telemetry_host = sparrow.boot.posthog_host;
		this.site_age = sparrow.boot.telemetry_site_age;

		if (cint(sparrow.boot.enable_telemetry) && this.project_id && this.telemetry_host) {
			this.enabled = true;
		}
	}

	initialize() {
		if (!this.enabled) return;
		try {
			posthog.init(this.project_id, {
				api_host: this.telemetry_host,
				autocapture: false,
				capture_pageview: false,
				capture_pageleave: false,
				advanced_disable_decide: true,
			});
			posthog.identify(sparrow.boot.sitename);
			this.send_heartbeat();
			this.register_pageview_handler();
		} catch (e) {
			console.trace("Failed to initialize telemetry", e);
			this.enabled = false;
		}
	}

	capture(event, app, props) {
		if (!this.enabled) return;
		posthog.capture(`${app}_${event}`, props);
	}

	disable() {
		this.enabled = false;
		posthog.opt_out_capturing();
	}

	send_heartbeat() {
		const KEY = "ph_last_heartbeat";
		const now = sparrow.datetime.system_datetime(true);
		const last = localStorage.getItem(KEY);

		if (!last || moment(now).diff(moment(last), "hours") > 12) {
			localStorage.setItem(KEY, now.toISOString());
			this.capture("heartbeat", "sparrow", { frappe_version: sparrow.boot?.versions?.sparrow });
		}
	}

	register_pageview_handler() {
		if (this.site_age && this.site_age > 5) {
			return;
		}

		sparrow.router.on("change", () => {
			posthog.capture("$pageview");
		});
	}
}

sparrow.telemetry = new TelemetryManager();
sparrow.telemetry.initialize();
