# Copyright (c) 2022, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import smtplib

import sparrow
from sparrow import _
from sparrow.email.oauth import Oauth
from sparrow.utils import cint, cstr


class InvalidEmailCredentials(sparrow.ValidationError):
	pass


def send(email, append_to=None, retry=1):
	"""Deprecated: Send the message or add it to Outbox Email"""

	def _send(retry):
		from sparrow.email.doctype.email_account.email_account import EmailAccount

		try:
			email_account = EmailAccount.find_outgoing(match_by_doctype=append_to)
			smtpserver = email_account.get_smtp_server()

			# validate is called in as_string
			email_body = email.as_string()

			smtpserver.sess.sendmail(email.sender, email.recipients + (email.cc or []), email_body)
		except smtplib.SMTPSenderRefused:
			sparrow.throw(_("Invalid login or password"), title="Email Failed")
			raise
		except smtplib.SMTPRecipientsRefused:
			sparrow.msgprint(_("Invalid recipient address"), title="Email Failed")
			raise
		except (smtplib.SMTPServerDisconnected, smtplib.SMTPAuthenticationError):
			if not retry:
				raise
			else:
				retry = retry - 1
				_send(retry)

	_send(retry)


class SMTPServer:
	def __init__(
		self,
		server,
		login=None,
		email_account=None,
		password=None,
		port=None,
		use_tls=None,
		use_ssl=None,
		use_oauth=0,
		access_token=None,
	):
		self.login = login
		self.email_account = email_account
		self.password = password
		self._server = server
		self._port = port
		self.use_tls = use_tls
		self.use_ssl = use_ssl
		self.use_oauth = use_oauth
		self.access_token = access_token
		self._session = None

		if not self.server:
			sparrow.msgprint(
				_(
					"Email Account not setup. Please create a new Email Account from Setup > Email > Email Account"
				),
				raise_exception=sparrow.OutgoingEmailError,
			)

	@property
	def port(self):
		port = self._port or (self.use_ssl and 465) or (self.use_tls and 587)
		return cint(port)

	@property
	def server(self):
		return cstr(self._server or "")

	def secure_session(self, conn):
		"""Secure the connection incase of TLS."""
		if self.use_tls:
			conn.ehlo()
			conn.starttls()
			conn.ehlo()

	@property
	def session(self):
		if self.is_session_active():
			return self._session

		SMTP = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

		try:
			_session = SMTP(self.server, self.port)
			if not _session:
				sparrow.msgprint(
					_("Could not connect to outgoing email server"), raise_exception=sparrow.OutgoingEmailError
				)

			self.secure_session(_session)

			if self.use_oauth:
				Oauth(_session, self.email_account, self.login, self.access_token).connect()

			elif self.password:
				res = _session.login(str(self.login or ""), str(self.password or ""))

				# check if logged correctly
				if res[0] != 235:
					sparrow.msgprint(res[1], raise_exception=sparrow.OutgoingEmailError)

			self._session = _session
			return self._session

		except smtplib.SMTPAuthenticationError:
			self.throw_invalid_credentials_exception()

		except OSError:
			# Invalid mail server -- due to refusing connection
			sparrow.throw(_("Invalid Outgoing Mail Server or Port"), title=_("Incorrect Configuration"))

	def is_session_active(self):
		if self._session:
			try:
				return self._session.noop()[0] == 250
			except Exception:
				return False

	def quit(self):
		if self.is_session_active():
			self._session.quit()

	@classmethod
	def throw_invalid_credentials_exception(cls):
		sparrow.throw(
			_("Please check your email login credentials."),
			title=_("Invalid Credentials"),
			exc=InvalidEmailCredentials,
		)
