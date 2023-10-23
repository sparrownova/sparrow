import sparrow
from sparrow.website.page_renderers.error_page import ErrorPage
from sparrow.website.page_renderers.not_found_page import NotFoundPage
from sparrow.website.page_renderers.not_permitted_page import NotPermittedPage
from sparrow.website.page_renderers.redirect_page import RedirectPage
from sparrow.website.path_resolver import PathResolver


def get_response(path=None, http_status_code=200):
	"""Resolves path and renders page"""
	response = None
	path = path or sparrow.local.request.path
	endpoint = path

	try:
		path_resolver = PathResolver(path)
		endpoint, renderer_instance = path_resolver.resolve()
		response = renderer_instance.render()
	except sparrow.Redirect:
		return RedirectPage(endpoint or path, http_status_code).render()
	except sparrow.PermissionError as e:
		response = NotPermittedPage(endpoint, http_status_code, exception=e).render()
	except sparrow.PageDoesNotExistError:
		response = NotFoundPage(endpoint, http_status_code).render()
	except Exception as e:
		response = ErrorPage(exception=e).render()

	return response


def get_response_content(path=None, http_status_code=200):
	response = get_response(path, http_status_code)
	return str(response.data, "utf-8")
