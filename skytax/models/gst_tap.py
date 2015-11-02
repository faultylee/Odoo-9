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
from openerp.osv import orm, fields,osv
import logging
import openerp.netsvc as netsvc
import StringIO
import base64
_logger = logging.getLogger(__name__)



class gst_tap_file(osv.osv):
    _name = 'gst.tap.file' 
    _columns = {
        'notes':fields.text('Details'),
        'data':fields.binary("GST TAP File",readonly=True),
        'name':fields.char("Filename",16,readonly=True),
        'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain = []),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'journal_ids': fields.many2many('account.journal', string='Journals', required=True),
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'due_date': fields.date("Due Date"),
        'write_date_txt': fields.datetime("Last Updated Date",readonly=True),
        'sr_tax': fields.float("SR (Tax)",readonly=True),
        'sr_base': fields.float("SR (Base)",readonly=True),
        't6_tax': fields.float("T6 (Tax)",readonly=True),
        't6_base': fields.float("T6 (Base)",readonly=True),
        'tx_tax': fields.float("TX (Tax)",readonly=True),
        'tx_base': fields.float("TX (Base)",readonly=True),
        'tx-re_tax': fields.float("TX-RE (Tax)",readonly=True),
        'tx-re_base': fields.float("TX-RE (Base)",readonly=True),
        'dmr_irr': fields.float("DMR/IRR (%)",readonly=True),
        
        'c1': fields.float("C1",readonly=True),
        'c2': fields.float("C2",readonly=True),
        'c3': fields.float("C3",readonly=True),
        'c4': fields.float("C4",readonly=True),
        'a1': fields.float("A1",readonly=True),
        'a2': fields.float("A2",readonly=True),
        'c6': fields.float("C6",readonly=True),
        'c7': fields.float("C7",readonly=True),
        'c8': fields.float("C8",readonly=True),
        'c9': fields.float("C9",readonly=True),
        'c10': fields.float("C10",readonly=True),
        'c11': fields.float("C11",readonly=True),
        'c12': fields.float("C12",readonly=True),
        'c13': fields.float("C13",readonly=True),
        'i14': fields.float("I14",readonly=True),
        'c15': fields.float("C15",readonly=True),
        'i16': fields.float("I16",readonly=True),
        'c17': fields.float("C17",readonly=True),
        'i18': fields.float("I18",readonly=True),
        'c19': fields.float("C19",readonly=True),
        'i20': fields.float("I20",readonly=True),
        'c21': fields.float("C21",readonly=True),
        'i22': fields.float("I22",readonly=True),
        'c23': fields.float("C23",readonly=True),
        'i24': fields.float("I24",readonly=True),
        }
        
    def _check_company_id(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context=context):
            company_id = wiz.company_id.id
            if wiz.fiscalyear_id and company_id != wiz.fiscalyear_id.company_id.id:
                return False
        return True

    _constraints = [
        #~ (_check_company_id, 'The fiscalyear, periods or chart of account chosen have to belong to the same company.', ['chart_account_id','fiscalyear_id','period_from','period_to']),
    ]

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        res = super(gst_tap_file, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context.get('active_model', False) == 'account.account':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='chart_account_id']")
            for node in nodes:
                node.set('readonly', '1')
                node.set('help', 'If you print the report from Account list/form view it will not consider Charts of account')
                setup_modifiers(node, res['fields']['chart_account_id'])
            res['arch'] = etree.tostring(doc)
        return res
    
    def onchange_chart_id(self, cr, uid, ids, chart_account_id=False, context=None):
        res = {}
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(cr, uid, chart_account_id, context=context).company_id.id
            now = time.strftime('%Y-%m-%d')
            domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
            res['value'] = {'company_id': company_id}
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {'value': {}}
        if filter == 'filter_date':
            res['value'] = {'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        return res

    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [], limit=1)
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
        
    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'filter': 'filter_date',
            'chart_account_id': _get_account,
    }
    
    def get_company_ids(self,cr,uid,ids,context=None):
        if context is None:
            context={}
        company_ids=[]
        for gst_tap in self.browse(cr,uid,ids):
            company_id = gst_tap.company_id.id
            child_ids = gst_tap.company_id.child_ids
            company_ids.append(company_id)
            for child in child_ids:
                if child.vat == gst_tap.company_id.vat:
                    company_ids.append(child.id)
        return company_ids

    def get_amount(self,cr,uid,ids,tax_code,date_from,date_to):
        company_ids = self.get_company_ids(cr,uid,ids)
        aml_obj = self.pool.get('account.move.line')
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code)])
        val=val1=val2=0.0
        if date_from or date_to:
            aml_ids=aml_obj.search(cr,uid,[('tax_line_id','in',account_tax_id),('date','>=',date_from),('date','<=',date_to),('move_id.state','=','posted')])
            for aml in aml_obj.browse(cr,uid,aml_ids):
                if aml.move_id.state == 'posted':
                    val1 += aml.debit
                    val2 += aml.credit
        if val1>val2:
            val = val1-val2
        else:
            val=val2-val1
        return val
    def get_value(self,cr,uid,ids,tax_code,date_from,date_to):
        context={}
        company_ids = self.get_company_ids(cr,uid,ids)
        aml_obj = self.pool.get('account.move.line')
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code),('company_id','in',company_ids)])
        res = {}
        val=val1=val2=0.0
        if date_from or date_to:
            aml_ids=aml_obj.search(cr,uid,[('tax_ids','in', account_tax_id),('date','>=',date_from),('date','<=',date_to),('move_id.state','=','posted')])
            for aml in aml_obj.browse(cr,uid,aml_ids):
                if aml.move_id.state == 'posted':
                    val1 += aml.debit
                    val2 += aml.credit
        if val1>val2:
            val = val1-val2
        else:
            val=val2-val1
        return val

    def get_bad_debt(self,cr,uid,ids,tax_code,account_code,date_from,date_to):
        company_ids = self.get_company_ids(cr,uid,ids)
        aml_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        #~ account_id = account_obj.search(cr,uid,[('description','ilike',account_code)])
        account_id = account_obj.search(cr,uid,[])
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code)])
        val=val1=val2=0.0
        acc_moves=[]
        if date_from or date_to:
            if account_id:
                    aml_ids=aml_obj.search(cr,uid,[('account_id','in',account_id),('date','>=',date_from),('date','<=',date_to),('move_id.state','=','posted')])
                    for aml in aml_obj.browse(cr,uid,aml_ids):
                        if aml.move_id.state == 'posted':
                            acc_moves.append(aml.move_id)
                    acc_moves = list(set(acc_moves))
                    for acc_move in acc_moves:
                        for line in acc_move.line_ids:
                            if account_tax_id:
                                for tax_line_br in account_tax_obj.browse(cr,uid,account_tax_id):
                                    tax_line_id = tax_line_br.id
                                    if line.tax_line_id.id == tax_line_id :
                                        val1 += line.debit
                                        val2 += line.credit
                                        val += aml.tax_amount
        return val
        
    def generate_txt(self, cr, uid, ids, data, context={}):
        company_ids = self.get_company_ids(cr,uid,ids)
        file_data=StringIO.StringIO()
        file_name = 'GST_Tap_File.txt'
        import getpass
        user = getpass.getuser()
        temp_path = '/home/' + user + '/' + file_name
        out = open(temp_path,'wb+')
        vals={}
        #~ company_name = "c1|c2|c3|c4|b5|c6|c7|c8|c9|c10|c11|c12|c13|i14|c15|i16|c17|i18|c19|i20|c21|i22|c23|c24\n"
        company_name = ""
        for report in self.browse(cr,uid,ids):
            date_from = report.date_from
            date_to = report.date_to
            lines2=self.get_value(cr,uid,ids,'SR',date_from,date_to)
            vals.update({'sr_base':lines2})
            lines3=self.get_value(cr,uid,ids,'DS',date_from,date_to)
            lines4=self.get_value(cr,uid,ids,'T6',date_from,date_to)
            vals.update({'t6_base':lines4})
            lines5=self.get_value(cr,uid,ids,'T0',date_from,date_to)
            five_a=lines2+lines3+lines4+lines5
            company_name+=str(five_a)+'|'#c1
            vals.update({'c1':five_a})
            lines2=self.get_amount(cr,uid,ids,'SR',date_from,date_to)
            vals.update({'sr_tax':lines2})
            lines3=self.get_amount(cr,uid,ids,'DS',date_from,date_to)
            lines4=self.get_amount(cr,uid,ids,'AJS',date_from,date_to)
            lines5=self.get_amount(cr,uid,ids,'T6',date_from,date_to)
            vals.update({'t6_tax':lines5})
            lines6=self.get_amount(cr,uid,ids,'T0',date_from,date_to)
            five_b=lines2+lines3+lines4+lines5+lines6
            company_name+=str(five_b)+'|'#c2
            vals.update({'c2':five_b})
            lines2=self.get_value(cr,uid,ids,'TX',date_from,date_to)
            vals.update({'tx_base':lines2})
            lines3=self.get_value(cr,uid,ids,'IM',date_from,date_to)
            lines4=self.get_value(cr,uid,ids,'TX-E43',date_from,date_to)
            lines5=self.get_value(cr,uid,ids,'TX-RE',date_from,date_to)
            vals.update({'tx-re_base':lines5})
            six_a=lines2+lines3+lines4+lines5
            company_name+=str(six_a)+'|'#c3
            vals.update({'c3':six_a})
            lines2=self.get_amount(cr,uid,ids,'TX',date_from,date_to)
            vals.update({'tx_tax':lines2})
            lines3=self.get_amount(cr,uid,ids,'IM',date_from,date_to)
            lines4=self.get_amount(cr,uid,ids,'TX-E43',date_from,date_to)
            T = self.get_value(cr,uid,ids,'SR',date_from,date_to) + self.get_value(cr,uid,ids,'T0',date_from,date_to) + self.get_value(cr,uid,ids,'T6',date_from,date_to) + self.get_value(cr,uid,ids,'ZRL',date_from,date_to) + self.get_value(cr,uid,ids,'ZRE',date_from,date_to) + self.get_value(cr,uid,ids,'DS',date_from,date_to) + self.get_value(cr,uid,ids,'OS',date_from,date_to) + self.get_value(cr,uid,ids,'RS',date_from,date_to) + self.get_value(cr,uid,ids,'GS',date_from,date_to)
            E = self.get_value(cr,uid,ids,'ES',date_from,date_to)
            lines5 = 0.0
            if T+E != 0:
                M = T/(T+E)
                Val = self.get_amount(cr,uid,ids,'TX-RE',date_from,date_to)
                lines5 = round(Val * M,2)
                vals.update({'dmr_irr':M})
            else:
                lines5 = 0.0
            vals.update({'tx-re_tax':lines5})
            lines6=self.get_amount(cr,uid,ids,'AJP',date_from,date_to)
            six_b=lines2+lines3+lines4+lines5+lines6
            company_name+=str(six_b)+'|'#c4
            vals.update({'c4':six_b})
            if five_b < six_b:
                a3= six_b-five_b
            else:
                a3=0.0
            vals.update({'a1':a3})
            if six_b < five_b:
                a4= five_b-six_b
            else:
                a4=0.0
            vals.update({'a2':a4})
            company_name+=str(0)+'|'#b5
            lines2=self.get_value(cr,uid,ids,'ZRL',date_from,date_to)
            company_name+=str(lines2)+'|'#c6
            vals.update({'c6':lines2})
            lines2=self.get_value(cr,uid,ids,'ZRE',date_from,date_to)
            company_name+=str(lines2)+'|'#c7
            vals.update({'c7':lines2})
            lines2=self.get_value(cr,uid,ids,'ES',date_from,date_to)
            lines3=self.get_value(cr,uid,ids,'ES43',date_from,date_to)
            es_12=lines2+lines3
            company_name+=str(es_12)+'|'#c8
            vals.update({'c8':es_12})
            lines2=self.get_value(cr,uid,ids,'RS',date_from,date_to)
            company_name+=str(lines2)+'|'#c9
            vals.update({'c9':lines2})
            lines2=self.get_value(cr,uid,ids,'IS',date_from,date_to)
            company_name+=str(lines2)+'|'#c10
            vals.update({'c10':lines2})
            lines2=self.get_bad_debt(cr,uid,ids,'TX-RE','2010/0',date_from,date_to)
            company_name+=str(lines2)+'|'#c11
            vals.update({'c11':lines2})
            lines2=self.get_bad_debt(cr,uid,ids,'AJP','8004/004',date_from,date_to)
            company_name+=str(lines2)+'|'#c12
            vals.update({'c12':lines2})
            lines2=self.get_bad_debt(cr,uid,ids,'AJS','8004/003',date_from,date_to)
            company_name+=str(lines2)+'|'#c13
            vals.update({'c13':lines2})
            company_name+='|' #i14
            company_name+='0.0|' #c15
            company_name+='|' #i16
            company_name+='0.0|' #c17
            company_name+='|' #i18
            company_name+='0.0|' #c19
            company_name+='|' #i20
            company_name+='0.0|' #c21
            company_name+='|' #i22
            company_name+='0.0|' #c23
            company_name+='0.0' #c24
        out.write(company_name)
        out.close
        data = base64.encodestring(company_name)
        vals.update({'data':data,'name':'GST Tap File'+'.txt','write_date_txt':report.write_date})
        self.write(cr,uid,ids,vals)
        return True

gst_tap_file()    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
