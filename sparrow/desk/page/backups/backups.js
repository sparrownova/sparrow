sparrow.pages["backups"].on_page_load = function (wrapper) {
	var page = sparrow.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		sparrow.set_route("Form", "System Settings");
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		sparrow.call({
			method: "sparrow.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: sparrow.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		if (sparrow.user.has_role("System Manager")) {
			sparrow.verify_password(function () {
				sparrow.call({
					method: "sparrow.utils.backups.get_backup_encryption_key",
					callback: function (r) {
						sparrow.msgprint({
							title: __("Backup Encryption Key"),
							message: __(r.message),
							indicator: "blue",
						});
					},
				});
			});
		} else {
			sparrow.msgprint({
				title: __("Error"),
				message: __("System Manager privileges required."),
				indicator: "red",
			});
		}
	});

	sparrow.breadcrumbs.add("Setup");

	$(sparrow.render_template("backups")).appendTo(page.body.addClass("no-border"));
};
