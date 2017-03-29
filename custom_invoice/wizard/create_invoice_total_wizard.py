# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class CerateInvoiceTotalWizard(models.TransientModel):

    _name = 'create.invoice.total.wizard'

    @api.multi
    def action_create_invoice_total(self):
        order_is = self._context.get('active_ids')
        orders = self.env['pos.order'].browse(order_is)
        orders.action_invoice_total()
        return True