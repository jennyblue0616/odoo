# -*- coding: utf-8 -*-
import xmlrpclib


class OdooRpc(object):
	def __init__(self, url, db, username, password):
		self.url = url
		self.db = db
		self.username = username
		self.password = password

	def method(self, model_name, function_name, domain):
		common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
		uid = common.authenticate(self.db, self.username, self.password, {})
		models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
		company_id = models.execute_kw(self.db, uid, self.password, model_name, function_name, domain)
		return company_id
