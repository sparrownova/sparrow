sparrow.route_history_queue = [];
const routes_to_skip = ["Form", "social", "setup-wizard", "recorder"];

const save_routes = sparrow.utils.debounce(() => {
	if (sparrow.session.user === "Guest") return;
	const routes = sparrow.route_history_queue;
	if (!routes.length) return;

	sparrow.route_history_queue = [];

	sparrow
		.xcall("sparrow.desk.doctype.route_history.route_history.deferred_insert", {
			routes: routes,
		})
		.catch(() => {
			sparrow.route_history_queue.concat(routes);
		});
}, 10000);

sparrow.router.on("change", () => {
	const route = sparrow.get_route();
	if (is_route_useful(route)) {
		sparrow.route_history_queue.push({
			creation: sparrow.datetime.now_datetime(),
			route: sparrow.get_route_str(),
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === "List" && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}
