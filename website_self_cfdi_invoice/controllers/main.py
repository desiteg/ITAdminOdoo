# -*- coding: utf-8 -*-
from odoo import http
from odoo import SUPERUSER_ID
from odoo.api import Environment
from odoo.http import request

import logging
import werkzeug

from odoo import http
from odoo import tools
from odoo.tools.translate import _
from odoo.addons.website.models.website import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale

PPG = 20 # Products Per Page
PPR = 4  # Products Per Row

import sys
reload(sys)  
sys.setdefaultencoding('utf8')


class FacturaCliente(http.Controller):
    @http.route('/portal/facturacliente/', auth='public', website=True)
    def index(self, **kw):
        # print "########### ENTRANDO AL PORTAL >>>>> "
        return http.request.render('website_self_cfdi_invoice.index',
            {
                'fields': ['RFC','Folio',],
            })
    @http.route('/portal/facturacliente/results/',type="http", auth="public", csrf=False, website=True)
    def my_fact_portal_insert(self, **kwargs):
        ### Esta linea implementa los Captcha en el Portal ####
        # if kwargs.has_key('g-recaptcha-response') and request.website.is_captcha_valid(kwargs['g-recaptcha-response']):
        rfc_partner = kwargs['rfc_partner'] or False
        order_number = kwargs['order_number'] or False
        mail_to = kwargs.get('ticket_pos', False)
        ticket_pos = kwargs.get('mail_to', False)
        if 'ticket_pos' in kwargs:
            ticket_pos = kwargs['ticket_pos'] or True
        else:
            ticket_pos = False
        auto_invoice_obj = http.request.env['website.self.invoice.web']
        
        #### Si tenemos datos de una consulta previa los retornamos
        request_preview = auto_invoice_obj.search([('rfc_partner','=',rfc_partner),('order_number','=',order_number),('state','=','done')])
        if request_preview:
            attachment_obj = http.request.env['website.self.invoice.web.attach']
            attachments = attachment_obj.search([('website_auto_id','=',request_preview[0].id)])
            return http.request.render('website_self_cfdi_invoice.html_result_thnks', 
                                                                                {
                                                                                'attachments': attachments,
                                                                                    })


        if not rfc_partner or not order_number: # or not mail_to:
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':['Los campos marcados con un ( * ) son Obligatorios.']})
        auto_invoice_id = auto_invoice_obj.create({
                                                    'rfc_partner': rfc_partner,
                                                    'order_number': order_number,
                                                    # 'mail_to': mail_to,
                                                    'ticket_pos': ticket_pos,
                                                    })
        attachment_obj = http.request.env['website.self.invoice.web.attach']
        attachments = attachment_obj.search([('website_auto_id','=',auto_invoice_id.id)])
        if auto_invoice_id.error_message:
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[auto_invoice_id.error_message]})
        return http.request.render('website_self_cfdi_invoice.html_result_thnks', 
                                                                            {
                                                                            'attachments': attachments,
                                                                            })

    @http.route('/portal/consulta_factura/',type="http", auth="public", csrf=False, website=True)
    def request_invoice(self, **kwargs):
        if not kwargs:
            return http.request.render('website_self_cfdi_invoice.index',
                                                                        {
                                                                            'fields': ['RFC','Folio',],
                                                                        })
        rfc_partner = kwargs['rfc_partner'] or False
        order_number = kwargs['order_number'] or False

        auto_invoice_obj = http.request.env['website.self.invoice.web']
        try:
            auto_invoice = auto_invoice_obj.search([('order_number','=',order_number),
                ('rfc_partner','=',rfc_partner)])
            if auto_invoice:
                attachment_obj = http.request.env['website.self.invoice.web.attach']
                attachments = attachment_obj.search([('website_auto_id','=',auto_invoice[0].id)])
                return http.request.render('website_self_cfdi_invoice.html_result_thnks', 
                                                                                    {
                                                                                    'attachments': attachments,
                                                                                    })
            else:
                error_message = "Su solicitud no pudo ser procesada.\nNo existe informacion para el Pedido %s." % order_number
                return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[error_message]})

        except:
            error_message = "Su solicitud no pudo ser procesada.\nLa informacion introducida es incorrecta."
            return http.request.render('website_self_cfdi_invoice.html_result_error_inv', {'errores':[error_message]})

        return http.request.render('website_self_cfdi_invoice.index',
            {
                'fields': ['RFC','Folio',],
            })
