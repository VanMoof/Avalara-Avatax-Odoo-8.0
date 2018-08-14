# coding: utf-8
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    tax_amt = fields.Float(
        'Avalara Tax Amount', digits=dp.get_precision('Account'))

    @api.model
    def move_line_get(self, invoice_id):
        """ Override to replace tax computation if AvaTax applies.
        FIXME: this is currently broken in combination with another tax on the
        line (and/or order based taxes).
        """
        invoice = self.env['account.invoice'].browse(invoice_id)
        avatax_config = self.env[
            'avalara.salestax']._get_avatax_config_company(
                company=invoice.company_id)
        if (not avatax_config or avatax_config.disable_tax_calculation or
                invoice.partner_id.country_id
                not in avatax_config.country_ids):
            return super(InvoiceLine, self).move_line_get(invoice_id)

        if any(line.invoice_line_tax_id for line in invoice.invoice_line):
            raise UserError(
                _('Taxes on this invoice are fetched using AvaTax. '
                  'Manually added taxes are not supported. Please remove '
                  'these taxes from the invoice lines.'))
        res = []
        currency = invoice.currency_id.with_context(date=invoice.date_invoice)

        for line in invoice.invoice_line:
            mres = self.move_line_get_item(line)
            if not mres:
                continue
            res.append(mres)
            tax_code_found = False

            for tax in self.env['account.invoice.tax'].compute(
                    invoice).values():
                tax_code_id = tax['base_code_id']
                if invoice.type in ('out_invoice', 'in_invoice'):
                    tax_amount = line.price_subtotal * tax['base_sign'] or 1.0
                else:
                    tax_amount = line.price_subtotal * tax['ref_base_sign']
                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(dict(mres))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = currency.compute(
                    tax_amount, invoice.company_id.currency_id)
        return res

    @api.multi
    def create_avalara_lines(self, config, sign=1):
        lines = []
        for line in self:
            # Add UPC to product item code
            if line.product_id.ean13 and config.upc_enable:
                item_code = 'upc:%s' % line.product_id.ean13
            else:
                item_code = line.product_id.default_code

            tax_code = (line.product_id.tax_code_id or
                        line.product_id.categ_id.tax_code_id).name or None

            # Calculate discount amount
            discount_amount = 0.0
            is_discounted = False
            if line.discount:
                discount_amount = sign * line.quantity * (
                    line.price_unit * ((line.discount or 0.0) / 100.0))
                is_discounted = True
            lines.append({
                'qty': line.quantity,
                'itemcode': item_code or None,
                'description': line.name,
                'discounted': is_discounted,
                'discount': discount_amount,
                'amount': sign * line.quantity * (
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                'tax_code': tax_code,
            })
        return lines
