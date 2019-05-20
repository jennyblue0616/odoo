# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
from ..tools.rpc import OdooRpc
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountIncomeWizard(models.TransientModel):
	_name = 'account.income.wizard'

	start_period = fields.Many2one('account.period', string='Start')
	end_period = fields.Many2one('account.period', string='End')
	customer = fields.Many2many('res.partner', string='customer')

	def report_parameter(self):
		res_data = list()
		cr = self._cr
		account_income_tax_records = self.env['account.income.tax'].search(
			[('start_period_id.date_start', '>=', self.start_period.date_start),
			 ('end_period_id.date_stop', '<=', self.end_period.date_stop)]
		)
		partner_ids = tuple(self.customer.ids)
		for record in account_income_tax_records:
			account_ids = tuple([i.id for i in record.account_id])
			if len(account_ids) == 1:
				account_ids = '(' + str(account_ids[0]) + ')'
			else:
				account_ids = account_ids
			sql = '''
				select sum(line.credit) amount, {tax_rate} as tax_rate, line.account_id, line.partner_id, 
					line.period_id, acc.name account_name, acc.code account_code,
					p.name partner_name, ap.code period_code, p.ac_period ac_period
				from account_move_line line
				left join account_account acc 
					on line.account_id = acc.id
				left join res_partner p
					on line.partner_id = p.id
				left join account_period ap
					on line.period_id = ap.id
				where account_id in {account_id}
			'''.format(account_id=account_ids, tax_rate=record.tax_id.amount)
			if len(partner_ids) == 1:
				partner_ids = '(' + str(partner_ids[0]) + ')'
			else:
				partner_ids = partner_ids
			if self.customer:
				partner_sql = ''' and partner_id in {partner_id}'''.format(partner_id=partner_ids)
			else:
				partner_sql = ' '
			sql += partner_sql
			start_period_date = record.start_period_id.date_start
			end_period_date = record.end_period_id.date_stop
			period_sql = ''' and ap.date_start >= '{start_period_id}' and ap.date_stop <= '{end_period_id}'  '''.format(
				start_period_id=start_period_date, end_period_id=end_period_date)
			sql += period_sql
			sql_income = 'group by account_id, partner_id, period_id, account_name, account_code,' \
						 'partner_name,period_code, ac_period'
			sql += sql_income
			cr.execute(sql)
			result = cr.dictfetchall()
			res_data += result
		return res_data

	def generate_domain(self):
		domain = [['company_id.code', '=', self.env.user.company_id.code],
				  ['contract_start', '>=', self.start_period.date_start],
				  ['contract_start', '<=', self.end_period.date_stop]]
		if self.customer:
			domain.append(['name', 'in', self.customer.mapped('name')])
		return [domain]

	def get_saas_customer_data(self):
		saas_re = {}
		odoorpc = OdooRpc(url=self.env['ir.config_parameter'].get_param('income.statement.url'),
						  db=self.env['ir.config_parameter'].get_param('income.statement.db'),
						  username=self.env['ir.config_parameter'].get_param('income.statement.username'),
						  password=self.env['ir.config_parameter'].get_param('income.statement.password'))
		domain = self.generate_domain()
		model_list = ['fresh_base.trans_undertake', 'fresh_base.stock_undertake',
					  'fresh_base.warehouse_undertake', 'fresh_base.trans_delegate_person',
					  'fresh_base.trans_delegate_company', 'fresh_base.warehouse_delegate',
					  # 'fresh_base.sale_contract','fresh_base.purchase_contract'
					  ]
		for model_name in model_list:
			saas_result = odoorpc.method(model_name=model_name, function_name='search_read',
										 domain=domain)
			for x in saas_result:
				customer_data = {
					'name': x.get('name', False),
					'type': x.get('type', False),
					'attr': x.get('attr', False),
					'bus_person': x.get('bus_person', False),
					'bus_person_site': x.get('bus_person_site', False),
					'phone': x.get('phone', False),
					'month_trans_income': x.get('month_trans_income', False),
					'contract_start': x.get('contract_start', False),
					'contract_end': x.get('contract_end', False),
					'expire_day': x.get('financial_account_period', False)
				}
				customer_name = x.get('name', False)
				saas_re.setdefault(customer_name, list())
				saas_re[customer_name].append(customer_data)
			# saas_re[x.get('name', False)] = customer_data
		return saas_re

	def print_to_excel(self):
		if not (self.start_period and self.end_period):
			raise UserError(u'必须选择开始期间和结束期间')
		report_name = 'income_statement.report_income_detail'
		saas_re = self.get_saas_customer_data()
		income_data = self.report_parameter()
		result = []
		for item in income_data:
			sum_amount = item['amount']
			account_name = item['account_name']
			account_code = item['account_code']
			partner_name = item['partner_name']
			period_code = item['period_code']
			tax_rate = item['tax_rate']
			ac_period = item['ac_period']
			# partner_type = partner.ptype_id.name
			tmp = {'sum_amount': sum_amount,
				   'account_name': account_code + account_name,
				   'partner_name': partner_name,
				   'period_code': period_code,
				   'account_tax': tax_rate,
				   'account_period': ac_period,
				   'contract_list': list(),
				   # 'partner_type': partner_type,
				   }
			tmp['contract_list'] = saas_re.get(partner_name, list())
			result.append(tmp)
		data = {
			"data": result,
		}
		return self.env['report'].get_action(self, report_name, data=data)
