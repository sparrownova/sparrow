// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Google Drive", {
	refresh: function (frm) {
		if (!frm.doc.enable) {
			frm.dashboard.set_headline(
				__("To use Google Drive, enable {0}.", [
					`<a href='/app/google-settings'>${__("Google Settings")}</a>`,
				])
			);
		}

		sparrow.realtime.on("upload_to_google_drive", (data) => {
			if (data.progress) {
				frm.dashboard.show_progress(
					"Uploading to Google Drive",
					(data.progress / data.total) * 100,
					__("{0}", [data.message])
				);
				if (data.progress === data.total) {
					frm.dashboard.hide_progress("Uploading to Google Drive");
				}
			}
		});

		if (frm.doc.enable && frm.doc.refresh_token) {
			let sync_button = frm.add_custom_button(__("Take Backup"), function () {
				sparrow.show_alert({
					indicator: "green",
					message: __("Backing up to Google Drive."),
				});
				sparrow
					.call({
						method: "sparrow.integrations.doctype.google_drive.google_drive.take_backup",
						btn: sync_button,
					})
					.then((r) => {
						sparrow.msgprint(r.message);
					});
			});
		}

		if (frm.doc.enable && frm.doc.backup_folder_name && !frm.doc.refresh_token) {
			frm.dashboard.set_headline(
				__(
					"Click on <b>Authorize Google Drive Access</b> to authorize Google Drive Access."
				)
			);
		}

		if (frm.doc.enable && frm.doc.refresh_token && frm.doc.authorization_code) {
			frm.page.set_indicator("Authorized", "green");
		}
	},
	authorize_google_drive_access: function (frm) {
		sparrow.call({
			method: "sparrow.integrations.doctype.google_drive.google_drive.authorize_access",
			args: {
				reauthorize: frm.doc.authorization_code ? 1 : 0,
			},
			callback: function (r) {
				if (!r.exc) {
					frm.save();
					window.open(r.message.url);
				}
			},
		});
	},
});
