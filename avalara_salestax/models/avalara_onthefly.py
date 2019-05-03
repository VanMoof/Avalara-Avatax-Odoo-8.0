# coding: utf-8
# © 2019 Vanmoof B.V. (<https://vanmoof.com)
# © 2019 Opener B.V. (<https://opener.amsterdam>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from uuid import uuid1
from openerp import api, fields, models
from openerp.addons.avalara_salestax.avalara_api import (
    AvaTaxService, BaseAddress)
from openerp.exceptions import ValidationError
from openerp.tools import ormcache


class AvalaraOnthefly(models.AbstractModel):
    _name = 'avalara.onthefly'

    @ormcache(skiparg=1)
    @api.model
    def address_to_latlong(
            self, street, street2, city, zip_code, state_code, country_code):
        config = self.env['avalara.salestax']._get_avatax_config_company()
        if not config or country_code not in config.country_ids.mapped('code'):
            return None, None
        avataxservice = AvaTaxService(
            config.account_number, config.license_key,
            config.service_url.encode('ascii'), config.request_timeout,
            config.logging)
        baseaddress = BaseAddress(
            avataxservice.create_address_service().addressSvc,
            street or None,
            street2 or None,
            city or None,
            zip_code or None,
            state_code or None,
            country_code or None, 0).data
        valid_address = avataxservice.validate_address(
            baseaddress,
            config.result_in_uppercase and 'Upper' or 'Default'
        ).ValidAddresses[0][0]
        return valid_address.Latitude, valid_address.Longitude

    @api.model
    def get_tax(self, origin_latitude, origin_longitude,
                dest_latitude, dest_longitude, lines, date=None):
        """ Get tax amount on the fly given the coordinates of the origin
        and destination address (see address_to_latlong above).

        :param lines: list of tuples (product.product(), uom_qty, unit_price)
        """
        config = self.env['avalara.salestax']._get_avatax_config_company()
        avataxservice = AvaTaxService(
            config.account_number, config.license_key,
            config.service_url.encode('ascii'), config.request_timeout,
            config.logging)
        coordinates = [origin_latitude, origin_longitude,
                       dest_latitude, dest_longitude]
        if not all(coordinates):
            raise ValidationError(
                'Please pass valid coordinates: {}'.format(coordinates))
        date = date or fields.Date.context_today(self)
        avataxservice.create_address_service()
        avataxservice.create_tax_service()

        origin = avataxservice.addressSvc.factory.create('BaseAddress')
        origin.AddressCode = 0  # meaning: source
        origin.Latitude = origin_latitude
        origin.Longitude = origin_longitude
        origin.TaxRegionId = 0

        destination = avataxservice.addressSvc.factory.create('BaseAddress')
        destination.AddressCode = 1  # meaning: destination
        destination.Latitude = dest_latitude
        destination.Longitude = dest_longitude
        destination.TaxRegionId = 0

        avalara_lines = []
        for product, uom_qty, unit_price in lines:
            tax_code = (
                product.tax_code_id or
                product.categ_id.tax_code_id).name or None
            avalara_lines.append({
                'qty': uom_qty,
                'itemcode': product.default_code or None,
                'description': product.name,
                'amount': uom_qty * unit_price,
                'tax_code': tax_code,
            })
        return avataxservice.get_tax(
            config.company_code, date, 'SalesOrder',
            uuid1(), None, origin, destination,
            avalara_lines, commit=False).TotalTax
