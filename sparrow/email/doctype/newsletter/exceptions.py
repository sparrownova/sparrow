# Copyright (c) 2021, Sparrownova Technologies and Contributors
# MIT License. See LICENSE

from sparrow.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
