# Copyright (c) 2021, Sparrownova Technologies and Contributors
# MIT License. See license.txt


import functools

import sparrow


@sparrow.whitelist()
def get_google_fonts():
	return _get_google_fonts()


@functools.lru_cache
def _get_google_fonts():
	file_path = sparrow.get_app_path("sparrow", "data", "google_fonts.json")
	return sparrow.parse_json(sparrow.read_file(file_path))
