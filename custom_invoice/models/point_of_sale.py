# -*- coding: utf-8 -*-

import base64
import json
import requests
from lxml import etree

from openerp import fields, models, api, _, SUPERUSER_ID
from openerp.exceptions import UserError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer = fields.Many2one('res.partner', string=_('Cliente Default'),
                                       domain=[('customer','=',True)])
    product_total = fields.Many2one('product.product', string=_('Producto total'))


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    def _default_customer(self):
        sessions = self.env['pos.session'].search([('state','=', 'opened'), ('user_id','=',self.env.uid)])
        if sessions:
            return sessions[0].config_id.default_customer
        
        
    partner_id = fields.Many2one('res.partner', string=_('Customer'),
                                     select=1, states={'draft': [('readonly', False)], 'paid': [('readonly', False)]},
                                     default=_default_customer)

    def action_invoice(self, cr, uid, ids, context=None):
        inv_ref = self.pool.get('account.invoice')
        inv_line_ref = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        inv_ids = []
        invoices = {}
        orders = self.pool.get('pos.order').browse(cr, uid, ids, context=context)

        for order in orders:
            group_key = order.partner_id.id
            # Force company for all SUPERUSER_ID action
            company_id = order.company_id.id
            local_context = dict(context or {}, force_company=company_id, company_id=company_id)
            if order.invoice_id:
                inv_ids.append(order.invoice_id.id)
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            acc = order.partner_id.property_account_receivable_id.id
            inv = {
                'name': order.name,
                'origin': order.name,
                'account_id': acc,
                'journal_id': order.sale_journal.id or None,
                'type': 'out_invoice',
                'reference': order.name,
                'partner_id': order.partner_id.id,
                'comment': order.note or '',
                'currency_id': order.pricelist_id.currency_id.id, # considering partner's sale pricelist's currency
                'company_id': company_id,
                'user_id': uid,
            }
            invoice = inv_ref.new(cr, uid, inv)
            invoice._onchange_partner_id()

            inv = invoice._convert_to_write(invoice._cache)
            if not inv.get('account_id', None):
                inv['account_id'] = acc
            if group_key not in invoices:
                inv_id = inv_ref.create(cr, SUPERUSER_ID, inv, context=local_context)
                self.write(cr, uid, [order.id], {'invoice_id': inv_id, 'state': 'invoiced'}, context=local_context)
                inv_ids.append(inv_id)
                invoices[group_key] = inv_id
            elif group_key in invoices:
                invoice_obj = inv_ref.browse(cr, uid, invoices[group_key], context=context)
                if order.name not in invoice_obj.origin.split(', '):
                    inv_ref.write(cr, SUPERUSER_ID, invoices[group_key], {'origin': invoice_obj.origin + ', ' + order.name}, context=local_context)
            inv_id = invoices[group_key]
            for line in order.lines:
                inv_name = product_obj.name_get(cr, uid, [line.product_id.id], context=local_context)[0][1]
                inv_line = {
                    'invoice_id': inv_id,
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'account_analytic_id': self._prepare_analytic_account(cr, uid, line, context=local_context),
                    'name': inv_name,
                }

                #Oldlin trick
                invoice_line = inv_line_ref.new(cr, SUPERUSER_ID, inv_line, context=local_context)
                invoice_line._onchange_product_id()
                invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids if tax.company_id.id == company_id]
                fiscal_position_id = line.order_id.fiscal_position_id
                if fiscal_position_id:
                    invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(invoice_line.invoice_line_tax_ids)
                invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids]
                # We convert a new id object back to a dictionary to write to bridge between old and new api
                inv_line = invoice_line._convert_to_write(invoice_line._cache)
                inv_line.update(price_unit=line.price_unit, discount=line.discount)
                inv_line_ref.create(cr, SUPERUSER_ID, inv_line, context=local_context)
            inv_ref.compute_taxes(cr, SUPERUSER_ID, [inv_id], context=local_context)
            self.signal_workflow(cr, uid, [order.id], 'invoice')
        
        for inv_id in invoices.values():
            inv_ref.signal_workflow(cr, SUPERUSER_ID, [inv_id], 'validate')

        if not inv_ids: return {}

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }
        
    
    def create_from_ui(self, cr, uid, orders, context=None):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        existing_order_ids = self.search(cr, uid, [('pos_reference', 'in', submitted_references)], context=context)
        existing_orders = self.read(cr, uid, existing_order_ids, ['pos_reference'], context=context)
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]

        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            order_id = self._process_order(cr, uid, order, context=context)
            order_ids.append(order_id)

            try:
                self.signal_workflow(cr, uid, [order_id], 'paid')
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                self.action_invoice(cr, uid, [order_id], context)
                
        return order_ids


    def action_invoice_total(self, cr, uid, ids, context=None):
        inv_ref = self.pool.get('account.invoice')
        inv_line_ref = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        inv_ids = []
        invoices = {}
        invoice_lines = {}
        orders = self.pool.get('pos.order').browse(cr, uid, ids, context=context)
        
        for order in orders:
            group_key = order.partner_id.id
            # Force company for all SUPERUSER_ID action
            company_id = order.company_id.id
            local_context = dict(context or {}, force_company=company_id, company_id=company_id)
            if order.invoice_id:
                inv_ids.append(order.invoice_id.id)
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            acc = order.partner_id.property_account_receivable_id.id
            inv = {
                'name': order.name,
                'origin': order.name,
                'account_id': acc,
                'journal_id': order.sale_journal.id or None,
                'type': 'out_invoice',
                'reference': order.name,
                'partner_id': order.partner_id.id,
                'comment': order.note or '',
                'currency_id': order.pricelist_id.currency_id.id, # considering partner's sale pricelist's currency
                'company_id': company_id,
                'user_id': uid,
            }
            invoice = inv_ref.new(cr, uid, inv)
            invoice._onchange_partner_id()

            inv = invoice._convert_to_write(invoice._cache)
            if not inv.get('account_id', None):
                inv['account_id'] = acc
            if group_key not in invoices:
                inv_id = inv_ref.create(cr, SUPERUSER_ID, inv, context=local_context)
                inv_ids.append(inv_id)
                invoices[group_key] = inv_id
                inv_name = order.config_id.product_total.name
                inv_line = {
                    'invoice_id': inv_id,
                    'product_id': order.config_id.product_total.id,
                    # 'price_unit': order.amount_total,
                    'quantity': 1,
                    'name': inv_name,
                }
                invoice_line = inv_line_ref.new(cr, SUPERUSER_ID, inv_line, context=local_context)
                invoice_line._onchange_product_id()
                invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids if tax.company_id.id == company_id]
                fiscal_position_id = order.fiscal_position_id
                if fiscal_position_id:
                    invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(invoice_line.invoice_line_tax_ids)
                invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids]
                # We convert a new id object back to a dictionary to write to bridge between old and new api
                inv_line = invoice_line._convert_to_write(invoice_line._cache)
                
                inv_line.update(price_unit=order.amount_total)
                inv_line_id = inv_line_ref.create(cr, SUPERUSER_ID, inv_line, context=local_context)
                invoice_lines[group_key] = inv_line_id
                print 'inv_line_id: ', inv_line_id
            elif group_key in invoices:
                invoice_obj = inv_ref.browse(cr, uid, invoices[group_key], context=context)
                if order.name not in invoice_obj.origin.split(', '):
                    inv_ref.write(cr, SUPERUSER_ID, invoices[group_key], {'origin': invoice_obj.origin + ', ' + order.name}, context=local_context)
                
                line = invoice_obj.invoice_line_ids[0]
                print 'invoice_lines[group_key]: ', invoice_lines[group_key]
                print line.price_unit
                print order.amount_total
                amount = line.price_unit + order.amount_total
                print amount
                inv_line_ref.write(cr, SUPERUSER_ID, invoice_lines[group_key], {'price_unit': amount}, context=local_context)
            inv_id = invoices[group_key]
            self.write(cr, uid, [order.id], {'invoice_id': inv_id}, context=local_context)
            inv_ref.compute_taxes(cr, SUPERUSER_ID, [inv_id], context=local_context)
            self.signal_workflow(cr, uid, [order.id], 'invoice')
        
        for inv_id in invoices.values():
            inv_ref.signal_workflow(cr, SUPERUSER_ID, [inv_id], 'validate')
            
        print inv_ids

        if not inv_ids: return {}

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.invoice',
            'context': {},
            'type': 'ir.actions.act_window',
            'res_id': inv_ids[0],
        }
            
    
            
    