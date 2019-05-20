# -*- coding: utf-8 -*-
import traceback

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MonomerStatements(models.Model):
	_name = 'monomer.statements'
	_sql_constraints = [('unique_name', 'unique(name)', 'the name must be unique'),
						('unique_company_period', 'unique(company_id, period_id)', 'the company must be unique')]

	name = fields.Char(string='name', required=True, default=lambda self: self._compute_name())
	period_id = fields.Many2one('account.period', string='period')
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)

	assess_operating_income_month = fields.Float('assess operating income', compute='sum_assess', store=True)
	operating_income_month = fields.Float('operating income', compute='sum_operating', store=True)
	adjust_item_month = fields.Float('adjust item', compute='sum_item', store=True)
	assess_operating_income_year = fields.Float('assess operating income year', compute='sum_assess_year', store=True)
	operating_income_year = fields.Float('operating income year', compute='sum_operating', store=True)
	adjust_item_year = fields.Float('adjust item year', compute='sum_item_year', store=True)

	assess_operating_cost_month = fields.Float('assess operating cost', compute='sum_assess', store=True)
	operating_cost_month = fields.Float('operating cost', compute='sum_operating', store=True)
	adjust_item_cost_month = fields.Float('adjust item cost', compute='sum_item', store=True)
	assess_operating_cost_year = fields.Float('assess operating cost year', compute='sum_assess_year', store=True)
	operating_cost_year = fields.Float('operating cost year', compute='sum_operating', store=True)
	adjust_item_cost_year = fields.Float('adjust item cost year', compute='sum_item_year', store=True)

	assess_operating_profit_month = fields.Float('assess operating profit', compute='sum_assess', store=True)
	operating_profit_month = fields.Float('operating profit', compute='sum_operating', store=True)
	adjust_item_profit_month = fields.Float('adjust item profit', compute='sum_item', store=True)
	assess_operating_profit_year = fields.Float('assess operating profit year', compute='sum_assess_year', store=True)
	operating_profit_year = fields.Float('operating profit year', compute='sum_operating', store=True)
	adjust_item_profit_year = fields.Float('adjust item profit year', compute='sum_item_year', store=True)

	assess_operating_receive_month = fields.Float('assess operating receive', compute='sum_assess', store=True)
	operating_receive_month = fields.Float('operating receive', compute='sum_operating', store=True)
	adjust_item_receive_month = fields.Float('adjust item receive', compute='sum_item', store=True)

	operate_id = fields.One2many('monomer.statements.income.line', 'operate_line_id')
	cost_id = fields.One2many('monomer.statements.cost.line', 'cost_line_id')
	profit_id = fields.One2many('monomer.statements.profit.line', 'profit_line_id')
	receive_id = fields.One2many('monomer.statements.receive.line', 'receive_line_id')

	# @api.constrains('period_id')
	def _check_period(self, current_period_id):
		if not current_period_id:
			raise UserError(u'必须选择期间')
		current_period_id = self.env['account.period'].browse(current_period_id)
		account_move = self.env['account.move'].search([('company_id', '=', self.env.user.company_id.id)],
													   order='period_id')
		account_move_records = account_move.filtered(lambda x: x.period_id == current_period_id)
		if not account_move_records:
			raise UserError(u'必须先创建期间为[%s]的会计凭证' % current_period_id.code)
		monomer_records = self.env['monomer.statements'].search([('company_id', '=', self.env.user.company_id.id)],
																order='period_id desc')
		if current_period_id.code.split('/')[0] == '01' and account_move_records:
			return True
		elif not monomer_records:
			first_record = account_move[0].period_id
			if current_period_id.code != first_record.code:
				raise UserError(u'选择期间必须等于凭证发生最早期间')
		elif monomer_records:
			period_record = self.env['account.period'].get_last_period(current_period_id)
			record = self.env['monomer.statements'].search([('company_id', '=', self.env.user.company_id.id),
															('period_id', '=', period_record.id)])
			if not record:
				raise UserError(u'上一期间的调整报表数据为空, 请先创建.')

	def _compute_name(self):
		return self.env['ir.sequence'].sudo().next_by_code('monomer.statements.create.code') + '/' + \
			   str(self.env.user.company_id.id)

	@api.depends('period_id')
	def sum_operating(self):
		res = self.env['ac.tb'].search(['&',
										'&', ('company_id', '=', self.env.user.company_id.id),
										('period_id', '=', self.period_id.id),
										'|', ('code', 'like', '6001'), ('code', 'like', '6051')])
		sum_credit = sum(x.credit for x in res)
		res1 = self.env['ac.tb'].search(['&',
										 '&', ('company_id', '=', self.env.user.company_id.id),
										 ('period_id', '=', self.period_id.id),
										 '|', ('code', 'like', '6401'), ('code', 'like', '6402')])
		sum_debit = sum(x.debit for x in res1)
		res2 = self.env['ac.tb'].search([
			('company_id', '=', self.env.user.company_id.id), ('period_id', '=', self.period_id.id),
			('code', 'like', '4103')
		])
		sum_profit_debit = sum(x.debit for x in res2)
		sum_profit_credit = sum(x.credit for x in res2)
		sum_profit = ''
		if sum_profit_debit != 0:
			sum_profit = '-' + str(sum_profit_debit)
		if sum_profit_credit != 0:
			sum_profit = sum_profit_credit
		res3 = self.env['ac.tb'].search([
			('company_id', '=', self.env.user.company_id.id), ('period_id', '=', self.period_id.id),
			('code', 'like', '1122')
		])
		sum_receive = sum(x.balance for x in res3)
		self.operating_income_month = sum_credit
		self.operating_cost_month = sum_debit
		self.operating_profit_month = sum_profit
		self.operating_receive_month = sum_receive
		if self.period_id:
			last_period = self.env['account.period'].get_last_period(self.period_id)
			if last_period:
				result = self.env['monomer.statements'].search([('company_id', '=', self.env.user.company_id.id),
																('period_id', '=', last_period.id)])
				self.operating_income_year = self.operating_income_month + result.operating_income_year
				self.operating_cost_year = self.operating_cost_month + result.operating_cost_year
				self.operating_profit_year = self.operating_profit_month + result.operating_profit_year
			else:
				self.operating_income_year = self.operating_income_month
				self.operating_cost_year = self.operating_cost_month
				self.operating_profit_year = self.operating_profit_month

	@api.one
	@api.depends('operate_id.month_amount', 'cost_id.month_amount', 'profit_id.month_amount',
				 'receive_id.month_amount')
	def sum_item(self):
		self.adjust_item_month = sum(item.month_amount for item in self.operate_id)
		self.adjust_item_cost_month = sum(item.month_amount for item in self.cost_id)
		self.adjust_item_profit_month = sum(item.month_amount for item in self.profit_id)
		self.adjust_item_receive_month = sum(item.month_amount for item in self.receive_id)

	@api.depends('operating_income_month', 'adjust_item_month', 'operating_cost_month', 'adjust_item_cost_month',
				 'operating_profit_month', 'adjust_item_profit_month', 'operating_receive_month', 'adjust_item_receive_month')
	def sum_assess(self):
		self.assess_operating_income_month = self.operating_income_month + self.adjust_item_month
		self.assess_operating_cost_month = self.operating_cost_month + self.adjust_item_cost_month
		self.assess_operating_profit_month = self.operating_profit_month + self.adjust_item_profit_month
		self.assess_operating_receive_month =  self.operating_receive_month + self.adjust_item_receive_month

	@api.one
	@api.depends('operate_id.year_amount', 'cost_id.year_amount', 'profit_id.year_amount')
	def sum_item_year(self):
		self.adjust_item_year = sum(item.year_amount for item in self.operate_id)
		self.adjust_item_cost_year = sum(item.year_amount for item in self.cost_id)
		self.adjust_item_profit_year = sum(item.year_amount for item in self.profit_id)

	@api.depends('operating_income_year', 'adjust_item_year', 'operating_cost_year',
				 'adjust_item_cost_year', 'operating_profit_year', 'adjust_item_profit_year')
	def sum_assess_year(self):
		self.assess_operating_income_year = self.operating_income_year + self.adjust_item_year
		self.assess_operating_cost_year = self.operating_cost_year + self.adjust_item_cost_year
		self.assess_operating_profit_year = self.operating_profit_year + self.adjust_item_profit_year

	def _get_create_amount(self, vals, monomer_model, monomer_field):
		period_id = vals.get('period_id', False)
		if not period_id:
			raise UserError(u'期间必填')
		if self.period_id or 'period_id' in vals.keys():
			period_object = self.env['account.period'].browse(period_id)
			last_period = self.env['account.period'].get_last_period(period_object)
			if last_period:
				last_period_partner = self.env[monomer_model].search([('period_id', '=', last_period.id)])
				last_ids = last_period_partner.mapped('company_id').ids
				set_last = set(last_ids)
				company_ids = vals.get(monomer_field, False)
				current_ids = []
				last_result = []
				for i in range(len(company_ids)) if company_ids else []:
					current_ids.append(company_ids[i][2].get('company_id', False))
				set_current = set(current_ids)
				sub_result = set_last - set_current
				result = list(sub_result)
				update_partner = self.env[monomer_model].search([('period_id', '=', last_period.id),
																 ('company_id', 'in', result)])
				result_list = []
				for item in update_partner:
					update_set = {
						'company_id': item.company_id.id,
						'year_amount': item.year_amount,
						'account_id': item.account_id.id,
						'note': item.note
					}
					result_list = [0, False, update_set]
					last_result.append(result_list)
				for item in last_result:
					vals[monomer_field].append(item)
				return vals
			else:
				return vals

	def _get_last_amount(self, vals, monomer_model, monomer_field):
		period_id = self.period_id if self.period_id else vals.get('period_id', False)
		if not period_id:
			raise UserError(u'期间必填')
		if self.period_id or 'period_id' in vals.keys():
			last_period = self.env['account.period'].get_last_period(period_id)
			if last_period:
				last_period_partner = self.env[monomer_model].search([('period_id', '=', last_period.id)])
				last_ids = last_period_partner.mapped('company_id').ids
				company_ids = vals.get(monomer_field, False)
				partner_list = []
				last_result = []
				for i in range(len(company_ids)) if company_ids else []:
					partner_list.append(company_ids[i][1])
				current_ids = []
				for item in partner_list:
					partner = self.env[monomer_model].browse(item)
					current_ids.append(partner.mapped('company_id').id)
				set_last = set(last_ids)
				set_current = set(current_ids)
				sub_result = set_last - set_current
				result = list(sub_result)
				update_partner = self.env[monomer_model].search([('period_id', '=', last_period.id),
																 ('company_id', 'in', result)])
				for item in update_partner:
					update_set = {
						'company_id': item.company_id.id,
						'year_amount': item.year_amount,
						'account_id': item.account_id.id,
						'note': item.note
					}
					last_result = [0, 0, update_set]
					vals[monomer_field].append(last_result) if monomer_field in vals.keys() else vals.update({monomer_field:last_result})
				return vals
			else:
				return vals

	@api.model
	def create(self, vals):
		self._check_period(vals.get('period_id'))
		vals = self._get_create_amount(vals, monomer_model='monomer.statements.income.line', monomer_field='operate_id')
		vals = self._get_create_amount(vals, monomer_model='monomer.statements.cost.line', monomer_field='cost_id')
		vals = self._get_create_amount(vals, monomer_model='monomer.statements.profit.line', monomer_field='profit_id')
		res = super(MonomerStatements, self).create(vals)
		return res

	@api.multi
	def write(self, vals):
		if vals.get('period_id'):
			raise UserError(u'不允许修改期间')
		vals = self._get_last_amount(vals, monomer_model='monomer.statements.income.line', monomer_field='operate_id')
		vals = self._get_last_amount(vals, monomer_model='monomer.statements.cost.line', monomer_field='cost_id')
		vals = self._get_last_amount(vals, monomer_model='monomer.statements.profit.line', monomer_field='profit_id')
		res = super(MonomerStatements, self).write(vals)
		return res


