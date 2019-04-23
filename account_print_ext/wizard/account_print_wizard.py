# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountPrintWizard(models.TransientModel):
	_name = 'account.print.wizard'

	print_level = fields.Integer('Account level')

	def print_confirm(self):
		data = {'account_level': self.print_level,
				'ids': self._context.get('active_ids')}

		# _logger.info({
		# 	'context': self._context.get('active_ids'),
		# 	'account_level': self.print_level
		# })
		# {'context': [671971, 671968], 'account_level': 2}
		return self.with_context(data).env['report'].get_action(
			self, 'account_print_ext.report_account_move', data=data)
