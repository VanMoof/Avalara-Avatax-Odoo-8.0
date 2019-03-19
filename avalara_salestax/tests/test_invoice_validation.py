# coding: utf-8
from uuid import uuid1
from testfixtures import LogCapture
from .common import get_config
from openerp.tests.common import TransactionCase


class TestInvoiceValidationSetUp(TransactionCase):
    def setUp(self):
        super(TestInvoiceValidationSetUp, self).setUp()
        config = get_config(self.env)
        config.write({
            'service_url': 'https://development.avalara.net',
            'auto_generate_customer_code': True,
            'validation_on_save': True,
            'address_validation': True,
        })
        company = config.company_id
        self.env.user.company_id = company
        new_york = self.env.ref('base.state_us_27')
        company.partner_id.write({
            'street': '324 Wythe Ave',
            'street2': False,
            'zip': 'NY 11249',
            'state_id': new_york.id,
            'country_id': new_york.country_id.id,
        })
        customer = self.env['res.partner'].create({
            'name': 'Customer',
            'street': '322 Wythe Ave',
            'street2': False,
            'zip': 'NY 11249',
            'state_id': new_york.id,
            'country_id': new_york.country_id.id,
        })
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        journal.sequence_id.prefix = uuid1()
        account = self.env['account.account'].search([
            ('type', '=', 'other'), ('company_id', '=', company.id)], limit=1)
        self.invoice = self.env['account.invoice'].create({
                'type': 'out_invoice',
                'partner_id': customer.id,
                'journal_id': journal.id,
                'account_id': customer.property_account_payable.id,
                'invoice_line': [(0, False, {
                    'product_id': False,
                    'name': 'Test Ë',
                    'account_id': account.id,
                    'quantity': 1,
                    'price_unit': 100.00},
                )],
            })


class TestInvoiceValidation(TestInvoiceValidationSetUp):
    def test_01_invoice_validation(self):
        """ Avalara computation is executed on invoice confirmation """
        with LogCapture(
                'openerp.addons.avalara_salestax.avalara_api') as capture:
            self.invoice.signal_workflow('invoice_open')
        self.assertIn('Committing',
                      ''.join(record.msg for record in capture.records))
