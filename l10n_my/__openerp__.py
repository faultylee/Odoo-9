##############################################################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  
#  Copyright 2014 Mr <mr@A>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
###############################################################################
{
    'name': 'Malaysian - Accounting',
    'version': '1.0',
    'description': """
Malaysia accounting chart and localization.
=======================================================

After installing this module, the Configuration wizard for accounting is launched.
    * The Chart of Accounts consists of the list of all the general ledger accounts
      required to maintain the transactions of Malaysia.
    * On that particular wizard, you will be asked to pass the name of the company,
      the chart template to follow, the no. of digits to generate, the code for your
      account and bank account, currency to create journals.

    * The Chart of Taxes would display the different types/groups of taxes such as
      Standard Rates, Zeroed, Exempted and Out of Scope.
    * The tax codes are specified considering the Tax Group and for easy accessibility of
      submission of GST Tax Report.

    """,
    'author': 'Aravinth',
    'website': 'http://www.aravinth.co.in',
    'category': 'Localization/Account Charts',
    'depends': ['base', 'account'],
    'data': [
		'data/account_chart_template.xml',
        'data/account.account.template.csv',
        'data/account.chart.template.csv',
        'data/account.account.tag.csv',
        'data/account.tax.template.csv',
        'data/res.country.state.csv',
        'data/account_chart_template.yml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
