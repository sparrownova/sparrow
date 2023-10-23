// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
sparrow._ = function (txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = "";

	let key = txt; // txt.replace(/\n/g, "");
	if (context) {
		translated_text = sparrow._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = sparrow._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = sparrow._;

sparrow.get_languages = function () {
	if (!sparrow.languages) {
		sparrow.languages = [];
		$.each(sparrow.boot.lang_dict, function (lang, value) {
			sparrow.languages.push({ label: lang, value: value });
		});
		sparrow.languages = sparrow.languages.sort(function (a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return sparrow.languages;
};
