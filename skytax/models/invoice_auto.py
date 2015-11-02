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
from datetime import date, timedelta
from openerp.osv import fields, osv

class invoice_auto(osv.osv):

    _name  = "invoice.auto"

    def action_generate(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        inv_obj = self.pool.get('account.invoice')
        print time.strftime('%Y-%m-%d')
        if time.strftime("%d") == '01' :
            print "test"
        #~ for data in  self.browse(cr, uid, [], context=context):
            #~ print data
        cr.execute('select id from account_invoice where date<%s and state =%s', (date.today()-timedelta(days=21),'draft'))
        invoice_ids = map(lambda x: x[0], cr.fetchall())
        inv_obj.action_confirm(cr, uid, line_ids, context=context)
        return True

invoice_auto()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
