import ast
import copy
import inspect
import json
import mimetypes
import types
from contextlib import contextmanager
from functools import lru_cache

import RestrictedPython.Guards
from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.transformer import RestrictingNodeTransformer

import sparrow
import sparrow.exceptions
import sparrow.integrations.utils
import sparrow.utils
import sparrow.utils.data
from sparrow import _
from sparrow.core.utils import html2text
from sparrow.frappeclient import FrappeClient
from sparrow.handler import execute_cmd
from sparrow.model.delete_doc import delete_doc
from sparrow.model.mapper import get_mapped_doc
from sparrow.model.rename_doc import rename_doc
from sparrow.modules import scrub
from sparrow.utils.background_jobs import enqueue, get_jobs
from sparrow.website.utils import get_next_link, get_shade, get_toc
from sparrow.www.printview import get_visible_columns


class ServerScriptNotEnabled(sparrow.PermissionError):
	pass


ARGUMENT_NOT_SET = object()


class NamespaceDict(sparrow._dict):
	"""Raise AttributeError if function not found in namespace"""

	def __getattr__(self, key):
		ret = self.get(key)
		if (not ret and key.startswith("__")) or (key not in self):

			def default_function(*args, **kwargs):
				raise AttributeError(f"module has no attribute '{key}'")

			return default_function
		return ret


class FrappeTransformer(RestrictingNodeTransformer):
	def check_name(self, node, name, *args, **kwargs):
		if name == "_dict":
			return

		return super().check_name(node, name, *args, **kwargs)


def safe_exec(script, _globals=None, _locals=None, restrict_commit_rollback=False):
	# server scripts can be disabled via site_config.json
	# they are enabled by default
	if "server_script_enabled" in sparrow.conf:
		enabled = sparrow.conf.server_script_enabled
	else:
		enabled = True

	if not enabled:
		sparrow.throw(_("Please Enable Server Scripts"), ServerScriptNotEnabled)

	# build globals
	exec_globals = get_safe_globals()
	if _globals:
		exec_globals.update(_globals)

	if restrict_commit_rollback:
		# prevent user from using these in docevents
		exec_globals.sparrow.db.pop("commit", None)
		exec_globals.sparrow.db.pop("rollback", None)
		exec_globals.sparrow.db.pop("add_index", None)

	with safe_exec_flags(), patched_qb():
		# execute script compiled by RestrictedPython
		exec(
			compile_restricted(script, filename="<serverscript>", policy=FrappeTransformer),
			exec_globals,
			_locals,
		)

	return exec_globals, _locals


def safe_eval(code, eval_globals=None, eval_locals=None):
	import unicodedata

	code = unicodedata.normalize("NFKC", code)

	_validate_safe_eval_syntax(code)

	if not eval_globals:
		eval_globals = {}

	eval_globals["__builtins__"] = {}
	eval_globals.update(WHITELISTED_SAFE_EVAL_GLOBALS)

	return eval(
		compile_restricted(code, filename="<safe_eval>", policy=FrappeTransformer, mode="eval"),
		eval_globals,
		eval_locals,
	)


def _validate_safe_eval_syntax(code):
	BLOCKED_NODES = (ast.NamedExpr,)

	tree = ast.parse(code, mode="eval")
	for node in ast.walk(tree):
		if isinstance(node, BLOCKED_NODES):
			raise SyntaxError(f"Operation not allowed: line {node.lineno} column {node.col_offset}")


@contextmanager
def safe_exec_flags():
	sparrow.flags.in_safe_exec = True
	yield
	sparrow.flags.in_safe_exec = False


