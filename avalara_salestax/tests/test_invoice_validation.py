# coding: utf-8
from uuid import uuid1
from testfixtures import LogCapture
from .common import AvalaraTestSetUp


class TestInvoiceValidationSetUp(AvalaraTestSetUp):
    def setUp(self):
        super(TestInvoiceValidationSetUp, self).setUp()
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.company.id)],
            limit=1)
        journal.sequence_id.prefix = uuid1()
        account = self.env['account.account'].search(
            [('type', '=', 'other'), ('company_id', '=', self.company.id)],
            limit=1)
        self.invoice = self.env['account.invoice'].create({
                'type': 'out_invoice',
                'partner_id': self.customer.id,
                'journal_id': journal.id,
                'account_id': self.customer.property_account_payable.id,
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
