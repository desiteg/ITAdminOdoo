# -*- coding: utf-8 -*-


from openerp import fields, models, api,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    numero_interior = fields.Char(string=_('Número Interior'))
    colonia = fields.Char(string=_('Colonia'))
    municipio = fields.Char(string=_('Municipio'))
    rfc = fields.Char(string=_('RFC'))
    tipo_comprobante = fields.Selection(
        selection=[('ingreso', 'Ingreso'), ('egreso', 'Egreso'), ('traslado', 'Traslado')],
        string=_('Tipo de comprobante'),
    )
    tipo_formato = fields.Selection(
        selection=[('Factura', 'Factura'), ('ReciboDeHonorarios', 'Recibo De Honorarios'), 
                   ('ReciboDeArrendamiento', 'Recibo De Arrendamiento'), ('NotaDeCredito', 'Nota De Credito'), 
                   ('NotaDeCargo', 'Nota De Cargo'), ('CartaPorte', 'Carta Porte')],
        string=_('Tipo de formato'),
    )
    forma_pago = fields.Selection(
        selection=[(_('Pago en una sola exhibición'), _('Pago en una sola exhibición')), ],
        string=_('Forma de pago'),
    )
    condicione_pago = fields.Selection(
        selection=[('Contado', 'Contado'), ('Pago a 15 dias', 'Pago a 15 dias'), 
                   ('Pago a 30 dias', 'Pago a 30 dias'), ('Pago a 90 dias', 'Pago a 90 dias'), ],
        string=_('Condiciones de formato'),
    )
    methodo_pago = fields.Selection(
        selection=[('01', '01 - Efectivo'), ('02', '02 - Cheque nominativo'), 
                   ('03', '03 - Transferencia electrónica de fondos'),
                   ('04', '04 - Tarjeta de Crédito'), ('05', '05 - Monedero electrónico'),
                   ('06', '06 - Dinero electrónico'), ('08', '08 - Vales de despensa'), 
                   ('28', '28 - Tarjeta de débito'), ('29', '29 - Tarjeta de servicios'), 
                   ('99', '99 - Otros'), ('98', '98 - NA'),],
        string=_('Método de pago'),
    )
    num_cta_pago = fields.Char(string=_('Núm. Cta. Pago'))
    
    