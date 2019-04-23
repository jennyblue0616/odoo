# -*- coding: utf-8 -*-

from odoo import models, fields, api
from math import ceil
import logging
import time
from pprint import pformat

_logger = logging.getLogger(__name__)


class AccountMoveReportPrint(models.AbstractModel):
	_name = 'report.account_print_ext.report_account_move_print'

	def _paginate(self, items, max_per_page=5):
		"""
		分页函数
		items 为要分页的条目们
		max_per_page 设定每页条数
		返回：页数
		"""
		count = len(items)
		return int(ceil(float(count) / max_per_page))

	def _get_account_name(self, id):
		account_name = self.env['account.account'].browse(id).name_get()[0]
		# Account move print use Account here:
		return account_name[1]

	def _get_account_partner(self, id, name):
		value = 'account.account,' + str(id)
		partner_prop_acc = self.env['ir.property'].search([('value_reference', '=', value)], {})
		if partner_prop_acc:
			return name
		else:
			return False

	def _get_exchange_rate(self, line):
		'''
		Exchange rate: Debit or Credit / currency ammount
		Why not get it from currency code + date ?
		'''
		exchange_rate = False
		if line.amount_currency:
			if line.debit > 0:
				exchange_rate = line.debit / line.amount_currency
			if line.credit > 0:
				exchange_rate = line.credit / (-1 * line.amount_currency)
		return exchange_rate

	def _get_unit_price(self, line):
		'''
		Unit price：Debit or Credit / Quantity
		'''
		unit_price = False
		if line.quantity:
			if line.debit > 0:
				unit_price = line.debit / line.quantity
			if line.credit > 0:
				unit_price = line.credit / line.quantity
		return unit_price

	def _rmb_format(self, value):
		"""
		将数值按位数分开
		"""
		if value < 0.01:
			# 值为0的不输出，即返回12个空格
			return ['' for i in range(12)]
		# 先将数字转为字符，去掉小数点，然后和12个空格拼成列表，取最后12个元素返回
		return (['' for i in range(12)] + list(('%0.2f' % value).replace('.', '')))[-12:]

	def _rmb_upper(self, value):
		"""
		人民币大写
		来自：http://topic.csdn.net/u/20091129/20/b778a93d-9f8f-4829-9297-d05b08a23f80.html
		传入浮点类型的值返回 unicode 字符串
		"""
		rmbmap = [u"零", u"壹", u"贰", u"叁", u"肆", u"伍", u"陆", u"柒", u"捌", u"玖"]
		unit = [u"分", u"角", u"元", u"拾", u"佰", u"仟", u"万", u"拾", u"佰", u"仟", u"亿",
				u"拾", u"佰", u"仟", u"万", u"拾", u"佰", u"仟", u"兆"]

		nums = map(int, list(str('%0.2f' % value).replace('.', '')))
		words = []
		zflag = 0  # 标记连续0次数，以删除万字，或适时插入零字
		start = len(nums) - 3
		for i in range(start, -3, -1):  # 使i对应实际位数，负数为角分
			if 0 != nums[start - i] or len(words) == 0:
				if zflag:
					words.append(rmbmap[0])
					zflag = 0
				words.append(rmbmap[nums[start - i]])
				words.append(unit[i + 2])
			elif 0 == i or (0 == i % 4 and zflag < 3):  # 控制‘万/元’
				words.append(unit[i + 2])
				zflag = 0
			else:
				zflag += 1

		if words[-1] != unit[0]:  # 结尾非‘分’补整字
			words.append(u"整")
		return ''.join(words)

	def _print_ext(self, id):
		return []

	def _get_page_ext(self, id):
		"""计算页数"""
		lists = []
		list = self._print_ext(id)
		length = len(list)
		lent = 0
		if length % 10 == 0:
			lent = length / 10
		else:
			lent = length / 10 + 1
		i = 1
		while i <= lent:
			lists.append(i * 10)
			i += 1
		return lists


class AccountMoveLine(models.Model):
	_inherit = 'account.move'

	gross_amount_ext = fields.Char(string=u"总额")


class AccountMoveReportOne(models.AbstractModel):
	_name = 'report.account_print_ext.report_account_move'
	_inherit = 'report.account_print_ext.report_account_move_print'

	def parse_account_code(self, num, accounts, res):
		res.append(accounts)
		accounts = accounts.parent_id
		if not accounts.parent_id:
			res.append(accounts)
			if len(res) > num:
				return res[::-1][num - 1].code
			else:
				return res[::-1][-1].code
		return self.parse_account_code(num, accounts, res)

	def get_id(self, id):
		"""获取凭证中科目的id"""
		move_id = self.env['account.move'].search([('id', '=', id), ('company_id', '=', self.env.user.company_id.id)])
		items = []
		if move_id.line_ids:
			for line in move_id.line_ids:
				id = line.id
				items.append(id)
		return items

	def unique_code(self, id, print_level):
		move_id = self.env['account.move'].search([('id', '=', id), ('company_id', '=', self.env.user.company_id.id)])
		list1 = []
		if move_id.line_ids:
			for line in move_id.line_ids:
				code = self.parse_account_code(print_level, accounts=line.account_id, res=[])
				list1.append(code)
			list2 = []
			list2 = [i for i in list1 if i not in list2]
			return list2
		return []

	def _print_ext(self, id):
		_logger.info({
			'self._context': self._context
		})
		# {'self._context': {'lang': u'zh_CN', 'edit_translations': False, 'tz': u'Asia/Shanghai', 'uid': 199,
		# 				   u'active_model': u'account.print.wizard', 'website_id': 1, u'ids': [671971, 671968],
		# 				   u'active_id': 72, u'params': {u'action': 1010}, u'search_disable_custom_filters': True,
		# 				   u'active_ids': [72], u'account_level': 2}}
		print_level = self._context.get('account_level')
		lists = []
		items = self.get_id(id)
		codes = self.unique_code(id,print_level)
		# 	[u'2221.03.01', u'1002.01.03', u'6602.04']
		for code in codes:
			res = self.env['account.move.line'].search([('account_id.code', 'like', code), ('id', 'in', items)])
			# account.move.line(2848136, 2848199)
			sum_debit = sum(x.debit for x in res)
			sum_credit = sum(x.credit for x in res)
			account_id = self.env['account.account'].search(
				[('code', '=', code), ('company_id', '=', self.env.user.company_id.id)])
			account_name = code + account_id.name
			data = {
				'name': u'详情请见明细页',
				'code': code,
				'account_name': account_name,
				'debit': sum_debit,
				'credit': sum_credit,
			}
			lists.append(data)
		return lists

	@api.model
	def render_html(self, docids, data=None):
		_logger.info('----------------')
		_logger.info({
			'data': data,
			'ids': self._context.get('active_ids')
		})
		# {'data': {u'ids': [671971, 671968],
		# 		  'context': {u'tz': u'Asia/Shanghai', u'uid': 199, u'active_model': u'account.print.wizard',
		# 					  u'ids': [671971, 671968], u'params': {u'action': 1010},
		# 					  u'search_disable_custom_filters': True, u'active_ids': [72], u'account_level': 2,
		# 					  u'active_id': 72}, u'account_level': 2}, 'ids': [72]}
		docids = data.get('ids')
		report_obj = self.env['report']
		docs = self.env['account.move'].sudo().browse(docids)
		for doc in docs:
			doc.gross_amount_ext = ("%.2f" % doc.amount)
		docargs = {
			'docs': docs,
			'lists': self._print_ext,
			'line_num': 10,
			'page': self._get_page_ext,
		}
		return report_obj.render('account_print_ext.report_account_move', docargs)
