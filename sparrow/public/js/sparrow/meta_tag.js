sparrow.provide("sparrow.model");
sparrow.provide("sparrow.utils");

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
sparrow.utils.set_meta_tag = function (route) {
	sparrow.db.exists("Website Route Meta", route).then((exists) => {
		if (exists) {
			sparrow.set_route("Form", "Website Route Meta", route);
		} else {
			// new doc
			const doc = sparrow.model.get_new_doc("Website Route Meta");
			doc.__newname = route;
			sparrow.set_route("Form", doc.doctype, doc.name);
		}
	});
};
