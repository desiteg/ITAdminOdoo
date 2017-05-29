# -*- coding: utf-8 -*-


from odoo import fields, models, api,_


class ResCompany(models.Model):
    _inherit = 'res.company'

    rfc = fields.Char(string=_('RFC'))
    api_key = fields.Char(string=_('API Key'))
    http_factura = fields.Char(string=_('HTTP Factura'))
    factura_dir = fields.Char(string=_('Facturas Directorio'))
    modo_prueba = fields.Boolean(string=_('Modo prueba'))
    serie_factura = fields.Char(string=_('Serie factura'))
    
    