def get_safe_globals():
	datautils = sparrow._dict()

	if sparrow.db:
		date_format = sparrow.db.get_default("date_format") or "yyyy-mm-dd"
		time_format = sparrow.db.get_default("time_format") or "HH:mm:ss"
	else:
		date_format = "yyyy-mm-dd"
		time_format = "HH:mm:ss"

	add_data_utils(datautils)

	form_dict = getattr(sparrow.local, "form_dict", sparrow._dict())

	if "_" in form_dict:
		del sparrow.local.form_dict["_"]

	user = getattr(sparrow.local, "session", None) and sparrow.local.session.user or "Guest"

	out = NamespaceDict(
		# make available limited methods of sparrow
		json=NamespaceDict(loads=json.loads, dumps=json.dumps),
		as_json=sparrow.as_json,
		dict=dict,
		log=sparrow.log,
		_dict=sparrow._dict,
		args=form_dict,
		sparrow=NamespaceDict(
			call=call_whitelisted_function,
			flags=sparrow._dict(),
			format=sparrow.format_value,
			format_value=sparrow.format_value,
			date_format=date_format,
			time_format=time_format,
			format_date=sparrow.utils.data.global_date_format,
			form_dict=form_dict,
			bold=sparrow.bold,
			copy_doc=sparrow.copy_doc,
			errprint=sparrow.errprint,
			qb=sparrow.qb,
			get_meta=sparrow.get_meta,
			new_doc=sparrow.new_doc,
			get_doc=sparrow.get_doc,
			get_mapped_doc=get_mapped_doc,
			get_last_doc=sparrow.get_last_doc,
			get_cached_doc=sparrow.get_cached_doc,
			get_list=sparrow.get_list,
			get_all=sparrow.get_all,
			get_system_settings=sparrow.get_system_settings,
			rename_doc=rename_doc,
			delete_doc=delete_doc,
			utils=datautils,
			get_url=sparrow.utils.get_url,
			render_template=sparrow.render_template,
			msgprint=sparrow.msgprint,
			throw=sparrow.throw,
			sendmail=sparrow.sendmail,
			get_print=sparrow.get_print,
			attach_print=sparrow.attach_print,
			user=user,
			get_fullname=sparrow.utils.get_fullname,
			get_gravatar=sparrow.utils.get_gravatar_url,
			full_name=sparrow.local.session.data.full_name
			if getattr(sparrow.local, "session", None)
			else "Guest",
			request=getattr(sparrow.local, "request", {}),
			session=sparrow._dict(
				user=user,
				csrf_token=sparrow.local.session.data.csrf_token
				if getattr(sparrow.local, "session", None)
				else "",
			),
			make_get_request=sparrow.integrations.utils.make_get_request,
			make_post_request=sparrow.integrations.utils.make_post_request,
			make_put_request=sparrow.integrations.utils.make_put_request,
			socketio_port=sparrow.conf.socketio_port,
			get_hooks=get_hooks,
			enqueue=safe_enqueue,
			sanitize_html=sparrow.utils.sanitize_html,
			log_error=sparrow.log_error,
			log=sparrow.log,
			db=NamespaceDict(
				get_list=sparrow.get_list,
				get_all=sparrow.get_all,
				get_value=sparrow.db.get_value,
				set_value=sparrow.db.set_value,
				get_single_value=sparrow.db.get_single_value,
				get_default=sparrow.db.get_default,
				exists=sparrow.db.exists,
				count=sparrow.db.count,
				escape=sparrow.db.escape,
				sql=read_sql,
				commit=sparrow.db.commit,
				rollback=sparrow.db.rollback,
				add_index=sparrow.db.add_index,
			),
			lang=getattr(sparrow.local, "lang", "en"),
		),
		FrappeClient=FrappeClient,
		style=sparrow._dict(border_color="#d1d8dd"),
		get_toc=get_toc,
		get_next_link=get_next_link,
		_=sparrow._,
		get_shade=get_shade,
		scrub=scrub,
		guess_mimetype=mimetypes.guess_type,
		html2text=html2text,
		dev_server=sparrow.local.dev_server,
		run_script=run_script,
		is_job_queued=is_job_queued,
		get_visible_columns=get_visible_columns,
	)

	add_module_properties(
		sparrow.exceptions, out.sparrow, lambda obj: inspect.isclass(obj) and issubclass(obj, Exception)
	)

	if sparrow.response:
		out.sparrow.response = sparrow.response

	out.update(safe_globals)

	# default writer allows write access
	out._write_ = _write
	out._getitem_ = _getitem
	out._getattr_ = _getattr_for_safe_exec

	# allow iterators and list comprehension
	out._getiter_ = iter
	out._iter_unpack_sequence_ = RestrictedPython.Guards.guarded_iter_unpack_sequence

	# add common python builtins
	out.update(get_python_builtins())

	return out


def is_job_queued(job_name, queue="default"):
	"""
	:param job_name: used to identify a queued job, usually dotted path to function
	:param queue: should be either long, default or short
	"""

	site = sparrow.local.site
	queued_jobs = get_jobs(site=site, queue=queue, key="job_name").get(site)
	return queued_jobs and job_name in queued_jobs


