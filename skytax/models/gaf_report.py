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
from openerp import SUPERUSER_ID, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools import image_resize_image
from datetime import datetime , date as dt
import openerp.addons.decimal_precision as dp

def date_conversion(date):
    return datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
    
class gaf_report(osv.osv):
    _name = 'gaf.report'
    _columns = {
        'notes':fields.text('Details'),
        "data":fields.binary("File",readonly=True),
        "name":fields.char("Filename",16,readonly=True),
        "company_id":fields.many2one('res.company',"Company",required=True),
        'write_date': fields.datetime("Last Updated Date",readonly=True),
        'creation_date': fields.date("Creation Date",readonly=True),
        'filter': fields.selection([ ('filter_date', 'Date'),('no_filter','No Filter')], "Filter by", required=True),
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        }
        
    _defaults = {'filter': 'filter_date'}

    def generate_txt(self, cr, uid, ids, data, context={}):
        import StringIO
        import base64
        import getpass
        user = getpass.getuser()
        file_name = 'GAF.txt'
        file_data=StringIO.StringIO()
        company_ids=[]
        for gaf in self.browse(cr,uid,ids):
            company_id = gaf.company_id.id
            company_browse = self.pool.get('res.company').browse(cr,uid,company_id)
            child_ids = company_browse.child_ids
            company_ids.append(company_id)
            for child in child_ids:
                if child.vat == company_browse.vat:
                    company_ids.append(child.id)
            if gaf.filter =='filter_date':
                filters = [('date_start','>=',gaf.date_from),('date_end','<=',gaf.date_to)]
                inv_filter = [('date_invoice','>=',gaf.date_from),('date_invoice','<=',gaf.date_to),('company_id','in',company_ids)]
                move_filter = [('date','>=',gaf.date_from),('date','<=',gaf.date_to),('state','=','posted'),('company_id','in',company_ids)]
            start_date = gaf.date_from +'|'
            end_date =  gaf.date_to+'|'
            cname = company_browse.name +'|'
            if company_browse.company_registry:
                cnuen = company_browse.company_registry +'|'
            else:
                cnuen = 'XXX'+'|'
            if company_browse.vat:
                gstno= company_browse.vat +'|'
            else:
                gstno = 'XXX'+'|'
            product_version = 'SkyGST v1.0 2014|'
            #~ if company_browse.sky_gafver:
                #~ gaf_version = company_browse.sky_gafver +'|\n'
            #~ else:
            gaf_version = '1.0' +'|\n'

            if not gaf.creation_date:
                creation_date = str(dt.today().strftime('%d/%m/%Y')) + '|'
            else:
                creation_date  = str(date_conversion(gaf.creation_date)) +'|'
            #~ out = open('GAF.txt','wb+')
            temp_path = '/home/' + user + '/' + file_name
            out = open(temp_path,'wb+')
            company_name = 'C|'
            company_name += cname 
            company_name += cnuen 
            company_name += gstno 
            company_name += start_date
            company_name += end_date
            company_name += creation_date 
            company_name += product_version 
            company_name += gaf_version 
            partner_obj = self.pool.get('res.partner')
            currency_obj = self.pool.get('res.currency')
            inv_obj = self.pool.get('account.invoice')
            voucher_obj = self.pool.get('account.voucher')
            aml_obj = self.pool.get('account.move.line')
            am_obj = self.pool.get('account.move')
            supp_ids = partner_obj.search(cr,uid,[('supplier','=',True)])
            cust_ids = partner_obj.search(cr,uid,[('customer','=',True)])
            tot_cust_bal=tot_supp_bal=tot_cust_tax=tot_supp_tax=0.00
            inv_ids = inv_obj.search(cr,uid,inv_filter)
            inv_ids = inv_obj.search(cr,uid,[('state','!=','draft'),('id','in',inv_ids)])
            ci=0
            si=0
            l=0
            tax_amount =0.0
            in_inv_ids = inv_obj.search(cr,uid,[('type', 'in', ['in_invoice','in_refund','in_debitnote'])])
            for inv in inv_obj.browse(cr,uid,in_inv_ids):
                foreign_supply=False
                supp_bal_amount =supp_bal_amount_for_curr =0.00
                sln=1
                if inv.currency_id.id == inv.company_id.currency_id.id:
                    supp_inv_for_currency = 'XXX|'
                else:
                    supp_inv_for_currency = str(inv.currency_id.name) +  '|'
                    foreign_supply=True
                for line  in inv.invoice_line_ids:
                    supp_name = 'P|'+inv.partner_id.name +'|'
                    if inv.partner_id.co_reg:
                        supp_brn = inv.partner_id.co_reg+'|'
                    else:
                        supp_brn = 'XXX'+'|'
                    if inv.partner_id.country_id.name:
                        supp_country = inv.partner_id.country_id.name+'|'
                    else:
                        supp_country = 'XXX'+'|'
                    supp_inv_date = str(date_conversion(inv.date_invoice))+'|'
                    supp_inv_number = str(inv.number)+'|'
                    if inv.supplier_invoice_number:
                        supp_import = str(inv.supplier_invoice_number)+'|'
                    elif inv.origin:
                        supp_import = str(inv.origin)+'|'
                    else:
                        supp_import = 'XXX'+'|'
                    supp_inv_line = str(sln)+'|'
                    supp_inv_name = str(line.number)+'|'
                    if foreign_supply:
                        acc_move_ids = am_obj.search(cr,uid,[('id','=',inv.move_id.id)])
                        acc_move = inv.move_id
                        for aml in acc_move.line_id:
                            if line.product_id.id == line.product_id.id:
                                cust_bal_amount = line.price_subtotal
                                supp_bal_amount_for_curr = aml.debit
                                supp_bal = str(aml.credit)+'|'
                                country = str(inv.partner_id.country_id.name)+'|'
                                for_curr_str = str(supp_bal_amount_for_curr) + '|'
                                tax_for_curr = '0.00|'
                    else:
                        supp_bal_amount = line.price_subtotal
                        supp_bal = str(supp_bal_amount)+'|'
                        supp_bal_amount_for_curr = 0.00
                        country='XXX'+'|'
                        for_curr_str = '0.00|'
                        tax_for_curr = '0.00|'
                    supp_bal = str(supp_bal_amount)+'|'
                    company_name+= supp_name
                    company_name+= supp_brn
                    company_name+= supp_inv_date
                    company_name+= supp_inv_number
                    company_name+= supp_import
                    company_name+= supp_inv_line
                    company_name+= supp_inv_name
                    company_name+= supp_bal
                    if line.invoice_line_tax_ids:
                        supp_inv_tax_name = str([x.description for x in line.invoice_line_tax_ids][0])  +'|'
                        tax_bases =  line.invoice_line_tax_ids.compute_all((line.price_unit * (1 - (line.discount or 0.0) / 100.0)),line.quantity, line.product_id, inv.partner_id)['taxes']
                        for tax_base in tax_bases:
                            tax_amount+=tax_base['amount']
                        supp_inv_tax = str(tax_base['amount'])+'|'
                        tot_supp_tax += (tax_base['amount'])
                    else:
                        supp_inv_tax_name = 'XXX'+'|'
                        supp_inv_tax = 'XXX'+'|'
                    company_name+= supp_inv_tax
                    company_name+= supp_inv_tax_name
                    company_name+= supp_inv_for_currency
                    company_name+= for_curr_str
                    company_name+= tax_for_curr
                    company_name+= '\n'
                    if foreign_supply:
                        total_supp_bal+=supp_bal_amount_for_curr
                    else:
                        tot_supp_bal+=supp_bal_amount
                    si+=1
                    sln+=1
            out_inv_ids = inv_obj.search(cr,uid,[('type', 'in', ['out_invoice','out_refund','out_debitnote'])])
            for inv in inv_obj.browse(cr,uid,out_inv_ids):
                sln=1
                foreign_supply=False
                cust_bal_amount =cust_bal_amount_for_curr =0.00
                if inv.currency_id.id == inv.company_id.currency_id.id:
                    cust_inv_for_currency =   'XXX|'
                else:
                    cust_inv_for_currency =  str(inv.currency_id.name) +'|'
                    foreign_supply=True
                for line  in inv.invoice_line_ids:
                    cust_name = 'S|'+inv.partner_id.name +'|'
                    #~ if inv.partner_id.co_reg:
                        #~ cust_brn = inv.partner_id.co_reg+'|'
                    #~ else:
                    cust_brn = 'XXX'+'|'
                    cust_inv_date = str(date_conversion(inv.date_invoice))+'|'
                    cust_inv_number = str(inv.number)+'|'
                    if inv.reference:
                        cust_import = str(inv.reference)+'|'
                    else:
                        cust_import = 'XXX'+'|'
                    cust_inv_line = str(sln)+'|'
                    #~ cust_inv_name = str(line.name)+'|'
                    cust_inv_name = str('1')+'|'
                    if foreign_supply:
                        acc_move_ids = am_obj.search(cr,uid,[('id','=',inv.move_id.id)])
                        acc_move = inv.move_id
                        for aml in acc_move.line_id:
                            if line.product_id.id == line.product_id.id:
                                cust_bal_amount = aml.credit
                                cust_bal_amount_for_curr = line.price_subtotal
                                cust_bal = str(aml.credit)+'|'
                                country = str(inv.partner_id.country_id.name)+'|'
                                for_curr_str = str(cust_bal_amount_for_curr) + '|'
                                tax_for_curr = '0.00|'
                    else:
                        cust_bal_amount = line.price_subtotal
                        cust_bal = str(cust_bal_amount)+'|'
                        cust_bal_amount_for_curr = 0.00
                        country='XXX'+'|'
                        for_curr_str = '0.00|'
                        tax_for_curr = '0.00|'
                    company_name+= cust_name
                    company_name+= cust_brn
                    company_name+= cust_inv_date
                    company_name+= cust_inv_number
                    company_name+= cust_import
                    company_name+= cust_inv_line
                    company_name+= cust_inv_name
                    company_name+= cust_bal
                    
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = False
                    if line.invoice_line_tax_ids:
                        cust_inv_tax_name = str([x.description for x in line.invoice_line_tax_ids][0])  +'|'
                        tax_bases =  line.invoice_line_tax_ids.compute_all(price,inv.currency_id,line.quantity, line.product_id, inv.partner_id)['taxes']
                        for tax_base in tax_bases:
                            tax_amount+=tax_base['amount']
                        cust_inv_tax = str(tax_base['amount'])+'|'
                        tot_cust_tax += (tax_base['amount'])
                    else:
                        cust_inv_tax_name = 'XXX'+'|'
                        cust_inv_tax = 'XXX'+'|'
                    company_name+= cust_inv_tax
                    company_name+= cust_inv_tax_name
                    company_name+= country
                    company_name+= cust_inv_for_currency
                    company_name+= for_curr_str
                    company_name+= tax_for_curr
                    company_name+= '\n'
                    tot_cust_bal+=cust_bal_amount
                    sln+=1
                    ci+=1
            """ Voucher Not needed since we use GLData for all entries"""
            aml_ids=[]
            move_ids = am_obj.search(cr,uid,move_filter)
            move_ids = am_obj.search(cr,uid,[('id','in',move_ids)])
            aml_ids = aml_obj.search(cr,uid,[('move_id','in',move_ids)])
            #~ print aml_ids
            #~ for am in am_obj.browse(cr,uid,move_ids):
                #~ for line in am.line_id:
                    #~ aml_ids.append(line.id)
            tot_debit=tot_credit=0.00
            balance=0.00
            for aml in aml_obj.browse(cr,uid,aml_ids):
                cust_aml_date = 'L|'+str(date_conversion(aml.date))+'|'
                cust_aml_acc_id = str(aml.account_id.code)+'|'
                cust_aml_acc_name = str(aml.account_id.name)+'|'
                if aml.invoice:
                    cust_aml_name = str(aml.invoice.number)+'|'
                else:
                    cust_aml_name = str(aml.name)+'|'
                if aml.ref:
                    cust_aml_ref = str(aml.ref)+'|'
                else:
                    cust_aml_ref= str(aml.move_id.name)+'|'
                cust_move_ref= str(aml.move_id.ref)+'|'
                cust_source_type= str(aml.move_id.journal_id.code)+'|'
                debit = str(aml.debit)+'|'
                credit = str(aml.credit)+'|'
                tot_debit+=aml.debit
                tot_credit+=aml.credit
                balance = round((tot_debit-tot_credit),2)
                bal= str(abs(balance))+'|\n'
                company_name+= cust_aml_date
                company_name+= cust_aml_acc_id
                company_name+= cust_aml_acc_name
                company_name+= cust_aml_name
                company_name+= cust_aml_ref
                company_name+= cust_source_type
                company_name+= debit
                company_name+= credit
                company_name+= bal
                l+=1
            balance = abs(round((tot_debit-tot_credit),2))
            company_name+='F|'+str(si)+'|'+str(tot_supp_bal)+'|'+str(tot_supp_tax)+'|'+str(ci)+'|'+str(tot_cust_bal)+'|'+str(tot_cust_tax)+'|'+str(l)+'|'+str(tot_debit)+'|'+str(tot_credit)+'|'+str(balance)+'|\n'
            out.write(company_name)
            out.close
            data = base64.encodestring(company_name)
            self.write(cr,uid,ids,{'data':data,'name':'GAF'+'.txt','creation_date':datetime.today()})
        return True
gaf_report()    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
