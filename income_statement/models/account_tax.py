# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountIncomeTax(models.Model):
	_name = 'account.income.tax'

	account_id = fields.Many2many('account.account', string='subject')
	tax_id = fields.Many2one('account.tax', string='tax')
	start_period_id = fields.Many2one('account.period', string='period')
	end_period_id = fields.Many2one('account.period', string='period')

# class ResPartnerModel(models.Model):
# 	_inherit = 'res.partner'
#
# 	ptype_id = fields.Many2many('core.value')

class CustomerAttribute(models.Model):
	_name = 'customer.attribute'

	type_id = fields.Char(string=u'type')
	value_id = fields.Char(string=u'value')