def safe_enqueue(function, **kwargs):
	"""
	Enqueue function to be executed using a background worker
	Accepts sparrow.enqueue params like job_name, queue, timeout, etc.
	in addition to params to be passed to function

	:param function: whitelisted function or API Method set in Server Script
	"""

	return enqueue("sparrow.utils.safe_exec.call_whitelisted_function", function=function, **kwargs)


def call_whitelisted_function(function, **kwargs):
	"""Executes a whitelisted function or Server Script of type API"""

	return call_with_form_dict(lambda: execute_cmd(function), kwargs)


def run_script(script, **kwargs):
	"""run another server script"""

	return call_with_form_dict(
		lambda: sparrow.get_doc("Server Script", script).execute_method(), kwargs
	)


def call_with_form_dict(function, kwargs):
	# temporarily update form_dict, to use inside below call
	form_dict = getattr(sparrow.local, "form_dict", sparrow._dict())
	if kwargs:
		sparrow.local.form_dict = form_dict.copy().update(kwargs)

	try:
		return function()
	finally:
		sparrow.local.form_dict = form_dict


@contextmanager
def patched_qb():
	require_patching = isinstance(sparrow.qb.terms, types.ModuleType)
	try:
		if require_patching:
			_terms = sparrow.qb.terms
			sparrow.qb.terms = _flatten(sparrow.qb.terms)
		yield
	finally:
		if require_patching:
			sparrow.qb.terms = _terms


@lru_cache
def _flatten(module):
	new_mod = NamespaceDict()
	for name, obj in inspect.getmembers(module, lambda x: not inspect.ismodule(x)):
		if not name.startswith("_"):
			new_mod[name] = obj
	return new_mod


def get_python_builtins():
	return {
		"abs": abs,
		"all": all,
		"any": any,
		"bool": bool,
		"dict": dict,
		"enumerate": enumerate,
		"isinstance": isinstance,
		"issubclass": issubclass,
		"list": list,
		"max": max,
		"min": min,
		"range": range,
		"set": set,
		"sorted": sorted,
		"sum": sum,
		"tuple": tuple,
	}


def get_hooks(hook=None, default=None, app_name=None):
	hooks = sparrow.get_hooks(hook=hook, default=default, app_name=app_name)
	return copy.deepcopy(hooks)


def read_sql(query, *args, **kwargs):
	"""a wrapper for sparrow.db.sql to allow reads"""
	query = str(query)
	check_safe_sql_query(query)
	return sparrow.db.sql(query, *args, **kwargs)


def check_safe_sql_query(query: str, throw: bool = True) -> bool:
	"""Check if SQL query is safe for running in restricted context.

	Safe queries:
	        1. Read only 'select' or 'explain' queries
	        2. CTE on mariadb where writes are not allowed.
	"""

	query = query.strip().lower()
	whitelisted_statements = ("select", "explain")

	if query.startswith(whitelisted_statements) or (
            query.startswith("with") and sparrow.db.db_type == "mariadb"
	):
		return True

	if throw:
		sparrow.throw(
			_("Query must be of SELECT or read-only WITH type."),
			title=_("Unsafe SQL query"),
			exc=sparrow.PermissionError,
		)

	return False


def _getitem(obj, key):
	# guard function for RestrictedPython
	# allow any key to be accessed as long as it does not start with underscore
	if isinstance(key, str) and key.startswith("_"):
		raise SyntaxError("Key starts with _")
	return obj[key]


UNSAFE_ATTRIBUTES = {
	# Generator Attributes
	"gi_frame",
	"gi_code",
	"gi_yieldfrom",
	# Coroutine Attributes
	"cr_frame",
	"cr_code",
	"cr_origin",
	"cr_await",
	# Async Generator Attributes
	"ag_code",
	"ag_frame",
	# Traceback Attributes
	"tb_frame",
	"tb_next",
	# Format Attributes
	"format",
	"format_map",
	# Frame attributes
	"f_back",
	"f_builtins",
	"f_code",
	"f_globals",
	"f_locals",
	"f_trace",
}


def _getattr_for_safe_exec(object, name, default=None):
	# guard function for RestrictedPython
	# allow any key to be accessed as long as
	# 1. it does not start with an underscore (safer_getattr)
	# 2. it is not an UNSAFE_ATTRIBUTES
	_validate_attribute_read(object, name)

	return RestrictedPython.Guards.safer_getattr(object, name, default=default)


def _get_attr_for_eval(object, name, default=ARGUMENT_NOT_SET):
	_validate_attribute_read(object, name)

	# Use vanilla getattr to raise correct attribute error. Safe exec has been supressing attribute
	# error which is bad for DX/UX in general.
	return getattr(object, name) if default is ARGUMENT_NOT_SET else getattr(object, name, default)


