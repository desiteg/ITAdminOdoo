# -*- coding: utf-8 -*-
##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C)2004-TODAY Tech Receptives(<https://www.techreceptives.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json

class Website(models.Model):
    _inherit = 'website'

    recaptcha_site_key = fields.Char('reCAPTCHA Site Key', default='6LchkgATAAAAAAdTJ_RCvTRL7_TTcN3Zm_YXB39s')
    recaptcha_private_key = fields.Char('reCAPTCHA Private Key', default='6LchkgATAAAAADbGqMvbRxHbTnTEkavjw1gSwCng')

    @api.multi
    def is_captcha_valid(self, response):
        for website in self:
            get_res = {'secret': website.recaptcha_private_key,'response': response}
            try:
                response = requests.get('https://www.google.com/recaptcha/api/siteverify', params=get_res)
            except Exception,e:
                raise UserError(('Invalid Data!'),("%s.")%(e))
            res_con = json.loads(response.content)
            if res_con.has_key('success') and res_con['success']:
                return True
        return False
