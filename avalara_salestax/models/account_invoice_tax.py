# coding: utf-8
from openerp import api, fields, models
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    @api.v8
    def compute(self, invoice):
        """ Append or amend a group with the Avalara tax """
        tax_grouped = super(AccountInvoiceTax, self).compute(invoice)
        config, partner = invoice.test_avalara()
        if config:
            currency = invoice.currency_id.with_context(
                date=invoice.date_invoice or fields.Date.context_today(self))
            company_currency = invoice.company_id.currency_id
            tax = self.env['account.tax'].search(
                [('name', '=', 'AVATAX'),
                 ('company_id', '=', invoice.company_id.id)], limit=1)
            if not tax:
                raise UserError(_(
                    'Please configure a tax called "AVALARA" for this '
                    'company.'))
            val = {
                'invoice_id': invoice.id,
                'name': tax.name,
                'amount': invoice.tax_amount,
                'manual': False,
                'sequence': tax.sequence,
                'base': invoice.amount_untaxed,
            }
            # TODO: while we have the correct tax_amount for taxes per line,
            # if the revenue account of the invoice line is used all tax
            # amounts end up on the account of the first line until we start
            # iterating over invoice lines here instead of doing one big
            # sweep
            if invoice.type in ('out_invoice', 'in_invoice'):
                val.update({
                    'base_code_id': tax.base_code_id.id,
                    'tax_code_id': tax.tax_code_id.id,
                    'base_amount': currency.compute(
                        val['base'] * tax.base_sign, company_currency,
                        round=False),
                    'tax_amount': currency.compute(
                        val['amount'] * tax.tax_sign, company_currency,
                        round=False),
                    'account_id': (tax.account_collected_id.id or
                                   invoice.invoice_line[0].account_id.id),
                    'account_analytic_id': (
                        tax.account_analytic_collected_id.id),
                    'base_sign': tax.base_sign,
                })
            else:
                val.update({
                    'base_code_id': tax.ref_base_code_id.id,
                    'tax_code_id': tax.ref_tax_code_id.id,
                    'base_amount': currency.compute(
                        val['base'] * tax.ref_base_sign, company_currency,
                        round=False),
                    'tax_amount': currency.compute(
                        val['amount'] * tax.ref_tax_sign, company_currency,
                        round=False),
                    'account_id': (tax.account_paid_id.id or
                                   invoice.invoice_line[0].account_id.id),
                    'account_analytic_id': (
                        tax.account_analytic_paid_id.id),
                    'base_sign': tax.ref_base_sign,
                })
            key = (val['tax_code_id'], val['base_code_id'],
                   val['account_id'])
            if key not in tax_grouped:
                tax_grouped[key] = val
            else:
                tax_grouped[key]['amount'] += val['amount']
                tax_grouped[key]['base'] += val['base']
                tax_grouped[key]['base_amount'] += val['base_amount']
                tax_grouped[key]['tax_amount'] += val['tax_amount']
        return tax_grouped
