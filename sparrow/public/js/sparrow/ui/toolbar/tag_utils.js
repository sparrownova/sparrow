// Copyright (c) 2019, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.tags");

sparrow.tags.utils = {
	get_tags: function (txt) {
		txt = txt.slice(1);
		let out = [];

		if (!sparrow.tags.tags) {
			sparrow.tags.utils.fetch_tags();
			return [];
		}

		for (let i in sparrow.tags.tags) {
			let tag = sparrow.tags.tags[i];
			let level = sparrow.search.utils.fuzzy_search(txt, tag);
			if (level) {
				out.push({
					type: "Tag",
					label: __("#{0}", [sparrow.search.utils.bolden_match_part(__(tag), txt)]),
					value: __("#{0}", [__(tag)]),
					index: 1 + level,
					match: tag,
					onclick() {
						// Use Global Search Dialog for tag search too.
						sparrow.searchdialog.search.init_search("#".concat(tag), "tags");
					},
				});
			}
		}

		return out;
	},

	fetch_tags() {
		sparrow.call({
			method: "sparrow.desk.doctype.tag.tag.get_tags_list_for_awesomebar",
			callback: function (r) {
				if (r && r.message) {
					sparrow.tags.tags = $.extend([], r.message);
				}
			},
		});
	},

	get_tag_results: function (tag) {
		function get_results_sets(data) {
			var results_sets = [],
				result,
				set;
			function get_existing_set(doctype) {
				return results_sets.find(function (set) {
					return set.title === doctype;
				});
			}

			function make_description(content) {
				var field_length = 110;
				var field_value = null;
				if (content.length > field_length) {
					field_value = content.slice(0, field_length) + "...";
				} else {
					var length = content.length;
					field_value = content.slice(0, length) + "...";
				}
				return field_value;
			}

			data.forEach(function (d) {
				// more properties
				var description = "";
				if (d.content) {
					description = make_description(d.content);
				}
				result = {
					label: d.name,
					value: d.name,
					description: description,
					route: ["Form", d.doctype, d.name],
				};
				set = get_existing_set(d.doctype);
				if (set) {
					set.results.push(result);
				} else {
					set = {
						title: d.doctype,
						results: [result],
						fetch_type: "Global",
					};
					results_sets.push(set);
				}
			});
			return results_sets;
		}
		return new Promise(function (resolve) {
			sparrow.call({
				method: "sparrow.desk.doctype.tag.tag.get_documents_for_tag",
				args: {
					tag: tag,
				},
				callback: function (r) {
					if (r.message) {
						resolve(get_results_sets(r.message));
					} else {
						resolve([]);
					}
				},
			});
		});
	},
};
