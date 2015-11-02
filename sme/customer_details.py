from datetime import datetime, timedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow

class customer(osv.osv):

    _name = _inherit = 'res.partner'
    _columns = {
            'co_reg':fields.char('Company Reg. No.'),
            'new_ic_number':fields.char('IC Number'),
            'gst_id' : fields.char('GST ID Number', size=12),
            'gst_date': fields.date('Date GST Status Verified', select=1),
            }
            
    _defaults ={ }
            
    _sql_constraints = [('co_reg_unique', 'unique (co_reg)', 'Company Reg Number must be unique per Customer!'),
                            ('gst_id_unique', 'unique (gst_id)', 'GST ID Number must be unique per Customer!'),
                            ('new_ic_number_unique', 'unique (new_ic_number)', 'IC Number must be unique per Customer!') ]
customer()
