# -*- coding: utf-8 -*-

import simplejson
from odoo import http
from odoo.http import request
import xlwt
import logging

_logger = logging.getLogger(__name__)
try:
	import StringIO
except ImportError:
	from io import StringIO

row = [u'公司名称', u'客户名称', u'本年新增', u'客户类型', u'业务模式', u'收入类型', u'月份', u'不含税收入', u'税率', u'含税收入', u'考核调整金额', u'已对账',
	   u'开票日期', u'收款日期', u'账期', u'客户类型', u'客户属性', u'业务接口人', u'职务', u'电话', u'月度运输收入(预估)',
	   u'合同签订日期', u'合同到期日', u'财务账期(天)']
style = xlwt.XFStyle()
font = xlwt.Font()
font.height = 20 * 10
style.num_format_str = '_(#,##0.00_);(#,##0.00)'
style.alignment.horz = 0x02
style.font = font

class income_report(http.Controller):
	@http.route(['/report/income_statement.report_income_detail'], type='http', auth='user', multilang=True)
	def report_income_detail(self, **data):
		data = simplejson.loads(data['options'])
		result = data.get('data')
		length = len(result)
		workbook = xlwt.Workbook(encoding='utf-8')
		sheet = workbook.add_sheet(u'sheet', cell_overwrite_ok=True)
		sheet.write_merge(0, 0, 0, 14, u'财务系统内数据（总数与月度收入匹配）', style)
		sheet.write_merge(0, 0, 15, 23, u'SAAS台账系统中导出（已录入合同）', style)
		for i in range(0, len(row)):
			sheet.write(1, i, row[i])
		body_row_idx = 2
		for idx, line in enumerate(result):
			sheet.write(body_row_idx, 0, request.env.user.company_id.name)
			sheet.write(body_row_idx, 1, line.get('partner_name', False))
			sheet.write(body_row_idx, 3, line.get('partner_type', False))
			sheet.write(body_row_idx, 5, line.get('account_name', False))
			sheet.write(body_row_idx, 6, line.get('period_code', False))
			sheet.write(body_row_idx, 7, line.get('sum_amount', False), style)
			sheet.write(body_row_idx, 8, str(line.get('account_tax', False))+'%')
			income_tax = line.get('account_tax', False) * 0.01
			income_taxed = xlwt.Formula('H{index} * (1+{tax})'.format(index=body_row_idx+1,tax=income_tax ))
			sheet.write(body_row_idx, 9, income_taxed, style)
			account_period = line.get('account_period', False)
			if not account_period:
				account_period = 30
			sheet.write(body_row_idx, 14, account_period)
			for contract_data in line.get('contract_list', list()):
				sheet.write(body_row_idx, 15, contract_data.get('type'))
				sheet.write(body_row_idx, 16, contract_data.get('attr'))
				sheet.write(body_row_idx, 17, contract_data.get('bus_person'))
				sheet.write(body_row_idx, 18, contract_data.get('bus_person_site'))
				sheet.write(body_row_idx, 19, contract_data.get('phone'))
				sheet.write(body_row_idx, 20, contract_data.get('month_trans_income'))
				sheet.write(body_row_idx, 21, contract_data.get('contract_start'))
				sheet.write(body_row_idx, 22, contract_data.get('contract_end'))
				sheet.write(body_row_idx, 23, contract_data.get('expire_day'))
				body_row_idx += 1
		sio = StringIO.StringIO()
		workbook.save(sio)
		sio.seek(0)
		content = sio.read()
		return request.make_response(content, headers=[
			('Content-Type', 'application/vnd.ms-excel'),
			('Content-Disposition', 'attachment; filename=%s.xlsx;'%(u'income_sheet'))
		])
