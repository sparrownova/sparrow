import sparrow
from sparrow.cache_manager import clear_defaults_cache


def execute():
	sparrow.db.set_default(
		"suspend_email_queue",
		sparrow.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	sparrow.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()
