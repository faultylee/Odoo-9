# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
import os
import openerp
import pytz
import time
from datetime import datetime
from openerp import SUPERUSER_ID, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools import image_resize_image
import openerp.addons.decimal_precision as dp

class stock_picking(osv.osv):
    _name = _inherit = 'stock.picking'
    _columns = {
        'user_id': fields.many2one('res.users', 'Salesperson', states={'draft': [('readonly', False)], 'done': [('readonly', True)]}, select=True, track_visibility='onchange'),
        'partner_ref': fields.char('Reference', help="Supplier or Customer Reference Number"),
    }

    _defaults ={}
    def default_get(self, cr, uid, fields, context=None):
        res = super(stock_picking, self).default_get(cr, uid, fields, context=context)
        picking_type =  context.get('picking_type', False) or False
        picking_type_id =   False
        pick_type_obj = self.pool.get('stock.picking.type')
        if picking_type:
            picking_type_id = pick_type_obj.search(cr, uid, [('code','=',picking_type),('active','=',True)])
        if picking_type_id:
            res.update({'picking_type_id': picking_type_id[0]})
        return res

stock_picking()

class stock_move(osv.osv):

    _name = _inherit = 'stock.move'

    _columns = {
        'no': fields.char('Sl No.', help="Unique Number"),
    }
    
stock_move()

class stock_pack_operation(osv.osv):
    _name = _inherit = "stock.pack.operation"
    
    _columns = {
        'pack_no': fields.char('Pack Sl No.', help="Unique Number"),
        }

stock_pack_operation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
