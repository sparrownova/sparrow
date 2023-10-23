sparrow.provide("sparrow.ui.misc");
sparrow.ui.misc.about = function () {
	if (!sparrow.ui.misc.about_dialog) {
		var d = new sparrow.ui.Dialog({ title: __("Sparrow Framework") });

		$(d.body).html(
			repl(
				"<div>\
		<p>" +
					__("Open Source Applications for the Web") +
					"</p>  \
		<p><i class='fa fa-globe fa-fw'></i>\
			Website: <a href='https://sparrownova.com' target='_blank'>https://sparrownova.com</a></p>\
		<p><i class='fa fa-github fa-fw'></i>\
			Source: <a href='https://github.com/sparrownova' target='_blank'>https://github.com/sparrownova</a></p>\
		<p><i class='fa fa-linkedin fa-fw'></i>\
			Linkedin: <a href='https://linkedin.com/company/sparrow-tech' target='_blank'>https://linkedin.com/company/sparrow-tech</a></p>\
		<p><i class='fa fa-facebook fa-fw'></i>\
			Facebook: <a href='https://facebook.com/shopper' target='_blank'>https://facebook.com/shopper</a></p>\
		<p><i class='fa fa-twitter fa-fw'></i>\
			Twitter: <a href='https://twitter.com/shopper' target='_blank'>https://twitter.com/shopper</a></p>\
		<hr>\
		<h4>Installed Apps</h4>\
		<div id='about-app-versions'>Loading versions...</div>\
		<hr>\
		<p class='text-muted'>&copy; Sparrownova Technologies and contributors </p> \
		</div>",
				sparrow.app
			)
		);

		sparrow.ui.misc.about_dialog = d;

		sparrow.ui.misc.about_dialog.on_page_show = function () {
			if (!sparrow.versions) {
				sparrow.call({
					method: "sparrow.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(sparrow.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				if (v.branch) {
					var text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					var text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			sparrow.versions = versions;
		};
	}

	sparrow.ui.misc.about_dialog.show();
};
