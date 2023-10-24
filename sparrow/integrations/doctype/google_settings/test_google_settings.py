# Copyright (c) 2021, Sparrow Technologies and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.tests.utils import sparrowTestCase

from .google_settings import get_file_picker_settings


class TestGoogleSettings(sparrowTestCase):
	def setUp(self):
		settings = sparrow.get_single("Google Settings")
		settings.client_id = "test_client_id"
		settings.app_id = "test_app_id"
		settings.api_key = "test_api_key"
		settings.save()

	def test_picker_disabled(self):
		"""Google Drive Picker should be disabled if it is not enabled in Google Settings."""
		sparrow.db.set_single_value("Google Settings", "enable", 1)
		sparrow.db.set_single_value("Google Settings", "google_drive_picker_enabled", 0)
		settings = get_file_picker_settings()

		self.assertEqual(settings, {})

	def test_google_disabled(self):
		"""Google Drive Picker should be disabled if Google integration is not enabled."""
		sparrow.db.set_single_value("Google Settings", "enable", 0)
		sparrow.db.set_single_value("Google Settings", "google_drive_picker_enabled", 1)
		settings = get_file_picker_settings()

		self.assertEqual(settings, {})

	def test_picker_enabled(self):
		"""If picker is enabled, get_file_picker_settings should return the credentials."""
		sparrow.db.set_single_value("Google Settings", "enable", 1)
		sparrow.db.set_single_value("Google Settings", "google_drive_picker_enabled", 1)
		settings = get_file_picker_settings()

		self.assertEqual(True, settings.get("enabled", False))
		self.assertEqual("test_client_id", settings.get("clientId", ""))
		self.assertEqual("test_app_id", settings.get("appId", ""))
		self.assertEqual("test_api_key", settings.get("developerKey", ""))
