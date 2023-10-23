import sparrow
import sparrow.share


def execute():
	for user in sparrow.STANDARD_USERS:
		sparrow.share.remove("User", user, user)
