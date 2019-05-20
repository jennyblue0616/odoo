# -*- coding: utf-8 -*-
{
	'name': 'income_statement',
	'description': """
export income statement to excel
""",
	'author': "ymj",
	'license': 'AGPL-3',
	"data": [
		'security/ir.model.access.csv',
		'wizard/income_sheet.xml',
		'views/income_account_report.xml',
		'views/income_tax_menu.xml',
		'views/customer_attribute_menu.xml'
	],
	'installable': True,
	'application': False,
	'auto_install': False,
}
