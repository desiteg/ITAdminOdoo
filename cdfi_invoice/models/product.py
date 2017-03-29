# -*- coding: utf-8 -*-
from openerp import fields, models, api,_


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    UNIDAD_MEDIDA_LIST=[('KILO', 'KILO'),
                   ('GRAMO', 'GRAMO'),
                   ('METRO LINEAL', 'METRO LINEAL'),
                   ('METRO CUADRADO', 'METRO CUADRADO'),
                   ('METRO CUBICO', 'METRO CUBICO'),
                   ('PIEZA', 'PIEZA'),
                   ('CABEZA', 'CABEZA'),
                   ('LITRO', 'LITRO'),
                   ('PAR', 'PAR'),
                   ('KILOWATT', 'KILOWATT'),
                   ('MILLAR', 'MILLAR'),
                   ('JUEGO', 'JUEGO'),
                   ('KILOWATT/HORA', 'KILOWATT/HORA'),
                   ('TONELADA', 'TONELADA'),
                   ('BARRIL', 'BARRIL'),
                   ('GRAMO NETO', 'GRAMO NETO'),
                   ('DECENAS', 'DECENAS'),
                   ('CIENTOS', 'CIENTOS'),
                   ('DOCENAS', 'DOCENAS'),
                   ('CAJA', 'CAJA'),
                   ('BOTELLA', 'BOTELLA'),
                   ('NO APLICA', 'NO APLICA'),
                   ]
    
    unidad_medida = fields.Selection(
        selection=UNIDAD_MEDIDA_LIST,
        string='Unidad de medida',
    )
    