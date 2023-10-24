import sparrow
from sparrow.tests.utils import sparrowTestCase, change_settings


class TestTestUtils(sparrowTestCase):
	SHOW_TRANSACTION_COMMIT_WARNINGS = True

	def test_document_assertions(self):

		currency = sparrow.new_doc("Currency")
		currency.currency_name = "STONKS"
		currency.smallest_currency_fraction_value = 0.420_001
		currency.save()

		self.assertDocumentEqual(currency.as_dict(), currency)

	def test_thread_locals(self):
		sparrow.flags.temp_flag_to_be_discarded = True

	def test_temp_setting_changes(self):
		current_setting = sparrow.get_system_settings("logout_on_password_reset")

		with change_settings("System Settings", {"logout_on_password_reset": int(not current_setting)}):
			updated_settings = sparrow.get_system_settings("logout_on_password_reset")
			self.assertNotEqual(current_setting, updated_settings)

		restored_settings = sparrow.get_system_settings("logout_on_password_reset")
		self.assertEqual(current_setting, restored_settings)


def tearDownModule():
	"""assertions for ensuring tests didn't leave state behind"""
	assert "temp_flag_to_be_discarded" not in sparrow.flags
	assert not sparrow.db.exists("Currency", "STONKS")
