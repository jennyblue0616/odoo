# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountPrintWizard(models.TransientModel):
	_name = 'account.print.wizard'

	print_level = fields.Integer('Account level')

	def print_to_pdf(self):
		data = {'account_level': self.print_level,
				'ids': self._context.get('active_ids')}

		return self.with_context(data).env['report'].get_action(
			self, 'account_print_ext.report_account_move', data=data)

	# def print_to_excel(self):
	# 	report_name = 'account_print_ext.account_report'
	# 	data = {'ids':self._context.get('active_ids')}
	# 	return self.env['report'].get_action(self, report_name, data=data)


