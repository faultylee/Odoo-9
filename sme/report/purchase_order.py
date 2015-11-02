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

import time
from openerp.osv import osv
from openerp.report import report_sxw

class order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time, 
            'lines':self._lines,
        })
        
    def _lines(self, obj):
        cr = self.cr
        uid  = self.uid
        context = None
        lines = []
        try: 
            if obj:
                n=1
                for line in obj.order_line:
                    lines.append(line)
                    self.pool.get('purchase.order.line').write( cr,uid,line.id,{'no':n})
                    n+=1
        except:
            return False
        return lines
        
class report_purchase(osv.AbstractModel):
    _name = 'report.purchase.report_purchaseorder'
    _inherit = 'report.abstract_report'
    _template = 'purchase.report_purchaseorder'
    _wrapped_report_class = order
    
class report_purchase_quote(osv.AbstractModel):
    _name = 'report.purchase.report_purchasequotation'
    _inherit = 'report.abstract_report'
    _template = 'purchase.report_purchasequotation'
    _wrapped_report_class = order

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

