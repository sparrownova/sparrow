# Copyright (c) 2018, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
