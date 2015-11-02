# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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

import time
from openerp.tools.translate import _
from openerp.osv import orm, fields
import logging
_logger = logging.getLogger(__name__)

class gst_period(orm.TransientModel):
    _name = 'wiz.gst.period' 
    _description = 'Print GST03'
    
    def _get_fiscal_year(self, cr, uid, context=None):
        year = self.pool.get('account.fiscalyear').search(cr, uid, [('state', '=', 'draft'),], limit=1 )
        return year and year[0] or False
        
    def _get_periods(self, cr, uid, context=None):
        period_ids = self.pool.get('account.period').search(cr, uid, [('special','=',False),('state', '=', 'draft'),('fiscalyear_id','=',self._get_fiscal_year(cr,uid,{}))], )
        return period_ids or False
    
    _columns = {
        'company_id': fields.many2one('res.company', 'Company Name', readonly=False)
    }    
    _defaults={
        #~ 'fiscalyear_id':_get_fiscal_year,
        #~ 'period_ids':_get_periods,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        company_id = data['company_id'][0]
        data.update({
            'company_id': company_id,
            'model': 'account.move',
        })
        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'gst03',
                    'datas': data}
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'gst.print',
                'datas': data}

    def xls_export(self, cr, uid, ids, context=None):
        return self.print_report(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
