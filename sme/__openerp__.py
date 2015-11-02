# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'SME Managment System',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 4,
    'summary': 'Sales, Accounting, Purchase, Inventory',
    'description': """SME Managment System""",
    'author': 'SKYGST',
    'website': 'https://www.skygst.com',
    'images': [],
    'depends': ['web','product','sale','purchase','account','account_voucher','mail','stock'],
    'data': [
        'security/groups_view.xml',
        
        'customer_details_view.xml',
        'company_view.xml',
        
        'sale_view.xml',
        'invoice_view.xml', 
                
        'data/report_paperformat.xml',
        
        'views/account_invoice_view.xml',
        'views/report.xml',
        'views/report_layout.xml',
        'views/report_purchaseorder.xml',
        'views/report_purchasequotation.xml',
        'views/report_invoice.xml',
        'views/report_account_voucher.xml',
        'views/report_saleorder.xml',
        'views/report_stockpicking.xml',
                
        'security/ir.model.access.csv'
    ],
    'css': ["static/src/css/custom.css"],
    'demo': [],
    'test': [],
    'qweb' : ["static/src/xml/pos.xml"],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