class MonomerStatementsIncomeLine(models.Model):
	_name = 'monomer.statements.income.line'

	operate_line_id = fields.Many2one('monomer.statements')
	company_id = fields.Many2one('res.company', string='Company', required=True)
	self_company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	month_amount = fields.Float('month amount')
	year_amount = fields.Float('year amount', compute='sum_year', store=True)
	account_id = fields.Many2one('account.account', required=True)
	note = fields.Char('note', required=True)
	period_id = fields.Many2one('account.period', related='operate_line_id.period_id')

	# @api.multi
	@api.depends('month_amount')
	def sum_year(self):
		for item in self:
			if item.period_id:
				last_period = item.env['account.period'].get_last_period(item.period_id)
				if last_period:
					result = item.env['monomer.statements.income.line'].search([('company_id', '=', item.company_id.id),
																				('account_id', '=', item.account_id.id),
																				('note', '=', item.note),
																				('period_id', '=', last_period.id)])
					item.year_amount = item.month_amount + result.year_amount
				else:
					item.year_amount = item.month_amount


class MonomerStatementsCostLine(models.Model):
	_name = 'monomer.statements.cost.line'

	cost_line_id = fields.Many2one('monomer.statements')
	company_id = fields.Many2one('res.company', string='Company', required=True)
	self_company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	month_amount = fields.Float('month amount')
	year_amount = fields.Float('year amount', compute='sum_year1', store=True)
	account_id = fields.Many2one('account.account', required=True)
	note = fields.Char('note', required=True)
	period_id = fields.Many2one('account.period', related='cost_line_id.period_id')

	@api.depends('month_amount')
	def sum_year1(self):
		for item in self:
			if item.period_id:
				last_period = item.env['account.period'].get_last_period(item.period_id)
				if last_period:
					result = item.env['monomer.statements.cost.line'].search([('company_id', '=', item.company_id.id),
																			  ('account_id', '=', item.account_id.id),
																			  ('note', '=', item.note),
																			  ('period_id', '=', last_period.id)])
					item.year_amount = item.month_amount + result.year_amount
				else:
					item.year_amount = item.month_amount


