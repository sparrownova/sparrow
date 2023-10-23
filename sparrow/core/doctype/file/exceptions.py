import sparrow


class MaxFileSizeReachedError(sparrow.ValidationError):
	pass


class FolderNotEmpty(sparrow.ValidationError):
	pass


from sparrow.exceptions import *
