# coding: utf-8
import logging
from os import environ
from openerp.exceptions import Warning as UserError
from openerp.tests.common import TransactionCase


def get_config(env):
    config = env['avalara.salestax'].search([], limit=1)
    if not config and environ.get('AVATAX_COMPANY_CODE'):
        logging.getLogger(__name__).info(
            'Creating Avatax account from environment variables')
        config = env['avalara.salestax'].create({
            'company_code': environ['AVATAX_COMPANY_CODE'],
            'date_expiration': '1998-12-31',
            'company_id': env.ref('base.main_company').id,
            'disable_tax_reporting': True,
            'service_url': 'https://development.avalara.net',
            'license_key': environ['AVATAX_LICENSE_KEY'],
            'account_number': environ['AVATAX_ACCOUNT_NUMBER'],
        })
    if not config:
        raise UserError('No Avatax configuration found.')
    return config


class AvalaraTestSetUp(TransactionCase):
    def setUp(self):
        super(AvalaraTestSetUp, self).setUp()
        self.config = get_config(self.env)
        self.config.write({
            'service_url': 'https://development.avalara.net',
            'auto_generate_customer_code': True,
            'validation_on_save': True,
            'address_validation': True,
        })
        self.company = self.config.company_id
        self.company.currency_id = self.env.ref('base.USD')
        self.env.user.company_id = self.company
        new_york = self.env.ref('base.state_us_27')
        self.company.partner_id.write({
            'street': '324 Wythe Ave',
            'street2': False,
            'zip': 'NY 11249',
            'state_id': new_york.id,
            'country_id': new_york.country_id.id,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer',
            'street': '322 Wythe Ave',
            'street2': False,
            'zip': 'NY 11249',
            'state_id': new_york.id,
            'country_id': new_york.country_id.id,
        })
