from openerp import SUPERUSER_ID
from openerp import tools
from datetime import datetime
from openerp.osv import osv, fields, expression
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import psycopg2

import openerp.addons.decimal_precision as dp

class purchase_order_line(osv.osv):
    _name = _inherit = 'purchase.order.line'
    _columns = {
        'no': fields.char('Sl No.', help="Unique Number"),
    }
purchase_order_line()
