# -*- coding: utf-8 -*-
{
    'name': '凭证打印扩展',
    "summary": "凭证打印扩展",
    'description': """
扩展凭证科目合并打印功能
""",
    'author': "Inspur LiHaoWei",
    'license': 'AGPL-3',
    "depends": [
        'account_accountant','account_cancel','account_period','account_hierarchy'
    ],
    "data": [
        'security/ir.model.access.csv',
        'report/account_move_report.xml',
        'wizard/print_wizard.xml',
        # 'views/print_account_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
