# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document


class OAuthProviderSettings(Document):
	pass


def get_oauth_settings():
	"""Returns oauth settings"""
	out = sparrow._dict(
		{
			"skip_authorization": sparrow.db.get_single_value(
				"OAuth Provider Settings", "skip_authorization"
			)
		}
	)

	return out
