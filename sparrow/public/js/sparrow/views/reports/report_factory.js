// Copyright (c) 2015, Sparrownova Technologies and Contributors
// MIT License. See license.txt

sparrow.views.ReportFactory = class ReportFactory extends sparrow.views.Factory {
	make(route) {
		const _route = ["List", route[1], "Report"];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		sparrow.set_route(_route);
	}
};