class MonomerStatementsProfitLine(models.Model):
	_name = 'monomer.statements.profit.line'

	profit_line_id = fields.Many2one('monomer.statements')
	company_id = fields.Many2one('res.company', string='Company', required=True)
	self_company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	month_amount = fields.Float('month amount')
	year_amount = fields.Float('year amount', compute='sum_year2', store=True)
	account_id = fields.Many2one('account.account', required=True)
	note = fields.Char('note', required=True)
	period_id = fields.Many2one('account.period', related='profit_line_id.period_id')

	@api.depends('month_amount')
	def sum_year2(self):
		for item in self:
			if item.period_id:
				last_period = item.env['account.period'].get_last_period(item.period_id)
				if last_period:
					result = item.env['monomer.statements.profit.line'].search([('company_id', '=', item.company_id.id),
																				('account_id', '=', item.account_id.id),
																				('note', '=', item.note),
																				('period_id', '=', last_period.id)])
					item.year_amount = item.month_amount + result.year_amount
				else:
					item.year_amount = item.month_amount

class MonomerStatementsReceiveLine(models.Model):
	_name = 'monomer.statements.receive.line'

	receive_line_id = fields.Many2one('monomer.statements')
	company_id = fields.Many2one('res.company', string='Company', required=True)
	self_company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	month_amount = fields.Float('month amount')
	account_id = fields.Many2one('account.account', required=True)
	note = fields.Char('note', required=True)
	period_id = fields.Many2one('account.period', related='receive_line_id.period_id')