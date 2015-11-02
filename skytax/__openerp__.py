# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'GST 03',
    'version': '0.3',
    'license': 'AGPL-3',
    'author': 'Aravinth, Senthil',
    'category': 'Accounting & Finance',
    'sequence': 10,
    'summary': 'Customized For GST',
    'description': """ GST 03 Report """,
    'depends': [ 'account', 'report_xls'],
    'data': [
             'views/gaf_report_view.xml',
             'views/gst_summary_view.xml',
             'views/gst_tap_pdf.xml',
             'views/gst_tap_view.xml',
             'views/do_cron.xml',
             'security/ir.model.access.csv'
            ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'css': [],
    'js': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
