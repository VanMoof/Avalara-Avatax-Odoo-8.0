# coding: utf-8
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_doc_no = fields.Char('Refund invoice No', size=32, readonly=True)
    invoice_date = fields.Date(
        'Original invoice date', readonly=True,
        help='Date of the invoice that this is a refund of')
    is_add_validate = fields.Boolean('Address is avalara-validated')
    exemption_code = fields.Char('Avalara Exemption Number')
    exemption_code_id = fields.Many2one(
        'exemption.code', 'Avalara Exemption code')
    shipping_lines = fields.One2many(
        'shipping.order.line', 'invoice_ship_id', 'AvaTax Shipping Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    shipping_address = fields.Text('Tax Address', readonly=True)
    location_code = fields.Char(
        'Location code', size=128, readonly=True,
        states={'draft': [('readonly', False)]})
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
        help='Determines the Avalara origin address')
    shipping_amt = fields.Float(
        string='Shipping Cost', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount')
    tax_amount = fields.Float(
        string='Avalara tax amount', digits=dp.get_precision('Account'),
        readonly=True)

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount',
                 'shipping_lines.shipping_cost')
    def _compute_amount(self):
        """ Add shipping amount to invoice total """
        super(AccountInvoice, self)._compute_amount()
        self.shipping_amt = sum(
            line.shipping_cost for line in self.shipping_lines)
        self.amount_total += self.shipping_amt

    @api.multi
    def get_tax_partner(self):
        """ partner address, on which avalara tax will calculate  """
        self.ensure_one()
        order = self.env['sale.order'].search(
            [('invoice_ids', '=', self.id)], limit=1)
        if not order and self.origin:
            a = self.origin
            if len(a.split(':')) > 1:
                so_origin = a.split(':')[1]
            else:
                so_origin = a.split(':')[0]
            order = self.env['sale.order'].search(
                [('name', '=', so_origin)], limit=1)
        if order:
            return order.get_tax_partner()
        return self.partner_id

    @api.multi
    def get_origin_address_for_tax(self):
        """ partner address, on which avalara tax will calculate  """
        self.ensure_one()
        order = self.env['sale.order'].search(
            [('invoice_ids', '=', self.id)], limit=1)
        if not order and self.origin:
            if len(self.origin.split(':')) > 1:
                so_origin = self.origin.split(':')[1]
            else:
                so_origin = self.origin.split(':')[0]
            order = self.env['sale.order'].search(
                [('name', '=', so_origin)], limit=1)
        if order and order.warehouse_id and order.warehouse_id.partner_id:
            return order.warehouse_id.partner_id
        if self.warehouse_id and order.warehouse_id.partner_id:
            return order.warehouse_id.partner_id
        return self.company_id.partner_id

    @api.multi
    def get_origin_tax_date(self):
        self.ensure_one()
        if self.invoice_date:  # stored at refund time
            return self.invoice_date
        if self.origin:
            refund = self.search([
                ('number', '=', self.origin),
                ('partner_id', '=', self.partner_id.id)], limit=1)
            if refund and refund.date_invoice:
                return refund.date_invoice
        return self.date_invoice

    @api.multi
    def get_tax_values_from_partner(self, partner):
        self.ensure_one()
        if partner.tax_exempt:
            self.exemption_code = partner.exemption_number
            self.exemption_code_id = partner.exemption_code_id
        self.tax_address = partner.format_tax_address()
        self.is_add_validate = bool(partner.validation_method)

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        partner = res.get_tax_partner()
        res.get_tax_values_from_partner(partner)
        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if vals.get('partner_id'):
            partner = self.get_tax_partner()
            self.get_tax_values_from_partner(partner)
        return res

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            self.warehouse_code = self.warehouse_id.code

    @api.multi
    def action_cancel(self):
        """ The original version of this module reset the invoice number
        and internal_number, allowing previously confirmed invoices to be
        deleted and creating gaps in invoice numbering when reconfirming
        invoices. It is likely that it did this because AvaTax does not allow
        numbers of previously voided transactions to be reused so expect an
        error when confirming a previously cancelled invoice. """
        res = super(AccountInvoice, self).action_cancel()
        for invoice in self:
            if invoice.type not in ('out_invoice', 'out_refund'):
                continue
            config = self.env['avalara.salestax'].with_context(
                force_comapany=invoice.company_id.id
            )._get_avatax_config_company()
            if not config or config.disable_tax_calculation:
                continue
            partner = self.get_tax_partner()
            if (not partner.country_id or
                    partner.country_id not in config.country_ids):
                continue
            doc_type = ('SalesInvoice'
                        if invoice.type == 'out_invoice' else 'ReturnInvoice')
            self.env['account.tax'].cancel_tax(
                config, invoice.internal_number, doc_type, 'DocVoided')
        return res

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """After validate invoice create finalize invoice move lines with
        shipping amount and also manage the debit and credit balance """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        if not self.shipping_lines:
            return move_lines
        amount = self.shipping_amt * (-1 if self.type == 'out_refund' else 1)
        move_lines.append((0, 0, {
            'analytic_account_id':  False,
            'tax_code_id':  False,
            'analytic_lines':  [],
            'tax_amount':  0,
            'name':  'Shipping Charge',
            'currency_id':  False,
            'credit':  amount if amount > 0 else 0,
            'debit': -amount if amount < 0 else 0,
            'quantity': 1,
            'partner_id': self.partner_id.id,
            'account_id': self.shipping_lines[0].account_id.id,
        }))
        # Retrieve the existing debit line if one exists
        for move_line in move_lines:
            journal_entry = move_line[2]
            if journal_entry['account_id'] == self.account_id.id:
                if amount > 0:
                    journal_entry['debit'] += amount
                else:
                    journal_entry['credit'] += -amount
                break
        else:
            raise UserError(
                'No line found on account %s for invoice %s when including '
                'the shipping amount in the financial move.' % (
                    self.account_id.code, self.name))
        return move_lines

    @api.multi
    def button_reset_taxes(self):
        for invoice in self:
            invoice.compute_tax()
        # Taxes are reset in the super method
        return super(AccountInvoice, self).button_reset_taxes()

    @api.multi
    def compute_tax(self):
        self.ensure_one()
        config, partner = self.test_avalara()
        if not config:
            return
        if config.address_validation and not partner.date_validation:
            if not config.validation_on_save:
                raise UserError(
                    'Address not avalara-validated: customer %s on invoice %s' %
                    (partner.name, self.internal_number))
            partner.multi_address_validation()

        ship_from_address = self.get_origin_address_for_tax()
        sign = 1 if self.type == 'out_invoice' else -1
        lines1 = self.invoice_line.create_avalara_lines(config, sign=sign)
        lines2 = self.shipping_lines.create_avalara_lines(sign=sign)
        date = self.date_invoice or fields.Date.context_today(self)

        tax_amount = 0
        if config.on_line:
            # Line level tax calculation
            # tax based on individual order line
            for line1, o_line in zip(lines1, self.invoice_line):
                o_line.tax_amt = sign * self.env['account.tax']._get_compute_tax(
                    config, date,
                    self.internal_number, 'SalesOrder', self.partner_id,
                    ship_from_address, partner, [line1], self.user_id,
                    self.exemption_code,
                    self.exemption_code_id.code).TotalTax
                tax_amount += o_line.tax_amt

            # tax based on individual shipping order line
            for line2, s_line in zip(lines2, self.shipping_lines):
                s_line.tax_amt = self.env['account.tax']._get_compute_tax(
                    config, date,
                    self.internal_number, 'SalesOrder', self.partner_id,
                    ship_from_address, partner, [line2],
                    self.user_id, self.exemption_code,
                    self.exemption_code_id.code).TotalTax
                tax_amount += s_line.tax_amt

        else:
            # Order level tax calculation
            tax_amount = self.env['account.tax']._get_compute_tax(
                config, date,
                self.internal_number, 'SalesOrder', self.partner_id,
                ship_from_address, partner, lines1 + lines2, self.user_id,
                self.exemption_code,
                self.exemption_code_id.code).TotalTax

            self.invoice_line.write({'tax_amt': 0.0})
            self.shipping_lines.write({'tax_amt': 0.0})
        self.tax_amount = tax_amount

    @api.multi
    def test_avalara(self):
        """ Check if Avalara taxes are applied to this invoice.
        Returns the appropriate config and tax partner, else (False, False)
        """
        self.ensure_one()
        if self.type not in ('out_invoice', 'out_refund'):
            return False, False
        config = self.env['avalara.salestax'].with_context(
            force_company=self.company_id.id)._get_avatax_config_company()
        if not config or config.disable_tax_calculation:
            return False, False
        partner = self.get_tax_partner()
        if (not partner.country_id or
                partner.country_id not in config.country_ids):
            return False, False
        return config, partner

    @api.multi
    def invoice_validate(self):
        """Commit the Avalara invoice record on invoice validation """
        to_commit = self.filtered(
            lambda inv: inv.state in ('draft', 'proforma2'))
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in to_commit:
            config, partner = invoice.test_avalara()
            if not config:
                continue
            if any(line.invoice_line_tax_id for line in invoice.invoice_line):
                raise UserError(
                    _('Taxes on this invoice are fetched using AvaTax. '
                      'Manually added taxes are not supported. Please remove '
                      'these taxes from the invoice lines.'))
            shipping_add_origin = invoice.get_origin_address_for_tax()
            tax_date = invoice.get_origin_tax_date()
            sign = 1 if invoice.type == 'out_invoice' else -1
            lines1 = invoice.invoice_line.create_avalara_lines(
                config, sign=sign)
            lines2 = invoice.shipping_lines.create_avalara_lines(sign=sign)
            document_type = (
                'ReturnInvoice'
                if invoice.type == 'out_refund' else 'SalesInvoice')
            self.env['account.tax']._get_compute_tax(
                config, invoice.date_invoice, invoice.internal_number,
                document_type, invoice.partner_id, shipping_add_origin,
                partner, lines1 + lines2, user=invoice.user_id,
                exemption_number=invoice.exemption_code,
                exemption_code_name=invoice.exemption_code_id.code,
                commit=True, invoice_date=tax_date,
                reference_code=invoice.invoice_doc_no,
                location_code=invoice.location_code)
        return res

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id)
        res.update({
            'shipping_lines': self._refund_cleanup_lines(
                invoice.shipping_lines),
            'invoice_doc_no': invoice.internal_number,
            'invoice_date': invoice.date_invoice,
        })
        return res

    @api.multi
    def check_tax_lines(self, compute_taxes):
        """ Called before creating move lines. We don't actually check existing
        tax lines, but we force-recreate them if AvaTax applies. """
        self.ensure_one()
        config, partner = self.test_avalara()
        if not config:
            return super(AccountInvoice, self).check_tax_lines(compute_taxes)
        self.button_reset_taxes()
