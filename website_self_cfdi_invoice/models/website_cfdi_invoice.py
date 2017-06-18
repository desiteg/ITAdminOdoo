# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
import time
from openerp import SUPERUSER_ID

import sys
import base64

reload(sys)  
sys.setdefaultencoding('utf8')

class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res  = super(account_invoice, self).invoice_validate()
        attachment_obj = self.env['ir.attachment']
        for invoice in self:
            self.env.cr.execute("delete from ir_attachment where name like 'Invoice_%s' and res_id = %s and res_model='account.invoice';" % ('%',invoice.id,))
        return res

# class ir_attachment(models.Model):
#     _name = 'ir.attachment'
#     _inherit = 'ir.attachment'

#     @api.model # Self, cr, uid, ids, context
#     def create(self, vals):
#         if 'name' in vals:
#             attachment_name = vals['name']
#             if '.pdf' in attachment_name:
#                 if attachment_name[0:8].upper == 'INVOICE_':
#                     return False

#         res  = super(ir_attachment, self).create(vals)
#         return res

class website_self_invoice_web(models.Model):
    _name = 'website.self.invoice.web'
    _description = 'Portal de Autofacturacion Integrado a Odoo' 
    _rec_name = 'order_number' 
    _order = 'create_date desc' 

    datas_fname = fields.Char('File Name',size=256)
    file = fields.Binary('Layout')
    download_file = fields.Boolean('Descargar Archivo')
    cadena_decoding = fields.Text('Binario sin encoding')
    type = fields.Selection([('csv','CSV'),('xlsx','Excel')], 'Tipo Exportacion', 
                            required=False, )
    rfc_partner = fields.Char('RFC', size=15)
    order_number = fields.Char('Folio Pedido de Venta', size=128)
    mail_to = fields.Char('Correo Electronico', size=256)
    ticket_pos = fields.Boolean('Ticket')
    state = fields.Selection([('draft','Borrador'),('error','Error'),('done','Relizado')])

    attachment_ids = fields.One2many('website.self.invoice.web.attach','website_auto_id','Adjuntos del Portal')
    
    error_message = fields.Text('Mensaje de Error')

    _defaults = {
        'download_file': False,
        'type': 'csv',
        'state': 'draft',
        }


    def website_form_input_filter(self, request, values):
        values['medium_id'] = (
                values.get('medium_id') or
                self.default_get(['medium_id']).get('medium_id') or
                self.sudo().env['ir.model.data'].xmlid_to_res_id('utm.utm_medium_website')
        )
        return values

    @api.multi
    def write(self, values):
        result = super(website_self_invoice_web, self).write(values)        
        return result

    @api.model
    def create(self, values):
        result = super(website_self_invoice_web, self).create(values)
        print 'result.ticket_pos: ', result.ticket_pos, ' values: ', values['ticket_pos']
        ### Validacion de Campos Obligatorios ###
        if not result.rfc_partner or not result.order_number: # or not result.mail_to:
            result.write({
                        'error_message':'Los campos Marcados con un ( * ) son Obligatorios.',
                        'state': 'error',
                    })
            return result
        self.env.cr.execute("""
            select id from res_partner where UPPER(rfc) like %s;
            """, ('%'+result.rfc_partner.upper()+'%',))
        cr_res = self.env.cr.fetchall()
        order_id = False

        try:
            partner_id = cr_res[0][0]
            if not partner_id:
                result.write({
                        'error_message':'El RFC %s no existe en la Base de Datos.' % result.rfc_partner,
                        'state': 'error',
                    })
                return result
        except:
            result.write({
                    'error_message':'El RFC %s no existe en la Base de Datos.' % result.rfc_partner,
                    'state': 'error',
                })
            return result
        ##### Retornamos  la Factura en caso que exista ####
        if result.ticket_pos == False:
            self.env.cr.execute("""
                select id from sale_order where UPPER(name)=%s;
                """, (result.order_number.upper(),))
            cr_res = self.env.cr.fetchall()
            try:
                order_id = cr_res[0][0]
                if not order_id:
                    result.write({
                            'error_message':'El Pedido %s no existe en la Base de Datos.' % result.order_number,
                            'state': 'error',
                        })
                    return result
            except:
                result.write({
                        'error_message':'El Pedido %s no existe en la Base de Datos.' % result.order_number,
                        'state': 'error',
                    })
                return result
        else:
            self.env.cr.execute("""
                select id from pos_order where UPPER(pos_reference)= %s;
                """, (result.order_number.upper(),))
            cr_res = self.env.cr.fetchall()
            try:
                order_id = cr_res[0][0]
                if not order_id:
                    result.write({
                            'error_message':'El Ticket %s no existe en la Base de Datos.' % result.order_number,
                            'state': 'error',
                        })
                    return result
            except:
                result.write({
                        'error_message':'El Ticket %s no existe en la Base de Datos.' % result.order_number,
                        'state': 'error',
                    })
                return result
        if order_id and result.ticket_pos == False:
            order_obj =  self.env['sale.order'].sudo()
            order_br = order_obj.browse(order_id)
            if order_br.partner_id.id != partner_id:
                result.write({
                            'error_message':'El RFC %s no pertenece al Relacionado con el Pedido de Venta %s.' % (result.rfc_partner,result.order_number,),
                            'state': 'error',
                        })
                return result
            order_br = order_obj.browse(order_id)
            picking_obj  = self.env['stock.picking'].sudo()
            picking_br = picking_obj.search([('origin','=',order_br.name)])
            if order_br.state in ('draft','sent'):
                result.write({
                            'error_message':'El Pedido %s se encuentra en espera de ser procesado, por favor comuniquese con la compañia.' % order_br.name,
                            'state': 'error',
                        })
                return result
            if picking_br:
                picking_br = picking_br[0]
                picking_br.force_assign()
                picking_br.action_done()
                # for move in picking_br.pack_operation_product_ids:
                #     if move.state != 'done':
                #         move.force_assign()
                #         move.action_done()
            
            if order_br.invoice_status != 'no': # not in('invoiced','no'):
                if True:
                    invoice_return = None
                    if order_br.invoice_status == 'invoiced':
                        invoice_return = order_br.invoice_ids.filtered(lambda r: r.state != 'cancel')
                        if invoice_return and invoice_return[0].estado_factura in['factura_correcta', 'factura_cancelada']:
                            result.write({
                                    'error_message':'El Pedido %s ya fue Facturado.' % result.order_number,
                                    'state': 'error',
                                })
                            return result
                    else:
                        invoice_return = order_br.action_invoice_create()
                    invoice_obj = self.env['account.invoice'].sudo()
                    invoice_br = invoice_obj.browse(invoice_return[0])
                    vals = {'factura_cfdi':True}
                    if not invoice_br.tipo_comprobante:
                        vals.update({'tipo_comprobante': 'ingreso'})
                    if not invoice_br.tipo_formato:
                        vals.update({'tipo_formato': 'Factura'})
                    if not invoice_br.forma_pago:
                        vals.update({'forma_pago': _('Pago en una sola exhibición')})
                    if not invoice_br.condicione_pago:
                        vals.update({'condicione_pago': 'Contado'})
                    invoice_br.write(vals)
                    if True:
                        if invoice_br.state == 'draft':
                            invoice_br.action_invoice_open()
                        else:
                            invoice_br.generate_cfdi_invoice()
                        ir_attach = self.env['ir.attachment'].sudo()
                        attachment_ids = ir_attach.search([('res_model','=','account.invoice'),('res_id','=',invoice_br.id)])
                        if not attachment_ids:
                            Template = self.env['mail.template'].sudo()
                            Attachment = self.env['ir.attachment'].sudo()
                            report = Template.env['report'].get_pdf([invoice_br.id], 'account.report_invoice')
                            report = base64.b64encode(report)
                            fname =  'CDFI_' + invoice_br.number.replace('/', '_') + '.pdf'
                            attachment_data = {
                                'name': fname,
                                'datas_fname': fname,
                                'datas': report,
                                'res_model': 'account.invoice',
                                'res_id': invoice_br.id,
                            }
                            attachment_ids = [Attachment.create(attachment_data)]
                        if attachment_ids:
                            attachment_web =[]
                            for attach in attachment_ids:
                                xval = (0,0,{
                                    'attach_id': attach.id,
                                    })
                                attachment_web.append(xval)
                            result.write({'attachment_ids':attachment_web})
                            result.write({'state':'done'})
                    else:
                        result.write({
                            'error_message':'La factura %s no pudo timbrarse con el PAC, comuniquese con la compañia.' % invoice_br.number,
                            'state': 'error',
                        })
                        return result
                else:
                    result.write({
                            'error_message':'El Pedido %s tiene problemas para ser procesado comuniquese con la compañia.' % result.order_number,
                            'state': 'error',
                        })
                    return result
            else:
                result.write({
                            'error_message':'El Pedido %s ya fue Facturado.' % result.order_number,
                            'state': 'error',
                        })
                return result
        if order_id and result.ticket_pos == True:
            invoice_obj = self.env['account.invoice'].sudo()
            pos_order_obj = self.env['pos.order'].sudo()
            pos_br = pos_order_obj.browse(order_id)
            # pos_br.write({'partner_id':partner_id})
            if pos_br.partner_id:
                if pos_br.partner_id.id != partner_id:
                    result.write({
                                'error_message':'El RFC %s no pertenece al Relacionado con el Pedido de Venta %s.' % (result.rfc_partner,result.order_number,),
                                'state': 'error',
                            }) 
                    return result
            if pos_br.state != 'cancel':
                if True:
                    invoice_id = None
                    if pos_br.state == 'invoiced':
                        invoice_return = invoice_obj.search([('origin', '=', pos_br.name), ('state', '!=', 'cancel')])
                        invoice_id = invoice_return.id
                        if invoice_return and invoice_return[0].estado_factura in['factura_correcta', 'factura_cancelada']:
                            result.write({
                                    'error_message':'El Pedido %s ya fue Facturado.' % result.order_number,
                                    'state': 'error',
                                })
                            return result
                    else:
                        invoice_return = pos_br.action_invoice()
                        invoice_id = invoice_return['res_id']
                    invoice_br = invoice_obj.browse(invoice_id)
                    vals = {'factura_cfdi':True}
                    if not invoice_br.tipo_comprobante:
                        vals.update({'tipo_comprobante': 'ingreso'})
                    if not invoice_br.tipo_formato:
                        vals.update({'tipo_formato': 'Factura'})
                    if not invoice_br.forma_pago:
                        vals.update({'forma_pago': _('Pago en una sola exhibición')})
                    if not invoice_br.condicione_pago:
                        vals.update({'condicione_pago': 'Contado'})
                    if not pos_br.statement_ids:
                        payment_method_code = pos_br.statement_ids[0].journal_id.code
                        if payment_method_code not in ('01', '04', '28'):
                            result.write({
                                    'error_message':'Forma de pago desconocido %s: %s.' % (payment_method_code,
                                                                                         pos_br.statement_ids[0].journal_id.name),
                                    'state': 'error',
                                })
                            return result
                        vals.update({'methodo_pago': payment_method_code})
                    invoice_br.write(vals)
                    
                    
                    if True:
                        if invoice_br.state == 'draft':
                            invoice_br.action_invoice_open()
                        else:
                            invoice_br.generate_cfdi_invoice()
                        ir_attach = self.env['ir.attachment'].sudo()
                        attachment_ids = ir_attach.search([('res_model','=','account.invoice'),('res_id','=',invoice_br.id)])
                        if not attachment_ids:
                            Template = self.env['mail.template'].sudo()
                            Attachment = self.env['ir.attachment'].sudo()
                            report = Template.env['report'].get_pdf([invoice_br.id], 'account.report_invoice')
                            report = base64.b64encode(report)
                            fname =  'CDFI_' + invoice_br.number.replace('/', '_') + '.pdf'
                            attachment_data = {
                                'name': fname,
                                'datas_fname': fname,
                                'datas': report,
                                'res_model': 'account.invoice',
                                'res_id': invoice_br.id,
                            }
                            attachment_ids = [Attachment.create(attachment_data)]
                        if attachment_ids:
                            attachment_web =[]
                            for attach in attachment_ids:
                                xval = (0,0,{
                                    'attach_id': attach.id,
                                    })
                                attachment_web.append(xval)
                            result.write({'attachment_ids':attachment_web})
                            result.write({'state':'done'})
                    else:
                        result.write({
                            'error_message':'La factura %s no pudo timbrarse con el PAC, comuniquese con la compañia.' % invoice_br.number,
                            'state': 'error',
                        })
                        return result

                else:
                   result.write({
                            'error_message':'El Ticket %s tiene problemas para ser procesado comuniquese con la compañia.' % result.order_number,
                            'state': 'error',
                        })
                   return result
            else:
                result.write({
                            'error_message':'El Ticket %s ya fue Facturado.' % result.order_number,
                            'state': 'error',
                        })
                return result
        #### Ligar Adjuntos de Facturacion al one2many por el campo attach_id ####
        return result
# URL ejemplo:
# http://localhost:10069/web?db=AUTOINVOICE_TEST

website_self_invoice_web()

class website_self_invoice_web_attach(models.Model):
    _name = 'website.self.invoice.web.attach'
    _description = 'Adjuntos para Portal de Auto Facturacion'

    website_auto_id = fields.Many2one('website.self.invoice.web', 'ID Ref')
    attach_id = fields.Many2one('ir.attachment', 'Adjunto')
    datas_fname = fields.Char('File Name',size=256, related="attach_id.datas_fname")
    file = fields.Binary('Archivo Binario', related="attach_id.datas")
