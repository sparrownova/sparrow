# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class OAuthBearerToken(Document):
	def validate(self):
		if not self.expiration_time:
			self.expiration_time = sparrow.utils.datetime.datetime.strptime(
				self.creation, "%Y-%m-%d %H:%M:%S.%f"
			) + sparrow.utils.datetime.timedelta(seconds=self.expires_in)
