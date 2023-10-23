// Copyright (c) 2015, Sparrownova Technologies and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.help");

sparrow.help.youtube_id = {};

sparrow.help.has_help = function (doctype) {
	return sparrow.help.youtube_id[doctype];
};

sparrow.help.show = function (doctype) {
	if (sparrow.help.youtube_id[doctype]) {
		sparrow.help.show_video(sparrow.help.youtube_id[doctype]);
	}
};

sparrow.help.show_video = function (youtube_id, title) {
	if (sparrow.utils.is_url(youtube_id)) {
		const expression =
			'(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (sparrow.help_feedback_link || "")
	let dialog = new sparrow.ui.Dialog({
		title: title || __("Help"),
		size: "large",
	});

	let video = $(
		`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`
	);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr;
	sparrow.utils.load_video_player().then(() => {
		plyr = new sparrow.Plyr(video[0], {
			hideControls: true,
			resetOnEnd: true,
		});
	});

	dialog.onhide = () => {
		plyr?.destroy();
	};
};

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && sparrow.help.show(doctype);
});
