# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CerateInvoiceWizard(models.TransientModel):

    _name = 'create.invoice.wizard'

    @api.multi
    def action_create_invoices(self):
        print 'action_create_invoices: '
        order_is = self._context.get('active_ids')
        print 'order_is: ', order_is
        orders = self.env['pos.order'].browse(order_is)
        orders.action_invoice()
        return True