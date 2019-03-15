# coding: utf-8
from openerp.exceptions import Warning as UserError
import logging
from os import environ


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
