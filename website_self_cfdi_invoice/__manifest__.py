# -*- coding: utf-8 -*-
{
    'name': "Portal de Auto-Facturacion CFDI",

    'summary': """
        Portal de Cliente diseñado para generar facturas desde la Web.""",

    'description': """

Portal Auto-Facturacion CFDI
================================

Permite al Cliente poder generar su Factura mediante la Parte Web.

    """,

    'author': "Esousy",
    'website': "",
    'category': 'Facturacion Electronica',
    'version': '10.0',
    'depends': [
        'base',
        'website',
        'website_sale',
        'website_crm',
        'sale',
        'account',
        'custom_invoice',
        'point_of_sale',
        'website_recaptcha_reloaded',
        ],
    'data': [
        #'security/ir.model.access.csv',
        'views/templates.xml',
    ],

}