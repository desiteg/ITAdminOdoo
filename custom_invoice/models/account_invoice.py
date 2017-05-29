# -*- coding: utf-8 -*-

import base64
import json
import requests
import datetime
from lxml import etree

from odoo import fields, models, api,_
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from reportlab.graphics.barcode import createBarcodeDrawing, getCodes
from reportlab.lib.units import mm
import amount_to_text_es_MX

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    factura_cfdi = fields.Boolean('Factura CFDI')
    tipo_comprobante = fields.Selection(
        selection=[('ingreso', 'Ingreso'), ('egreso', 'Egreso'), ('traslado', 'Traslado')],
        string=_('Tipo de comprobante'),
        related='partner_id.tipo_comprobante'
    )
    tipo_formato = fields.Selection(
        selection=[('Factura', 'Factura'), ('ReciboDeHonorarios', 'Recibo De Honorarios'), 
                   ('ReciboDeArrendamiento', 'Recibo De Arrendamiento'), ('NotaDeCredito', 'Nota De Credito'), 
                   ('NotaDeCargo', 'Nota De Cargo'), ('CartaPorte', 'Carta Porte')],
        string=_('Tipo de formato'),
        related='partner_id.tipo_formato'
    )
    forma_pago = fields.Selection(
        selection=[(_('Pago en una sola exhibición'), _('Pago en una sola exhibición')), ],
        string=_('Forma de pago'),
        related='partner_id.forma_pago'
    )
    condicione_pago = fields.Selection(
        selection=[('Contado', 'Contado'), ('Pago a 15 dias', 'Pago a 15 dias'), 
                   ('Pago a 30 dias', 'Pago a 30 dias'), ('Pago a 90 dias', 'Pago a 90 dias'), ],
        string=_('Condiciones de formato'),
        related='partner_id.condicione_pago'
    )
    methodo_pago = fields.Selection(
        selection=[('01', '01 - Efectivo'), ('02', '02 - Cheque nominativo'), 
                   ('03', '03 - Transferencia electrónica de fondos'),
                   ('04', '04 - Tarjeta de Crédito'), ('05', '05 - Monedero electrónico'),
                   ('06', '06 - Dinero electrónico'), ('08', '08 - Vales de despensa'), 
                   ('28', '28 - Tarjeta de débito'), ('29', '29 - Tarjeta de servicios'), 
                   ('99', '99 - Otros'), ('98', '98 - NA'),],
        string=_('Método de pago'),
        related='partner_id.methodo_pago'
    )
    num_cta_pago = fields.Char(string=_('Núm. Cta. Pago'), 
        related='partner_id.num_cta_pago')
    xml_invoice_link = fields.Char(string=_('XML Invoice Link'))
    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'), 
                   ('problemas_factura', 'Problemas con la factura'), ('factura_cancelada', 'Factura cancelada'), ],
        string=_('Estado de factura'),
        default='factura_no_generada',
        readonly=True
    )
    pdf_cdfi_invoice = fields.Binary("CDFI Invoice")
    qrcode_image = fields.Binary("QRCode")
    regimen_fiscal = fields.Char(string=_('Regimen fiscal'))
    numero_cetificado = fields.Char(string=_('Numero de cetificado'))
    cetificaso_sat = fields.Char(string=_('Cetificao SAT'))
    folio_fiscal = fields.Char(string=_('Folio Fiscal'))
    fecha_certificacion = fields.Char(string=_('Fecha y Hora Certificación'))
    cadena_origenal = fields.Char(string=_('Cadena Origenal del Complemento digital de SAT'))
    selo_digital_cdfi = fields.Char(string=_('Selo Digital del CDFI'))
    selo_sat = fields.Char(string=_('Selo del SAT'))
    moneda = fields.Char(string=_('Moneda'))
    tipocambio = fields.Char(string=_('TipoCambio'))
    folio = fields.Char(string=_('Folio'))
    version = fields.Char(string=_('Version'))
    number_folio = fields.Char(string=_('Folio'), compute='_get_number_folio')
    amount_to_text = fields.Char('Amount to Text', compute='_get_amount_to_text',
                                 size=256, 
                                 help='Amount of the invoice in letter')
    qr_value = fields.Char(string=_('QR Code Value'))
    invoice_datetime = fields.Char(string=_('11/12/17 12:34:12'))
    rfc_emisor = fields.Char(string=_('RFC'))
    name_emisor = fields.Char(string=_('Name'))
    serie_emisor = fields.Char(string=_('A'))
    
    @api.depends('number')
    @api.one
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('INV','').replace('/','')
            
    @api.depends('amount_total', 'currency_id')
    @api.one
    def _get_amount_to_text(self):
        self.amount_to_text = amount_to_text_es_MX.get_amount_to_text(self, self.amount_total, 'es_cheque', self.currency_id.name)
        
    @api.model
    def _get_amount_2_text(self, amount_total):
        return amount_to_text_es_MX.get_amount_to_text(self, amount_total, 'es_cheque', self.currency_id.name)
            
    
    @api.model
    def to_json(self):
        request_params = { 
                'company': {
                      'rfc': self.company_id.rfc,
                      'api_key': self.company_id.api_key,
                      'modo_prueba': self.company_id.modo_prueba,
                },
                'customer': {
                      'name': self.partner_id.name,
                      'rfc': self.partner_id.rfc,
                      'street': self.partner_id.street,
                      'street2': self.partner_id.street2,
                      'numero_interior': self.partner_id.numero_interior,
                      'colonia': self.partner_id.colonia,
                      'municipio': self.partner_id.municipio,
                      'state': self.partner_id.state_id.name,
                      'city': self.partner_id.city,
                      'country': self.partner_id.country_id.name,
                      'postalcode': self.partner_id.zip,
                      'email': self.partner_id.email,
                },
                'invoice': {
                      'tipo_comprobante': self.tipo_comprobante,
                      'tipo_formato': self.tipo_formato,
                      'forma_pago': self.forma_pago,
                      'condicione_pago': self.condicione_pago,
                      'methodo_pago': self.methodo_pago,
                      'lugarexpedicion': _('%s %s' % (self.company_id.city, self.company_id.state_id.name)),
                      'num_cta_pago': self.num_cta_pago,
                      'subtotal': self.amount_untaxed,
                      'total': self.amount_total,
                      'folio': self.number.replace('INV','').replace('/',''),
                      'serie_factura': self.company_id.serie_factura,
                },
        }
        amount_total = 0.0
        amount_untaxed = 0.0
        tax_grouped = {}
        items = {'numerodepartidas': len(self.invoice_line_ids)}
        invoice_lines = []
        for line in self.invoice_line_ids:
            if line.quantity < 0:
                continue
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            amounts = line.invoice_line_tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id,
                                                         partner=line.invoice_id.partner_id)
        
            price_exclude_tax = amounts['total_excluded']
            price_include_tax = amounts['total_included']
            if line.invoice_id:
                price_exclude_tax = line.invoice_id.currency_id.round(price_exclude_tax)
                price_include_tax = line.invoice_id.currency_id.round(price_include_tax)
            amount_untaxed += price_exclude_tax
            amount_total += price_include_tax
            print 'price_exclude_tax: ', price_exclude_tax
            invoice_lines.append({
                      'quantity': line.quantity,
                      'unidad_medida': line.product_id.unidad_medida,
                      'product': line.product_id.code,
                      'price_unit': price_exclude_tax / line.quantity,
                      'amount': line.price_subtotal,
                      'description': line.product_id.name,
                })
            
            taxes = amounts['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': line.invoice_id.id,
                    'name': tax['name'],
                    'tax_id': tax['id'],
                    'amount': tax['amount'],
                }
                key = tax['id']
                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
        request_params['invoice'].update({'subtotal': amount_untaxed, 'total': amount_total})
        items.update({'invoice_lines': invoice_lines})
        request_params.update({'items': items})
        tax_lines = []
        tax_count = 0
        for line in tax_grouped.values():
            tax_count += 1
            tax = self.env['account.tax'].browse(line['tax_id'])
            tax_lines.append({
                      'name': line['name'],
                      'percentage': tax.amount,
                      'amount': line['amount'],
                })
        taxes = {'numerodeimpuestos': tax_count}
        if tax_lines:
            taxes.update({'tax_lines': tax_lines})
        request_params.update({'taxes': taxes})
        print request_params
        return request_params
        
    @api.multi
    def invoice_validate(self):
        # after validate, send invoice data to external system via http post
        for invoice in self:
            if invoice.factura_cfdi:
                values = invoice.to_json()
                url = '%s%s' % (invoice.company_id.http_factura, '/invoice?handler=OdooHandler')
                response = requests.post(url , 
                                         auth=None,verify=False, data=json.dumps(values), 
                                         headers={"Content-type": "application/json"})
    
                #print 'Response: ', response.status_code
                json_response = response.json()
                xml_file_link = False
                estado_factura = json_response['estado_factura']
                if estado_factura == 'problemas_factura':
                    raise UserError(_('Error para timbrar factura, favor de revisar los datos de facturación. Si el error persiste, contacte a soporte técnico.'))
                # Receive and stroe XML invoice
                if json_response.get('factura_xml'):
                    xml_file_link = invoice.company_id.factura_dir + '/' + invoice.number.replace('/', '_') + '.xml'
                    xml_file = open(xml_file_link, 'w')
                    xml_invoice = base64.b64decode(json_response['factura_xml'])
                    xml_file.write(xml_invoice)
                    xml_file.close()
                    invoice._set_data_from_xml(xml_invoice)
                invoice.write({'estado_factura': estado_factura,
                               'xml_invoice_link': xml_file_link})
        result = super(AccountInvoice, self).invoice_validate()
        return result
    
    @api.one
    def _set_data_from_xml(self, xml_invoice):
        if not xml_invoice:
            return None
        NSMAP = {
                 'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                 'cfdi':'http://www.sat.gob.mx/cfd/3', 
                 'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                 }
        # xml_invoice = open('RIRF810817A38_235.xml', 'rb').read()
        xml_data = etree.fromstring(xml_invoice)
        Emisor = xml_data.find('cfdi:Emisor', NSMAP)
        RegimenFiscal = Emisor.find('cfdi:RegimenFiscal', NSMAP)
        Complemento = xml_data.find('cfdi:Complemento', NSMAP)
        TimbreFiscalDigital = Complemento.find('tfd:TimbreFiscalDigital', NSMAP)
        
        self.rfc_emisor = Emisor.attrib['rfc']
        self.name_emisor = Emisor.attrib['nombre']
        self.methodo_pago = xml_data.attrib['metodoDePago']
        self.forma_pago = _(xml_data.attrib['formaDePago'])
        self.condicione_pago = xml_data.attrib['condicionesDePago']
        self.num_cta_pago = xml_data.get('NumCtaPago', '')
        self.tipocambio = xml_data.attrib['TipoCambio']
        self.tipo_comprobante = xml_data.attrib['tipoDeComprobante']
        self.moneda = xml_data.attrib['Moneda']
        self.regimen_fiscal = RegimenFiscal.attrib['Regimen']
        self.numero_cetificado = xml_data.attrib['noCertificado']
        self.cetificaso_sat = TimbreFiscalDigital.attrib['noCertificadoSAT']
        self.fecha_certificacion = TimbreFiscalDigital.attrib['FechaTimbrado']
        self.selo_digital_cdfi = TimbreFiscalDigital.attrib['selloCFD']
        self.selo_sat = TimbreFiscalDigital.attrib['selloSAT']
        self.folio_fiscal = TimbreFiscalDigital.attrib['UUID']
        self.folio = xml_data.attrib['folio']
        self.serie_emisor = xml_data.attrib['serie']
        self.invoice_datetime = xml_data.attrib['fecha']
        self.version = TimbreFiscalDigital.attrib['version']
        self.cadena_origenal = '||%s|%s|%s|%s|%s||' % (self.version, self.folio_fiscal, self.fecha_certificacion, 
                                                         self.selo_digital_cdfi, self.cetificaso_sat)
        
        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.amount_total).split('.')
        print 'amount_str, ', amount_str
        qr_value = '?re=%s&rr=%s&tt=%s.%s&id=%s' % (self.company_id.rfc, 
                                                 self.partner_id.rfc,
                                                 amount_str[0].zfill(10),
                                                 amount_str[1].ljust(6, '0'),
                                                 self.folio_fiscal
                                                 )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodestring(ret_val.asString('jpg'))
    
    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):
        for invoice in self:
            if not invoice.factura_cfdi:
                continue
            if invoice.estado_factura == 'factura_cancelada':
                raise UserError(_('The invoice already refunded, can''t be opened again.'))
            values = {
                      'rfc': self.company_id.rfc,
                      'api_key': self.company_id.api_key,
                      'folio': self.folio,
                      'serie_factura': self.company_id.serie_factura,
                      'modo_prueba': self.company_id.modo_prueba,
                      }
            url = '%s%s' % (invoice.company_id.http_factura, '/refund?handler=OdooHandler')
            response = requests.post(url , 
                                     auth=None,verify=False, data=json.dumps(values), 
                                     headers={"Content-type": "application/json"})

            print 'Response: ', response.status_code
            json_response = response.json()
            # print json.dumps(json_response, indent=4, sort_keys=True)
            # if json_response['estado_factura'] == 'factura_cancelada':
            invoice.write({'estado_factura': json_response['estado_factura']})
            
            if json_response['estado_factura'] == 'problemas_factura':
                raise UserError(_('Error para cancelar factura, debe esperar 24 hrs para cancelar una factura. Si el error persiste, contacte a soporte técnico.'))
        return super(AccountInvoice, self).refund(date_invoice=date_invoice, date=date, description=description, journal_id=journal_id)

    @api.multi
    def print_cdfi_invoice(self):
        self.ensure_one()
        #return self.env['report'].get_action(self, 'custom_invoice.cdfi_invoice_report') #modulename.custom_report_coupon 
        filename = 'CDFI_' + self.number.replace('/', '_') + '.pdf'
        return {
                 'type' : 'ir.actions.act_url',
                 'url': '/web/binary/download_document?model=account.invoice&field=pdf_cdfi_invoice&id=%s&filename=%s'%(self.id, filename),
                 'target': 'self',
                 }
 
 
class MailTemplate(models.Model):
    "Templates for sending email"
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        results = super(MailTemplate, self).generate_email(res_ids, fields=fields)
        
        if isinstance(res_ids, (int, long)):
            res_ids = [res_ids]
        res_ids_to_templates = super(MailTemplate, self).get_email_template(res_ids)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.iteritems():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        for template, template_res_ids in templates_to_res_ids.iteritems():
            if template.report_template and template.report_template.report_name == 'account.report_invoice':
                for res_id in template_res_ids:
                    invoice = self.env[template.model].browse(res_id)
                    if not invoice.factura_cfdi:
                        continue
                    xml_file = open(invoice.xml_invoice_link, 'rb').read()
                    attachments = results[res_id]['attachments'] or []
                    attachments.append(('CDFI_' + invoice.number.replace('/', '_') + '.xml', 
                                        base64.b64encode(xml_file)))
                    results[res_id]['attachments'] = attachments
        return results

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:            
    