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

import xlwt
import time
from datetime import datetime
import format_common
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell, _render
from openerp.tools.translate import translate, _
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'gst' # To DO : create translation table

class gst_print_xls(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(gst_print_xls, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'datetime': datetime,
            '_': self._,
        })
        
    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) or src

class gst_xls(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(gst_xls, self).__init__(name, table, rml, parser, header, store)

        # XLS Template

    def _build_codes_dict(self, tax_code, res={}, context=None):
        if context is None:
            context = {}
        tax_pool = self.pool.get('account.tax')
        if tax_code.sum_period:
            if res.get(tax_code.name, False):
                raise orm.except_orm(_('Error'), _('Too many occurences of tax code %s') % tax_code.name)
            # search for taxes linked to that code
            tax_ids = tax_pool.search(self.cr, self.uid, [('tax_code_id', '=', tax_code.id)], context=context)
            if tax_ids:
                tax = tax_pool.browse(self.cr, self.uid, tax_ids[0], context=context)
                # search for the related base code
                base_code = tax.base_code_id or tax.parent_id and tax.parent_id.base_code_id or False
                if not base_code:
                    raise orm.except_orm(_('Error'), _('No base code found for tax code %s') % tax_code.name)
                # check if every tax is linked to the same tax code and base code
                for tax in tax_pool.browse(self.cr, self.uid, tax_ids, context=context):
                    test_base_code = tax.base_code_id or tax.parent_id and tax.parent_id.base_code_id or False
                    if test_base_code.id != base_code.id:
                        raise orm.except_orm(_('Error'), _('Not every tax linked to tax code %s is linked the same base code') % tax_code.name)
                res[tax_code.name] = {
                    'vat': tax_code.sum_period,
                    'base': base_code.sum_period,
                    }
            for child_code in tax_code.child_ids:
                res = self._build_codes_dict(child_code, res=res, context=context)
        return res

    def get_bad_debt(self,tax_code,account_code,period_id,company_id):
        cr=self.cr
        uid=self.uid
        period_obj = self.pool.get('account.period')
        aml_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        account_id = account_obj.search(cr,uid,[('code','ilike',account_code)])
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code)])
        val=val1=val2=0.0
        acc_moves=[]
        if account_id:
            aml_ids=aml_obj.search(cr,uid,[('account_id','in',account_id),('move_id.state','=','posted')])
            for aml in aml_obj.browse(cr,uid,aml_ids):
                if aml.move_id.period_id.id == period_id and aml.move_id.state == 'posted':
                    acc_moves.append(aml.move_id)
            acc_moves = list(set(acc_moves))
            for acc_move in acc_moves:
                for line in acc_move.line_id:
                    if account_tax_id:
                        for tax_code in account_tax_obj.browse(cr,uid,account_tax_id):
                            tax_code_id = tax_code.base_code_id.id
                            if line.tax_code_id.id == tax_code_id :
                                val1 += line.debit
                                val2 += line.credit
        if val1>val2:
            val = val1-val2
        else:
            val=val2-val1
        return val
    def get_amount(self,tax_code,period_id,company_id):
        context={}
        cr = self.cr
        uid=self.uid
        period_obj = self.pool.get('account.period')
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code)])
        res = {}
        val=val1=val2=0.0
        if account_tax_id:
            for tax_line in  account_tax_obj.browse(cr,uid,account_tax_id):
                tax_line_id = tax_code.id
                context['period_id'] = period_id
                aml_obj = self.pool.get('account.move.line')
                aml_ids=aml_obj.search(cr,uid,[('tax_line_id','=',tax_line_id),('move_id.state','=','posted')])
                
                for aml in aml_obj.browse(cr,uid,aml_ids):
                    if aml.move_id.period_id.id == period_id and aml.move_id.state == 'posted':
                        val1 += aml.debit
                        val2 += aml.credit
        if val1>val2:
            val = val1-val2
        else:
            val=val2-val1
        return val

    def get_value(self,tax_codecompany_id):
        context={}
        cr = self.cr
        uid=self.uid
        period_obj = self.pool.get('account.period')
        aml_obj = self.pool.get('account.move.line')
        account_tax_obj = self.pool.get('account.tax')
        account_tax_id = account_tax_obj.search(cr,uid,[('description','=',tax_code)],context=context)
        res = {}
        tax_code_id=[]
        if account_tax_id:
            for tax_line_br in account_tax_obj.browse(cr,uid,account_tax_id):
                tax_line_id.append(tax_line_br.id)
        val=val1=val2=0.0
        aml_ids=aml_obj.search(cr,uid,[('tax_line_id','in',tax_line_id),('move_id.state','=','posted')])
        for aml in aml_obj.browse(cr,uid,aml_ids):
            if aml.move_id.state == 'posted':
                val1 += aml.debit
                val2 += aml.credit
        if val1>val2:
            val = val1-val2
        else:
            val=val2-val1
        return val


    def inv_report(self,data,inv_type):
        cr=self.cr
        uid=self.uid
        account_obj = self.pool.get('account.account')
        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        company_id = data['company_id']
        # If you want to add partner means put this ---------- p.name as p_name,
        self.cr.execute("""SELECT  ai.date_invoice as inv_date,
            ai.internal_number as inv_number,
             (ail.quantity*ail.price_unit) as inv_total,ail.name  as inv_product_name,
             atax.description as Tax ,
             CASE WHEN atax.price_include =FALSE THEN  (ail.quantity*ail.price_unit * atax.amount) ElSE ((ail.quantity*ail.price_unit)-ail.price_subtotal) END  as TaxAmount
            FROM account_invoice ai
            JOIN account_invoice_line ail ON ail.invoice_id = ai.id
            JOIN account_invoice_line_tax  ailtax ON ailtax.invoice_line_id = ail.id
            JOIN account_tax atax ON atax.id = ailtax.tax_id
            JOIN res_partner p ON ai.partner_id = p.id
          
            WHERE ai.company_id = %s  AND ai.type=%s  AND ai.state in ('open','paid')
            ORDER BY  inv_number,inv_date

            """%(company_id,inv_type))
        lines = self.cr.dictfetchall()
        return lines

    def pos_report(self,data):
        cr=self.cr
        uid=self.uid
        account_obj = self.pool.get('account.account')
        company_id = data['company_id']
        # If you want to add partner means put this ---------- p.name as p_name,
        self.cr.execute("""SELECT  ai.date_order as inv_date,
            ai.name as inv_number,
            (ail.qty*ail.price_unit) as inv_total,ail.name  as inv_product_name,
            acc_tax.description as taxcode,
            (ail.price_subtotal_incl-ail.price_subtotal) as Tax
            FROM pos_order ai
            JOIN pos_order_line ail ON ail.order_id = ai.id
            JOIN account_move  am ON am.id = ai.account_move
            JOIN product_taxes_rel prod_tax ON prod_tax.prod_id = ail.product_id
            JOIN account_tax acc_tax ON acc_tax.id = prod_tax.tax_id
            WHERE ai.company_id = %s 
            ORDER BY  inv_number,inv_date

            """%(company_id))
        lines = self.cr.dictfetchall()
        return lines

    def annual_adjustment_report(self,data,inv_type):
        cr=self.cr
        uid=self.uid
        #~ context = self.context 
        account_obj = self.pool.get('account.account')
        company_id = data['company_id']
        period_ids = data['period_ids']
        # If you want to add partner means put this ---------- p.name as p_name
        query = """SELECT  ai.date_invoice as inv_date,
            ai.internal_number as inv_number,
            (ail.quantity*ail.price_unit) as inv_total,ail.name  as inv_product_name,
            atax.description as ztax ,
            CASE WHEN atax.price_include =FALSE THEN  (ail.quantity*ail.price_unit * atax.amount) ElSE ((ail.quantity*ail.price_unit)-ail.price_subtotal) END  as TaxAmount,
            ai.period_id as tperiod
            FROM account_invoice ai
            JOIN account_invoice_line ail ON ail.invoice_id = ai.id
            JOIN account_invoice_line_tax  ailtax ON ailtax.invoice_line_id = ail.id
            JOIN account_tax atax ON atax.id = ailtax.tax_id
            JOIN res_partner p ON ai.partner_id = p.id
          
            WHERE  atax.description =%s AND ai.company_id = %s  AND ai.type=%s AND ai.state in ('open','paid')  AND"""
        #~ if len(period_ids) >1:
            #~ cond="""
            #~ ORDER BY  inv_number,inv_date"""
            #~ period_ids = tuple(period_ids)
        #~ else:
        cond="""
        ORDER BY  inv_number,inv_date
        """
        sql = str(query+""" """ + cond)
        code = "'TX-RE'"
        self.cr.execute(sql%(code,company_id,inv_type))
        lines = self.cr.dictfetchall()
        return lines

    def irr(self,period_id,company_id):
        T = self.get_value('SR',company_id) + self.get_value('T6',company_id) + self.get_value('T0',company_id) + self.get_value('ZRL',company_id) + self.get_value('ZRE',company_id) + self.get_value('DS',company_id) + self.get_value('OS',company_id) + self.get_value('RS',company_id) + self.get_value('GS',company_id)
        E = self.get_value('ES',company_id)
        if T+E != 0 :
            IRR = round((T/(T+E)*100),2)
            DMR = round((E/(T+E)*100),2)
        else:
            IRR =0.0
            DMR =0.0

        if DMR <= 5 and E <= 5000:
            STATUS = 'qualify'
        else:
            STATUS = 'not qualify'
        return IRR,DMR,STATUS
        
    def generate_xls_report(self, _p, _xs, data, objects, wb,context=None):

        #~ # To DO : adapt to allow rendering space extensions by inherited module
        ws_o = wb.add_sheet('GST-03')
        ws_d = wb.add_sheet('GST Summary')
        
        ########### Report Styles ##############
        
        M_header_tstyle1 = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=400, color='grey')
        M_header_tstyle = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=200, color='yellow')
        header_tstyle = format_common.font_style(position='left', bold=1, border=1, fontos='black', font_height=180, color='green')
        header_tstyle_c = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=180, color='green')
        header_tstyle_r = format_common.font_style(position='right', bold=1, border=1, fontos='black', font_height=180, color='green')
        view_tstyle = format_common.font_style(position='left', bold=1, fontos='black', font_height=180)
        view_tstyle_r = format_common.font_style(position='right', bold=1, fontos='black', font_height=180)
        other_tstyle1 = format_common.font_style(fontos='black', border=1, font_height=180)
        other_tstyle = format_common.font_style(position='right', fontos='black', border=1, font_height=180)
        other_tstyle_l = format_common.font_style(position='left', bold=1, fontos='black', border=1, font_height=180)
        other_tstyle_c = format_common.font_style(position='center', fontos='black', font_height=180)

        #~ period_br = account_period_obj.browse(self.cr,self.uid, data['period_ids'])
        #~ company_id = data['company_id']
        wk={}
        
        #~ for period in period_br:
            #~ sheet_name = 'For - '+ period.name
            #~ sheet_name = sheet_name.replace('/', '-')
            #~ wk[period.name] = wb.add_sheet(sheet_name)
            #~ data1 = self.inv_report(data,period,"'out_invoice'")
            #~ i=0;j=0;k=0;l=0;m=0;n=0;o=0;p=0;
            #~ if data1:
                #~ columns = sorted(list(data1[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write_merge(0, 0, 0, 5, 'GST Transaction Listing', M_header_tstyle1)
                #~ wk[period.name].write(1,2,"Supply",M_header_tstyle)
                #~ wk[period.name].write(2,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(2,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(2,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(2,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(2,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(2,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ wk[period.name].row(0).height = 256 * 3
                #~ for i, row in enumerate(data1,3):
                    #~ for j, col in enumerate(columns):
                        #~ if j==5 or j==3:
                            #~ row[col] = round(row[col],2)
                        #~ wk[period.name].write(i, j, row[col], other_tstyle1)
            #~ data2 = self.inv_report(data,period,"'in_invoice'")
            #~ if data2:
                #~ columns = sorted(list(data2[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write(i+4,2,"Purchase",M_header_tstyle)
                #~ wk[period.name].write(i+5,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(i+5,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(i+5,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(i+5,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(i+5,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(i+5,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ for m, row in enumerate(data2):
                    #~ for j, col in enumerate(columns):
                        #~ if j==5 or j==3:
                            #~ row[col] = round(row[col],2)
                        #~ wk[period.name].write(i+m+6, j, row[col], other_tstyle1)
            #~ data3 = self.inv_report(data,period,"'out_refund'")
            #~ if data3:
                #~ columns = sorted(list(data3[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write(i+m+7,2,"Supply Credit Note",M_header_tstyle)
                #~ wk[period.name].write(i+m+8,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(i+m+8,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(i+m+8,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(i+m+8,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(i+m+8,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(i+m+8,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ for n, row in enumerate(data3):
                    #~ for j, col in enumerate(columns):
                       #~ wk[period.name].write(i+m+n+9, j, row[col], other_tstyle1)
            #~ data4 = self.inv_report(data,period,"'in_refund'")
            #~ if data4:
                #~ columns = sorted(list(data4[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write(i+m+n+11,2,"Purchase Credit Note",M_header_tstyle)
                #~ wk[period.name].write(i+m+n+12,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+12,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+12,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+12,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+12,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+12,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ for o, row in enumerate(data4):
                    #~ for j, col in enumerate(columns):
                       #~ wk[period.name].write(i+m+n+o+13, j, row[col], other_tstyle1)
            #~ data5 = self.inv_report(data,period,"'in_debitnote'")
            #~ if data5:
                #~ columns = sorted(list(data5[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write(i+m+n+o+15,2,"Supply Debit Note",M_header_tstyle)
                #~ wk[period.name].write(i+m+n+o+16,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+16,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+16,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+16,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+16,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+16,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ for p, row in enumerate(data5):
                    #~ for j, col in enumerate(columns):
                       #~ wk[period.name].write(i+m+n+o+p+17, j, row[col], other_tstyle1)
            #~ data6 = self.inv_report(data,period,"'out_debitnote'")
            #~ if data6:
                #~ columns = sorted(list(data6[0].keys())) # list() is not need in Python 2.x
                #~ wk[period.name].write(i+m+n+o+p+19,2,"Purchase Debit Note",M_header_tstyle)
                #~ wk[period.name].write(i+m+n+o+p+20,0,"Date",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+p+20,1,"Invoice Number",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+p+20,2,"Product Detail",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+p+20,3,"Amount",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+p+20,4,"Tax Code",header_tstyle_c)
                #~ wk[period.name].write(i+m+n+o+p+20,5,"GST",header_tstyle_c)
                #~ wk[period.name].col(0).width = 256 * 15
                #~ wk[period.name].col(1).width = 256 * 20
                #~ wk[period.name].col(2).width = 256 * 50
                #~ wk[period.name].col(4).width = 256 * 10
                #~ wk[period.name].col(5).width = 256 * 10
                #~ for q, row in enumerate(data6):
                    #~ for j, col in enumerate(columns):
                       #~ wk[period.name].write(i+m+n+o+p+q+21, j, row[col], other_tstyle1)
            #~ pos_installed = False
            #~ ir_model_obj = self.pool.get('ir.model')
            #~ pos_installed = ir_model_obj.search(self.cr,self.uid,[('model','=','pos.order')])
            #~ if pos_installed:
                #~ data7 = self.pos_report(data,period)
                #~ if data7:
                    #~ columns = sorted(list(data7[0].keys())) # list() is not need in Python 2.x
                    #~ wk[period.name].write(i+m+n+o+p+23,2,"POS",M_header_tstyle)
                    #~ wk[period.name].write(i+m+n+o+p+24,0,"Date",header_tstyle_c)
                    #~ wk[period.name].write(i+m+n+o+p+24,1,"Order Number",header_tstyle_c)
                    #~ wk[period.name].write(i+m+n+o+p+24,2,"Product Detail",header_tstyle_c)
                    #~ wk[period.name].write(i+m+n+o+p+24,3,"Amount",header_tstyle_c)
                    #~ wk[period.name].write(i+m+n+o+p+24,4,"GST",header_tstyle_c)
                    #~ wk[period.name].write(i+m+n+o+p+24,5,"Tax Code",header_tstyle_c)
                    #~ wk[period.name].col(0).width = 256 * 15
                    #~ wk[period.name].col(1).width = 256 * 20
                    #~ wk[period.name].col(2).width = 256 * 50
                    #~ wk[period.name].col(4).width = 256 * 10
                    #~ wk[period.name].col(5).width = 256 * 10
                    #~ for q, row in enumerate(data7):
                        #~ for j, col in enumerate(columns):
                           #~ wk[period.name].write(i+m+n+o+p+q+25, j, row[col], other_tstyle1)
        #~ 
        for ws in [ws_o,ws_d]:
            ws.panes_frozen = True
            ws.remove_splits = True
            ws.portrait = 0 # Landscape
            ws.fit_width_to_pages = 1

        row_pos_o = 0
        row_pos_d = 0
       
        for ws in [ws_o,ws_d]:
            ws.header_str = self.xls_headers['standard']
            ws.footer_str = self.xls_footers['standard']
        
        ws_o.write(0, 0, 'GST O3', M_header_tstyle)
        ws_o.write(2, 0, 'Item', header_tstyle)
        ws_o.write(2, 1, 'Details', header_tstyle)
        ws_o.col(1).width = 256 * 80
        ws_o.col(11).width = 256 * 12

        ws_o.write(3, 0, '5', other_tstyle_l)
        ws_o.write(3, 1, 'Output tax', other_tstyle_l)
        ws_o.write(4, 1, 'a) Total Value of Standard Rate Supply * ', other_tstyle_l)
        ws_o.write(5, 1, 'b) Total Output Tax (Inclusive of Bad Debt Recovered & other Adjustments)', other_tstyle_l)
        ws_o.write(7, 0, '6', other_tstyle_l)
        ws_o.write(7, 1, 'Input tax', other_tstyle_l)
        ws_o.write(8, 1, 'a) Total Value of Standard Rated Acquisition * ', other_tstyle_l)
        ws_o.write(9, 1, 'b) Total Input Tax (Inclusive of Bad Debt Relief & other Adjustments) *', other_tstyle_l)
        ws_o.write(11, 0, '7', other_tstyle_l)
        ws_o.write(11, 1, 'GST Amount Payable (Item 5b - Item 6b) *', other_tstyle_l)
        ws_o.write(12, 0, '8', other_tstyle_l)
        ws_o.write(12, 1, 'GST Amount Claimable (Item 6b - Item 5b) *', other_tstyle_l)   
        ws_o.write(14, 0, '10',other_tstyle_l)
        ws_o.write(14, 1, 'Total Value of Local Zero-Rated Supplies *',other_tstyle_l)
        ws_o.write(15, 0, '11',other_tstyle_l)
        ws_o.write(15, 1, 'Total Value of Export Supplies *',other_tstyle_l)
        ws_o.write(16, 0, '12',other_tstyle_l)
        ws_o.write(16, 1, 'Total Value of Exempt Supplies *',other_tstyle_l)
        ws_o.write(17, 0, '13',other_tstyle_l)
        ws_o.write(17, 1, 'Total Value of Supplies Granted GST Relief *',other_tstyle_l)
        ws_o.write(19, 0, '14',other_tstyle_l)
        ws_o.write(19, 1, 'Total Value of Goods Imported Under Approved Trader Scheme *',other_tstyle_l)
        ws_o.write(20, 0, '15',other_tstyle_l)
        ws_o.write(20, 1, 'Total Value of GST Suspended  under item 14  *',other_tstyle_l)
        ws_o.write(22, 0, '16',other_tstyle_l)
        ws_o.write(22, 1, 'Total Value of Capital Goods Acquired *',other_tstyle_l)
        ws_o.write(23, 0, '17',other_tstyle_l)
        ws_o.write(23, 1, 'Bad Debt Relief *',other_tstyle_l)
        ws_o.write(24, 0, '18',other_tstyle_l)
        ws_o.write(24, 1, 'Bad Debt Recovered * ',other_tstyle_l)
        i=2
        #~ for period_id in period_br:
            #~ ws_o.write(2, i, period_id.name, header_tstyle_r)
            #~ five_a = self.get_value('SR',period_id.id,company_id)+self.get_value('T6',period_id.id,company_id)+self.get_value('T0',period_id.id,company_id)+self.get_value('DS',period_id.id,company_id)
            #~ ws_o.write(4, i, round(five_a,2), other_tstyle)
            #~ five_b = self.get_amount('SR',period_id.id,company_id)+self.get_amount('T6',period_id.id,company_id)+self.get_amount('T0',period_id.id,company_id)+self.get_amount('DS',period_id.id,company_id)+self.get_amount('AJS',period_id.id,company_id)
            #~ ws_o.write(5, i, round(five_b,2), other_tstyle)
            #~ six_a = self.get_value('TX',period_id.id,company_id)+self.get_value('IM',period_id.id,company_id)+self.get_value('TX-RE',period_id.id,company_id)+self.get_value('TX-E43',period_id.id,company_id)
            #~ ws_o.write(8, i, round(six_a,2), other_tstyle)
            #~ 
            #~ T = self.get_value('SR',period_id.id,company_id) + self.get_value('T6',period_id.id,company_id) + self.get_value('T0',period_id.id,company_id) + self.get_value('ZRL',period_id.id,company_id) + self.get_value('ZRE',period_id.id,company_id) + self.get_value('DS',period_id.id,company_id) + self.get_value('OS',period_id.id,company_id) + self.get_value('RS',period_id.id,company_id) + self.get_value('GS',period_id.id,company_id)
            #~ E = self.get_value('ES',period_id.id,company_id)
            #~ TXRE = 0.0
            #~ if T+E != 0:
                #~ M = T/(T+E)
                #~ Val = self.get_amount('TX-RE',period_id.id,company_id)
                #~ TXRE =  Val * M
            #~ else:
                #~ TXRE = 0.0
            #~ six_b = self.get_amount('TX',period_id.id,company_id)+self.get_amount('IM',period_id.id,company_id)+TXRE+self.get_amount('TX-E43',period_id.id,company_id)+self.get_amount('AJP',period_id.id,company_id)
            #~ ws_o.write(9, i, round(six_b,2), other_tstyle)
            #~ 
            #~ if (self.get_amount('SR',period_id.id,company_id)+self.get_amount('T6',period_id.id,company_id)+self.get_amount('T0',period_id.id,company_id)+self.get_amount('DS',period_id.id,company_id)+self.get_amount('AJS',period_id.id,company_id)) > (self.get_amount('TX',period_id.id,company_id)+self.get_amount('IM',period_id.id,company_id)+self.get_amount('TX-RE',period_id.id,company_id)+self.get_amount('TX-E43',period_id.id,company_id)+self.get_amount('AJP',period_id.id,company_id)):
                #~ bb=(self.get_amount('SR',period_id.id,company_id)+self.get_amount('T6',period_id.id,company_id)+self.get_amount('T0',period_id.id,company_id)+self.get_amount('DS',period_id.id,company_id)+self.get_amount('AJS',period_id.id,company_id)) - (self.get_amount('TX',period_id.id,company_id)+self.get_amount('IM',period_id.id,company_id)+TXRE+self.get_amount('TX-E43',period_id.id,company_id)+self.get_amount('AJP',period_id.id,company_id))
                #~ ws_o.write(11,i, round(bb,2), other_tstyle)
                #~ ws_o.write(12,i, 0.0, other_tstyle)
            #~ elif (self.get_amount('SR',period_id.id,company_id)+self.get_amount('T6',period_id.id,company_id)+self.get_amount('T0',period_id.id,company_id)+self.get_amount('DS',period_id.id,company_id)+self.get_amount('AJS',period_id.id,company_id)) < (self.get_amount('TX',period_id.id,company_id)+self.get_amount('IM',period_id.id,company_id)+self.get_amount('TX-RE',period_id.id,company_id)+self.get_amount('TX-E43',period_id.id,company_id)+self.get_amount('AJP',period_id.id,company_id)):
                #~ bb= (self.get_amount('TX',period_id.id,company_id)+self.get_amount('IM',period_id.id,company_id)+TXRE+self.get_amount('TX-E43',period_id.id,company_id)+self.get_amount('AJP',period_id.id,company_id)) - (self.get_amount('SR',period_id.id,company_id)+self.get_amount('T6',period_id.id,company_id)+self.get_amount('T0',period_id.id,company_id)+self.get_amount('DS',period_id.id,company_id)+self.get_amount('AJS',period_id.id,company_id))
                #~ ws_o.write(11,i, 0.0, other_tstyle)
                #~ ws_o.write(12,i, round(bb,2), other_tstyle)
            #~ ws_o.write(14, i, self.get_value('ZRL',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(15, i, self.get_value('ZRE',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(16, i, self.get_value('ES',period_id.id,company_id)+self.get_value('ES43',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(17, i, self.get_value('RS',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(19, i, self.get_value('IS',period_id.id,company_id), other_tstyle)
            #~ is_percent = 0.06
            #~ ws_o.write(20, i, self.get_value('IS',period_id.id,company_id)*is_percent, other_tstyle)
            #~ ws_o.write(22,i,self.get_bad_debt('TX-RE','2010/0',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(23,i,self.get_bad_debt('AJP','8004/004',period_id.id,company_id), other_tstyle)
            #~ ws_o.write(24,i,self.get_bad_debt('AJS','8004/003',period_id.id,company_id), other_tstyle)
            #~ i+=1
        #~ 
        #### Work Sheet 2 ###################
        
        ws_d.write_merge(0, 0, 0, 12, 'GST Summary', M_header_tstyle1)
        ws_d.row(0).height = 256 * 3
        
        style1 = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                              'font: colour white, bold True;')
                              
        style2 = xlwt.easyxf('pattern: pattern solid, fore_colour white;'
                              'font: colour black, bold True;')
                              
        ws_d.write(1, 0, 'SUPPLY', M_header_tstyle) 
        ws_d.col(0).width = 256 * 20
        
        ws_d.write(2, 0, 'Code', header_tstyle)        
        ws_d.write(3, 0, 'SR', other_tstyle_l)
        ws_d.write(4, 0, 'T6', other_tstyle_l)
        ws_d.write(5, 0, 'T0', other_tstyle_l)
        ws_d.write(6, 0, 'ZRL', other_tstyle_l)
        ws_d.write(7, 0, 'ZRE', other_tstyle_l)
        ws_d.write(8, 0, 'ES43', other_tstyle_l)
        ws_d.write(9, 0, 'DS', other_tstyle_l)
        ws_d.write(10, 0, 'OS', other_tstyle_l)
        ws_d.write(11, 0, 'ES', other_tstyle_l)
        ws_d.write(12, 0, 'RS', other_tstyle_l)
        ws_d.write(13, 0, 'GS', other_tstyle_l)
        ws_d.write(14, 0, 'AJS', other_tstyle_l)
        #### Purchase #########
        ws_d.write(16, 0, 'PURCHASE', M_header_tstyle)
        ws_d.write(17, 0, 'Code', header_tstyle)
        ws_d.write(18, 0, 'TX', other_tstyle_l)
        ws_d.write(19, 0, 'IM', other_tstyle_l)
        ws_d.write(20, 0, 'IS', other_tstyle_l)
        ws_d.write(21, 0, 'BL', other_tstyle_l)
        ws_d.write(22, 0, 'NR', other_tstyle_l)
        ws_d.write(23, 0, 'ZP', other_tstyle_l)
        ws_d.write(24, 0, 'EP', other_tstyle_l)
        ws_d.write(25, 0, 'OP', other_tstyle_l)
        ws_d.write(26, 0, 'TX-E43', other_tstyle_l)
        ws_d.write(27, 0, 'TX-N43', other_tstyle_l)
        ws_d.write(28, 0, 'TX-RE', other_tstyle_l)
        ws_d.write(29, 0, 'GP', other_tstyle_l)
        ws_d.write(30, 0, 'AJP', other_tstyle_l)
        ws_d.write(32, 0, 'IRR =', header_tstyle)
        ws_d.write(33, 0, 'DmR*', header_tstyle)
        ws_d.write(34, 0, 'DmR Status', header_tstyle)
        i=1
        sr_total=t6_total=t0_total=zrl_total=zre_total=es43_total=ds_total=os_total=es_total=rs_total=gs_total=ajs_total=tx_total=im_total=0.0
        is_total=bl_total=nr_total=zp_total=ep_total=op_total=txe43_total=txn43_total=txre_total=gp_total=ajp_total=0.0
        irr_total = dmr_total = 0.0
        #~ sr_total=0.0
        txn43_adj=0.0
        #~ for period_id in period_br:
            #~ sr_vals=self.get_value('SR',period_id.id,company_id)
            #~ t6_vals=self.get_value('T6',period_id.id,company_id)
            #~ t0_vals=self.get_value('T0',period_id.id,company_id)
            #~ zrl_vals=self.get_value('ZRL',period_id.id,company_id)
            #~ zre_vals=self.get_value('ZRE',period_id.id,company_id)
            #~ es43_vals=self.get_value('ES43',period_id.id,company_id)
            #~ ds_vals=self.get_value('DS',period_id.id,company_id)
            #~ os_vals=self.get_value('OS',period_id.id,company_id)
            #~ es_vals=self.get_value('ES',period_id.id,company_id)
            #~ rs_vals=self.get_value('RS',period_id.id,company_id)
            #~ gs_vals=self.get_value('GS',period_id.id,company_id)
            #~ ajs_vals=self.get_value('AJS',period_id.id,company_id)
            #~ 
            #~ tx_vals=self.get_value('TX',period_id.id,company_id)
            #~ im_vals=self.get_value('IM',period_id.id,company_id)
            #~ is_vals=self.get_value('IS',period_id.id,company_id)
            #~ bl_vals=self.get_value('BL',period_id.id,company_id)
            #~ nr_vals=self.get_value('NR',period_id.id,company_id)
            #~ zp_vals=self.get_value('ZP',period_id.id,company_id)
            #~ ep_vals=self.get_value('EP',period_id.id,company_id)
            #~ op_vals=self.get_value('OP',period_id.id,company_id)
            #~ txe43_vals=self.get_value('TX-E43',period_id.id,company_id)
            #~ txn43_vals=self.get_value('TX-N43',period_id.id,company_id)
            #~ txre_vals=self.get_value('TX-RE',period_id.id,company_id)
            #~ gp_vals=self.get_value('GP',period_id.id,company_id)
            #~ ajp_vals=self.get_value('AJP',period_id.id,company_id)
            #~ 
            #~ ws_d.write(2, i, period_id.name, header_tstyle_r)
            #~ ws_d.write(3, i, sr_vals, other_tstyle)
            #~ ws_d.write(4, i, t6_vals, other_tstyle)
            #~ ws_d.write(5, i, t0_vals, other_tstyle)
            #~ ws_d.write(6, i,zrl_vals, other_tstyle)
            #~ ws_d.write(7, i, zre_vals, other_tstyle)
            #~ ws_d.write(8, i, es43_vals, other_tstyle)
            #~ ws_d.write(9, i, ds_vals, other_tstyle)
            #~ ws_d.write(10, i, os_vals, other_tstyle)
            #~ ws_d.write(11, i, es_vals, other_tstyle)
            #~ ws_d.write(12, i, rs_vals, other_tstyle)
            #~ ws_d.write(13, i, gs_vals, other_tstyle)
            #~ ws_d.write(14, i, ajs_vals, other_tstyle)
            #~ 
            #~ ws_d.write(17, i, period_id.name, header_tstyle_r)
            #~ ws_d.write(18, i, tx_vals, other_tstyle)
            #~ ws_d.write(19, i, im_vals, other_tstyle)
            #~ ws_d.write(20, i, is_vals, other_tstyle)
            #~ ws_d.write(21, i, bl_vals, other_tstyle)
            #~ ws_d.write(22, i, nr_vals, other_tstyle)
            #~ ws_d.write(23, i, zp_vals, other_tstyle)
            #~ ws_d.write(24, i, ep_vals, other_tstyle)
            #~ ws_d.write(25, i, op_vals, other_tstyle)
            #~ ws_d.write(26, i, txe43_vals, other_tstyle)
            #~ ws_d.write(27, i, txn43_vals, other_tstyle)
            #~ ws_d.write(28, i, txre_vals, other_tstyle)    
            #~ ws_d.write(29, i, gp_vals, other_tstyle)
            #~ ws_d.write(30, i, ajp_vals, other_tstyle)
            #~ 
            #~ IRR,DMR,STATUS=self.irr(period_id.id,company_id)
            #~ ws_d.write(32,i,str(IRR)+'%', other_tstyle)
            #~ ws_d.write(33,i,str(DMR)+'%', other_tstyle)
            #~ ws_d.write(34,i,STATUS, other_tstyle)
            #~ account_tax_obj = self.pool.get('account.tax')
            #~ cr= self.cr
            #~ uid = self.uid
            #~ tax_ids = account_tax_obj.search(cr,uid,[('description','=','TX-N43')])
            #~ if tax_ids:
                #~ tax_percent = account_tax_obj.browse(cr,uid,tax_ids[0]).amount
                #~ if STATUS =='qualify':
                    #~ txn43_adj += txn43_vals * tax_percent
            #~ i+=1
            #~ irr_total += IRR
            #~ dmr_total += DMR
            #~ sr_total+=sr_vals
            #~ t6_total+=t6_vals
            #~ t0_total+=t0_vals
            #~ zrl_total+=zrl_vals
            #~ zre_total+=zre_vals
            #~ es43_total+=es43_vals
            #~ ds_total+=ds_vals
            #~ os_total+=os_vals
            #~ es_total+=es_vals
            #~ rs_total+=rs_vals
            #~ gs_total+=gs_vals
            #~ ajs_total+=ajs_vals
            #~ tx_total+=tx_vals
            #~ im_total+=im_vals
            #~ is_total+=is_vals
            #~ bl_total+=bl_vals
            #~ nr_total+=nr_vals
            #~ zp_total+=zp_vals
            #~ ep_total+=ep_vals
            #~ op_total+=op_vals
            #~ txe43_total+=txe43_vals
            #~ txn43_total+=txn43_vals
            #~ txre_total+=txre_vals
            #~ gp_total+=gp_vals
            #~ ajp_total+=ajp_vals
        #~ ws_d.write(2,i,'Total',header_tstyle_r)
        #~ ws_d.write(3,i,sr_total,other_tstyle)
        #~ ws_d.write(4, i, t6_total, other_tstyle)
        #~ ws_d.write(5, i, t0_total, other_tstyle)
        #~ ws_d.write(6, i,zrl_total, other_tstyle)
        #~ ws_d.write(7, i, zre_total, other_tstyle)
        #~ ws_d.write(8, i, es43_total, other_tstyle)
        #~ ws_d.write(9, i, ds_total, other_tstyle)
        #~ ws_d.write(10, i, os_total, other_tstyle)
        #~ ws_d.write(11, i, es_total, other_tstyle)
        #~ ws_d.write(12, i, rs_total, other_tstyle)
        #~ ws_d.write(13, i, gs_total, other_tstyle)
        #~ ws_d.write(14, i, ajs_total, other_tstyle)
        #~ 
        #~ ws_d.write(17, i, 'Total', header_tstyle_r)
        #~ ws_d.write(18, i, tx_total, other_tstyle)
        #~ ws_d.write(19, i, im_total, other_tstyle)
        #~ ws_d.write(20, i, is_total, other_tstyle)
        #~ ws_d.write(21, i, bl_total, other_tstyle)
        #~ ws_d.write(22, i, nr_total, other_tstyle)
        #~ ws_d.write(23, i, zp_total, other_tstyle)
        #~ ws_d.write(24, i, ep_total, other_tstyle)
        #~ ws_d.write(25, i, op_total, other_tstyle)
        #~ ws_d.write(26, i, txe43_total, other_tstyle)
        #~ ws_d.write(27, i, txn43_total, other_tstyle)
        #~ ws_d.write(28, i, txre_total, other_tstyle)    
        #~ ws_d.write(29, i, gp_total, other_tstyle)
        #~ ws_d.write(30, i, ajp_total, other_tstyle)
        #~ irr_median = round((irr_total/(i-1)),2)
        #~ dmr_median = round((dmr_total/(i-1)),2)
        #~ ws_d.write(32,i,str(irr_median)+'%', other_tstyle)
        #~ ws_d.write(33,i,str(dmr_median)+'%', other_tstyle)
        #~ #### Work Sheet Annual Adjustment ###################
        #~ ws_a = wb.add_sheet('Annual Adjustment')
        #~ period_ids=[]
        #~ fiscal_year = period_br[0].fiscalyear_id.name
        #~ for period in period_br:
            #~ period_ids.append(period.id)
        #~ adjust_data = self.annual_adjustment_report(data,period_ids,"'in_invoice'")
        #~ inv_total,gst_total,itc_total=0,0,0
        #~ for adj in adjust_data:
            #~ val1,val2,val3 =self.irr(adj['tperiod'],company_id)
            #~ adj['tqitc'] = adj['taxamount']*val1/100
            #~ inv_total +=adj['inv_total']
            #~ gst_total +=adj['taxamount']
            #~ itc_total +=adj['tqitc']
            #~ adj['tperiod']=str(val1)+'%'
        #~ if adjust_data:
            #~ columns = sorted(list(adjust_data[0].keys()))
            #~ x=0
            #~ ws_a.write_merge(0, 0, 0, 7, 'Annual Adjustment of The Year', M_header_tstyle1)
            #~ ws_a.row(0).height = 256 * 3
            #~ ws_a.write(x+1,0,"Date",header_tstyle_c)
            #~ ws_a.write(x+1,1,"Invoice Number",header_tstyle_c)
            #~ ws_a.write(x+1,2,"Description",header_tstyle_c)
            #~ ws_a.write(x+1,3,"Amount",header_tstyle_c)
            #~ ws_a.write(x+1,4,"GST",header_tstyle_c)
            #~ ws_a.write(x+1,5,"IRR",header_tstyle_c)
            #~ ws_a.write(x+1,6,"ITC",header_tstyle_c)
            #~ ws_a.write(x+1,7,"Tax Code",header_tstyle_c)
            #~ ws_a.col(0).width = 256 * 15
            #~ ws_a.col(1).width = 256 * 20
            #~ ws_a.col(2).width = 256 * 50
            #~ ws_a.col(3).width = 256 * 20
            #~ ws_a.col(4).width = 256 * 10
            #~ ws_a.col(5).width = 256 * 10
            #~ ws_a.col(6).width = 256 * 10
            #~ ws_a.col(7).width = 256 * 10
            #~ for c, row in enumerate(adjust_data):
                #~ for d, col in enumerate(columns):
                   #~ ws_a.write(c+2, d, row[col], other_tstyle1)
            #~ ws_a.write(c+3,2,'Total',other_tstyle1)
            #~ ws_a.write(c+3,3,round(inv_total,2),other_tstyle1)
            #~ ws_a.write(c+3,4,round(gst_total,2),other_tstyle1)
            #~ ws_a.write(c+3,6,round(itc_total,2),other_tstyle1)
            #~ 
            #~ ws_a.write(c+5,3,'Amount',other_tstyle1)
            #~ ws_a.write(c+5,4,'Annual IRR',other_tstyle1)
            #~ ws_a.write(c+5,5,'TX-RE' + str(fiscal_year),other_tstyle1)
            #~ ws_a.write(c+6,2,'Total ITC Claim TX-RE of the Year' + str(fiscal_year),other_tstyle1)
            #~ ws_a.write(c+6,3,round(inv_total,2),other_tstyle1)
            #~ ws_a.write(c+6,5,round(itc_total,2),other_tstyle1)
            #~ ws_a.write(c+7,2,'Total ITC Eligible TX-RE of the Year' + str(fiscal_year),other_tstyle1)
            #~ ws_a.write(c+7,3,round(inv_total,2),other_tstyle1)
            #~ ws_a.write(c+7,4,str(irr_median)+'%',other_tstyle1)
            #~ itc_eligible = inv_total * (irr_median/100) * 0.06
            #~ ws_a.write(c+7,5,round(itc_eligible,2) ,other_tstyle1)
            #~ if itc_total >= itc_eligible:
                #~ adj_output_tax  = itc_total - itc_eligible
            #~ else:
                #~ adj_output_tax  = itc_eligible -  itc_total 
            #~ ws_a.write(c+8,5,round(adj_output_tax,2),other_tstyle1)
            #~ 
            #~ ws_a.write(c+9,2,'Total Exempt Input Tax TX-N43 ='+str(txn43_adj),other_tstyle1)
    # end def generate_xls_report

gst_xls('report.gst03', 'account.period',
    parser=gst_print_xls)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
