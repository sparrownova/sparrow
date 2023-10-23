import sparrow


# no context object is accepted
def get_context():
	context = sparrow._dict()
	context.body = "Custom Content"
	return context