def _validate_attribute_read(object, name):
	if isinstance(name, str) and (name in UNSAFE_ATTRIBUTES):
		raise SyntaxError(f"{name} is an unsafe attribute")

	if isinstance(object, (types.ModuleType, types.CodeType, types.TracebackType, types.FrameType)):
		raise SyntaxError(f"Reading {object} attributes is not allowed")

	if name.startswith("_"):
		raise AttributeError(f'"{name}" is an invalid attribute name because it ' 'starts with "_"')


def _write(obj):
	# guard function for RestrictedPython
	if isinstance(
		obj,
		(
			types.ModuleType,
			types.CodeType,
			types.TracebackType,
			types.FrameType,
			type,
			types.FunctionType,  # covers lambda
			types.MethodType,
			types.BuiltinFunctionType,  # covers methods
		),
	):
		raise SyntaxError(f"Not allowed to write to object {obj} of type {type(obj)}")
	return obj


def add_data_utils(data):
	for key, obj in sparrow.utils.data.__dict__.items():
		if key in VALID_UTILS:
			data[key] = obj


def add_module_properties(module, data, filter_method):
	for key, obj in module.__dict__.items():
		if key.startswith("_"):
			# ignore
			continue

		if filter_method(obj):
			# only allow functions
			data[key] = obj


VALID_UTILS = (
	"DATE_FORMAT",
	"TIME_FORMAT",
	"DATETIME_FORMAT",
	"is_invalid_date_string",
	"getdate",
	"get_datetime",
	"to_timedelta",
	"get_timedelta",
	"add_to_date",
	"add_days",
	"add_months",
	"add_years",
	"date_diff",
	"month_diff",
	"time_diff",
	"time_diff_in_seconds",
	"time_diff_in_hours",
	"now_datetime",
	"get_timestamp",
	"get_eta",
	"get_time_zone",
	"get_system_timezone",
	"convert_utc_to_user_timezone",
	"convert_utc_to_system_timezone",
	"now",
	"nowdate",
	"today",
	"nowtime",
	"get_first_day",
	"get_quarter_start",
	"get_first_day_of_week",
	"get_year_start",
	"get_last_day_of_week",
	"get_last_day",
	"get_time",
	"get_datetime_in_timezone",
	"get_datetime_str",
	"get_date_str",
	"get_time_str",
	"get_user_date_format",
	"get_user_time_format",
	"format_date",
	"format_time",
	"format_datetime",
	"format_duration",
	"get_weekdays",
	"get_weekday",
	"get_timespan_date_range",
	"global_date_format",
	"has_common",
	"flt",
	"cint",
	"floor",
	"ceil",
	"cstr",
	"rounded",
	"remainder",
	"safe_div",
	"round_based_on_smallest_currency_fraction",
	"encode",
	"parse_val",
	"fmt_money",
	"get_number_format_info",
	"money_in_words",
	"in_words",
	"is_html",
	"is_image",
	"get_thumbnail_base64_for_image",
	"image_to_base64",
	"pdf_to_base64",
	"strip_html",
	"escape_html",
	"pretty_date",
	"comma_or",
	"comma_and",
	"comma_sep",
	"new_line_sep",
	"filter_strip_join",
	"get_url",
	"get_host_name_from_request",
	"url_contains_port",
	"get_host_name",
	"get_link_to_form",
	"get_link_to_report",
	"get_absolute_url",
	"get_url_to_form",
	"get_url_to_list",
	"get_url_to_report",
	"get_url_to_report_with_filters",
	"evaluate_filters",
	"compare",
	"get_filter",
	"make_filter_tuple",
	"make_filter_dict",
	"sanitize_column",
	"scrub_urls",
	"expand_relative_urls",
	"quoted",
	"quote_urls",
	"unique",
	"strip",
	"to_markdown",
	"md_to_html",
	"markdown",
	"is_subset",
	"generate_hash",
	"formatdate",
	"get_user_info_for_avatar",
	"get_abbr",
)


WHITELISTED_SAFE_EVAL_GLOBALS = {
	"int": int,
	"float": float,
	"long": int,
	"round": round,
	# RestrictedPython specific overrides
	"_getattr_": _get_attr_for_eval,
	"_getitem_": _getitem,
	"_getiter_": iter,
	"_iter_unpack_sequence_": RestrictedPython.Guards.guarded_iter_unpack_sequence,
}
