# coding: utf-8
import logging
from openerp import api, fields, models
from openerp.addons.avalara_salestax.avalara_api import (
    AvaTaxService, BaseAddress)
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class AccountTax(models.Model):
    """ Inherit to implement the tax using avatax API """
    _inherit = "account.tax"

    @api.model
    def _get_compute_tax(
            self, config, doc_date, doc_code, doc_type, partner,
            ship_from_address, shipping_address, lines,
            user=None, exemption_number=None, exemption_code_name=None,
            commit=False, invoice_date=False, reference_code=False,
            location_code=False):
        # TODO: get actual currency from order or invoice
        currency_code = self.env.user.company_id.currency_id.name
        if not partner.customer_code:
            if not config.auto_generate_customer_code:
                raise UserError(_(
                    'Customer Code for customer %s not defined. Try clicking '
                    'the "Generate Customer Code" button on the address '
                    'form.') % partner.name)
            partner.sudo().generate_cust_code()

        if not shipping_address:
            raise UserError(_('AvaTax: No Shipping Address Defined'))
        if not lines:
            raise UserError(_('AvaTax needs at least one sale order line '
                              'to compute tax'))

        if (not config.address_validation and
                not shipping_address.date_validation):
            raise UserError(
                _('Automatic address validation is disabled. Please validate '
                  'the shipping address for the partner %s manually.') %
                shipping_address.name)
        if not ship_from_address:
            raise UserError(_('AvaTax: there is no company address defined.'))

        if (not config.address_validation and
                not ship_from_address.date_validation):
            raise UserError(
                _('Automatic address validation is disabled. Please validate '
                  'the company address %s manually.') % ship_from_address.name)

        # For check credential
        avalara_obj = AvaTaxService(
            config.account_number, config.license_key,
            config.service_url.encode('ascii'), config.request_timeout,
            config.logging)
        avalara_obj.create_tax_service()
        addSvc = avalara_obj.create_address_service().addressSvc
        origin = BaseAddress(
            addSvc, ship_from_address.street or None,
            ship_from_address.street2 or None,
            ship_from_address.city, ship_from_address.zip,
            ship_from_address.state_id.code or None,
            ship_from_address.country_id.code or None, 0).data
        destination = BaseAddress(
            addSvc, shipping_address.street or None,
            shipping_address.street2 or None,
            shipping_address.city, shipping_address.zip,
            shipping_address.state_id.code or None,
            shipping_address.country_id.code or None, 1).data

        # Convert datetime to date to prevent errors like
        # "String was not recognized as a valid DateTime" (sic)
        if doc_date and len(doc_date) > 10:
            doc_date = fields.Date.context_today(
                self, timestamp=fields.Datetime.from_string(doc_date))
        if invoice_date and len(invoice_date) > 10:
            invoice_date = fields.Date.context_today(
                self, timestamp=fields.Datetime.from_string(invoice_date))

        # using get_tax method to calculate tax based on address
        return avalara_obj.get_tax(
            config.company_code, doc_date, doc_type,
            partner.customer_code, doc_code, origin, destination,
            lines, exemption_number,
            exemption_code_name,
            user and user.name or None, commit, invoice_date, reference_code,
            location_code, currency_code, partner.vat or None)

    @api.model
    def cancel_tax(self, config, doc_code, doc_type, cancel_code):
        """ Cancel previously registered tax """
        avalara_obj = AvaTaxService(
            config.account_number, config.license_key,
            config.service_url.encode('ascii'), config.request_timeout,
            config.logging)
        avalara_obj.create_tax_service()
        try:
            avalara_obj.get_tax_history(
                config.company_code, doc_code, doc_type)
        except Exception as e:  # Presumably, registered tax is not found
            logging.getLogger(__name__).exception(
                'Failed to fetch tax history for code %s: %s', doc_code, e)
            return True
        return avalara_obj.cancel_tax(
            config.company_code, doc_code, doc_type, cancel_code)
