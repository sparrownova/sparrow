# Copyright (c) 2021, Sparrow Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import sparrow


def execute():
	indicator_map = {
		"blue": "Blue",
		"orange": "Orange",
		"red": "Red",
		"green": "Green",
		"darkgrey": "Gray",
		"gray": "Gray",
		"purple": "Purple",
		"yellow": "Yellow",
		"lightblue": "Light Blue",
	}
	for d in sparrow.get_all("Kanban Board Column", fields=["name", "indicator"]):
		color_name = indicator_map.get(d.indicator, "Gray")
		sparrow.db.set_value("Kanban Board Column", d.name, "indicator", color_name)
