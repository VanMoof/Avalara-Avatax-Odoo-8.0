# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class AddressValidate(models.TransientModel):
    """Address Validation using Avalara API"""
    _name = 'avalara.salestax.address.validate'
    _rec_name = 'partner_id'
    _description = 'Address Validation using AvaTax'

    partner_id = fields.Many2one('res.partner', readonly=True)
    original_street = fields.Char('Street', readonly=True)
    original_street2 = fields.Char('Street2', readonly=True)
    original_city = fields.Char('City', readonly=True)
    original_zip = fields.Char('Zip', readonly=True)
    original_state_id = fields.Many2one(
        'res.country.state', 'State', readonly=True)
    original_country_id = fields.Many2one(
        'res.country', 'Country', readonly=True)
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    state_id = fields.Many2one('res.country.state', 'State')
    country_id = fields.Many2one('res.country', 'Country')
    latitude = fields.Char()
    longitude = fields.Char()

    @api.model
    def default_get(self, fields):
        """  Returns the default values for the fields. """
        res = super(AddressValidate, self).default_get(fields)
        if self.env.context.get('active_id') and (
                not fields or 'original_street' in fields):
            partner = self.env['res.partner'].browse(
                self.env.context['active_id'])
            if not partner.country_id:
                raise UserError(_('Please enter the customer country first.'))
            # Get the valid result from the AvaTax Address Validation Service
            vals = partner.multi_address_validation(auto=False)
            if vals is None:
                raise UserError(_(
                    'No valid configuration found or customer country (%s) '
                    'not supported') % partner.country_id.name or '-')
            for key in [key for key in vals.keys() if key not in self._fields]:
                vals.pop(key)
            res.update(vals)
            res.update({
                'partner_id': partner.id,
                'original_street': partner.street,
                'original_street2': partner.street2,
                'original_city': partner.city,
                'original_state_id': partner.state_id.id,
                'original_zip': partner.zip,
                'original_country_id': partner.country_id.id,
            })
        return res

    @api.multi
    def accept_valid_address(self):
        """ Updates the existing address with the valid address returned by
        the service. """
        self.partner_id.write({
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': self.state_id.id,
            'zip': self.zip,
            'country_id': self.country_id.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'date_validation': fields.Date.context_today(self),
            'validation_method': 'avatax'
        })
        return {'type': 'ir.actions.act_window_close'}
