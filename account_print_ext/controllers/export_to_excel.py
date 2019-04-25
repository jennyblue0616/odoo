# -*- coding: utf-8 -*-

import simplejson
from copy import copy
from odoo import http
from odoo.http import request
import xlwt
import logging

_logger = logging.getLogger(__name__)
try:
	import StringIO
except ImportError:
	from io import StringIO


class account_report(http.Controller):
	@http.route(['/report/account_print_ext.account_report'], type='http', auth='user', multilang=True)
	def account_report(self, **data):
		data = simplejson.loads(data['options'])
		id = data.get('ids')
		move_id = request.env['account.move'].search([('id', '=', id)])
		workbook = xlwt.Workbook(encoding='utf-8')
		sheet = workbook.add_sheet(u'sheet', cell_overwrite_ok=True)
		row = [u'摘要', u'会计科目', u'现金流量表行', u'分析账户', u'合作伙伴', u'车辆', u'借方', u'贷方']
		for i in range(0, len(row)):
			sheet.write(0, i, row[i])
		sheet.write(1, 0, u'详情见摘要')
		account_line = move_id.line_ids
		length = len(move_id.line_ids)
		width = len(row)
		# 长度 5 行
		# 宽度 8 列
		accounts = move_id.line_ids.mapped('account_id')
		for j in range(1, length):
			sheet.write(j, 1, accounts[j].name)
			sheet.write(j, width-2, account_line[j].debit)
			sheet.write(j, width-1, account_line[j].credit)
		sheet.write(length-1,0, move_id.attachment_num)
		sheet.write_merge(length-1, length-1, 1, width-4)
		sheet.write(length-1, 1, u'合计')
		sheet.write(length-1, width-2, move_id.gross_amount_ext)
		sheet.write(length-1, width-1, move_id.gross_amount_ext)
		sio = StringIO.StringIO()
		workbook.save(sio)
		sio.seek(0)
		content = sio.read()
		return request.make_response(content, headers=[
			('Content-Type', 'application/vnd.ms-excel'),
			('Content-Disposition', 'attachment; filename=%s.xlsx;'%(id))
		])
