# Copyright (c) 2017, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import sparrow


@sparrow.whitelist()
def get_leaderboard_config():
	leaderboard_config = sparrow._dict()
	leaderboard_hooks = sparrow.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(sparrow.get_attr(hook)())

	return leaderboard_config
