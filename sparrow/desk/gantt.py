# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import json

import sparrow


@sparrow.whitelist()
def update_task(args, field_map):
	"""Updates Doc (called via gantt) based on passed `field_map`"""
	args = sparrow._dict(json.loads(args))
	field_map = sparrow._dict(json.loads(field_map))
	d = sparrow.get_doc(args.doctype, args.name)
	d.set(field_map.start, args.start)
	d.set(field_map.end, args.end)
	d.save()
