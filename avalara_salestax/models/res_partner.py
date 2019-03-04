# coding: utf-8
import logging
from random import random
import time
from openerp import api, fields, models
from openerp.addons.avalara_salestax.avalara_api import (
    AvaTaxService, BaseAddress)
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    exemption_number = fields.Char(
        'Avalara Exemption Number',
        help='Indicates if the customer is exempt or not for Avalara taxes')
    exemption_code_id = fields.Many2one(
        'exemption.code', 'Avalara Exemption Code',
        help='Indicates the type of exemption the customer may have')
    date_validation = fields.Date(
        'Last Validation Date', readonly=True,
        help='The date the address was last validated by AvaTax and accepted')
    validation_method = fields.Selection(
        [('avatax', 'AVALARA'), ('usps', 'USPS'),
         ('other', 'Other')], 'Address Validation Method', readonly=True,
        help='It gets populated when the address is validated by the method')
    latitude = fields.Char()
    longitude = fields.Char()
    validated_on_save = fields.Boolean(
        'Validated On Save',
        help='Indicates if the address was validated automatically')
    customer_code = fields.Char('Avalara Customer Code', copy=False)
    tax_apply = fields.Boolean(
        'Tax Calculation',
        help='Indicates that AvaTax calculation is compulsory')
    tax_exempt = fields.Boolean(help='Exempted from AvaTax calculation')

    @api.multi
    def format_tax_address(self):
        self.ensure_one()
        city = ('%s,' % self.city) if self.city else False
        lines = (
            self.name,
            self.street,
            ' '.join(filter(None, (city, self.state_id.name, self.zip))),
            self.country_id.name)
        return '\n'.join(filter(None, lines))

    @api.multi
    def generate_cust_code(self):
        """ Populate customer code """
        prefix = '%s-%s-Cust-' % (time.time(), int(random() * 10))
        for partner in self:
            if not self.customer_code:
                self.customer_code = prefix + str(partner.id)

    @api.model
    def get_country_by_code(self, code):
        return self.env['res.country'].search(
            [('code', '=', code)], limit=1)

    @api.model
    def get_state_by_code(self, code, country_code):
        country = self.get_country_by_code(country_code)
        return self.env['res.country.state'].search(
            [('code', '=', code), ('country_id', '=', country.id)], limit=1)

    @api.multi
    def multi_address_validation(self, auto=True):
        config = self.env['avalara.salestax']._get_avatax_config_company()
        if not config:
            return
        avapoint = AvaTaxService(
            config.account_number, config.license_key,
            config.service_url, config.request_timeout,
            config.logging)
        addSvc = avapoint.create_address_service().addressSvc

        for partner in self:
            if (not partner.country_id or
                    partner.country_id not in config.country_ids):
                if not auto:
                    return None
                continue
            baseaddress = BaseAddress(
                addSvc, partner.street or None,
                partner.street2 or None,
                partner.city or None,
                partner.zip or None,
                partner.state_id.code or None,
                partner.country_id.code or None, 0).data
            try:
                valid_address = avapoint.validate_address(
                    baseaddress,
                    config.result_in_uppercase and 'Upper' or 'Default'
                ).ValidAddresses[0][0]
            except Exception as e:
                if not auto:
                    raise
                logging.getLogger(__name__).exception(
                    'Could not validate address %s: %s',
                    partner.name, e)
                continue
            vals = {
                'street': valid_address.Line1,
                'street2': valid_address.Line2,
                'city': valid_address.City,
                'state_id': self.get_state_by_code(
                    valid_address.Region, valid_address.Country).id,
                'zip': valid_address.PostalCode,
                'country_id': self.get_country_by_code(
                    valid_address.Country).id,
                'latitude': valid_address.Latitude,
                'longitude': valid_address.Longitude,
                'date_validation': fields.Date.context_today(self),
                'validation_method': 'avatax',
                'validated_on_save': True
            }
            if not auto:  # Don't write
                return vals

            super(ResPartner, partner).write(vals)

        return {
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.ids)],
        }

    @api.multi
    def verify_address_validatation(self):
        """Method is used to verify of state and country """
        self.ensure_one()
        wizard = self.env['avalara.salestax.address.validate'].with_context(
            active_ids=self.ids, active_id=self.ids[0]).create({})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Address Validation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard._name,
            'res_id': wizard.id,
            'target': 'new',
            'context': {'active_ids': self.ids},
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(customer_code)',
         'Customer Code must be unique!'),
    ]

    @api.constrains('tax_exempt', 'exemption_number', 'exemption_code_id')
    def _check_exemption(self):
        for partner in self:
            if partner.tax_exempt and (
                    not partner.exemption_number and
                    not partner.exemption_code_id):
                raise ValidationError(
                    'If the partner is tax exempt, please add an exemption '
                    'number or an exemption code: %s' % partner.name)

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        config = self.env['avalara.salestax']._get_avatax_config_company()
        if config:
            if (not self.env.context.get('from_validate_button') and
                    config.validation_on_save):
                res.multi_address_validation()
            if config.auto_generate_customer_code:
                res.generate_cust_code()
        return res

    @api.multi
    def write(self, vals):
        """ Apply automatic address validation if applicable """
        res = super(ResPartner, self).write(vals)
        if not self.env.context.get('from_validate_button') and any(
                field in vals for field in (
                    'street', 'street2', 'zip', 'city', 'country_id',
                    'state_id')):
            config = self.env['avalara.salestax']._get_avatax_config_company()
            if config and config.validation_on_save:
                self.multi_address_validation()
        return res
