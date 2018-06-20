# coding: utf-8
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    exemption_code = fields.Char('Avalara Exemption Number', readonly=True)
    is_add_validate = fields.Boolean(
        'Address is Avalara-validated', readonly=True)
    exemption_code_id = fields.Many2one(
        'exemption.code', 'Avalara Exemption Code', readonly=True)
    shipping_lines = fields.One2many(
        'shipping.order.line', 'sale_ship_id', 'AvaTax Shipping Lines',
        readonly=True, states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)]})
    amount_shipping = fields.Float(
        'Avalara shipping cost',
        compute='_compute_amount_shipping',
        digits=dp.get_precision('Sale Price'),
        store=True)
    tax_amount = fields.Float(
        'Avalara tax amount', digits=dp.get_precision('Sale Price'))
    tax_add_default = fields.Boolean(
        'Use default address', readonly=True,
        states={'draft': [('readonly', False)]})
    tax_add_invoice = fields.Boolean(
        'Use invoice address', readonly=True,
        states={'draft': [('readonly', False)]})
    tax_add_shipping = fields.Boolean(
        'Use delivery address', default=True,
        readonly=True, states={'draft': [('readonly', False)]})
    tax_address = fields.Text('Tax Address', readonly=True)
    location_code = fields.Char(
        'Origin address', readonly=True, help='Origin address location code')

    @api.multi
    @api.depends('shipping_lines', 'shipping_lines.shipping_cost')
    def _compute_amount_shipping(self):
        for order in self:
            self.amount_shipping = order.pricelist_id.currency_id.round(
                sum(line.shipping_cost for line in self.shipping_lines))

    @api.model
    def _prepare_invoice(self, order, lines):
        """ Override method to add shipping lines in invoice.
        @param lines: Shipping lines with ship method, code and amount and
        after it will return shipping tax amount using shipping code
        """
        res = super(SaleOrder, self)._prepare_invoice(order, lines)
        ship_data = []
        for ship_line in order.shipping_lines:
            ship_data.append((0, 0, {
                'ship_method_id': ship_line.ship_method_id.id,
                'shipping_cost': ship_line.shipping_cost,
                'ship_code_id': ship_line.ship_code_id.id,
                'sale_account_id': ship_line.sale_account_id.id,
                'tax_amt': ship_line.tax_amt,
            }))
        res.update({
            'shipping_lines': ship_data or False,
            'exemption_code': order.exemption_code or '',
            'exemption_code_id': order.exemption_code_id.id,
            'shipping_amt': order.amount_shipping,
            'shipping_address': order.tax_address,
            'location_code': order.warehouse_id.code or '',
        })
        return res

    @api.multi
    def get_tax_values_from_partner(self, partner):
        self.ensure_one()
        if partner.tax_exempt:
            self.exemption_code = partner.exemption_number
            self.exemption_code_id = partner.exemption_code_id
        self.tax_address = partner.format_tax_address()
        self.is_add_validate = bool(partner.validation_method)

    @api.multi
    def get_tax_partner(self):
        self.ensure_one()
        if self.tax_add_default:
            return self.partner_id
        if self.tax_add_invoice:
            return self.partner_invoice_id
        return self.partner_shipping_id

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if not res.tax_address:
            partner = res.get_tax_partner()
            res.get_tax_values_from_partner(partner)
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('tax_add_default'):
            for sale in self:
                sale.get_tax_values_from_partner(self.partner_id)
        elif vals.get('tax_add_invoice'):
            for sale in self:
                sale.get_tax_values_from_partner(self.partner_invoice_id)
        elif vals.get('tax_add_shipping'):
            for sale in self:
                sale.get_tax_values_from_partner(self.partner_shipping_id)
        else:
            if vals.get('partner_id'):
                for sale in self.filtered('tax_add_default'):
                    sale.get_tax_values_from_partner(self.partner_id)
            elif vals.get('partner_invoice_id'):
                for sale in self.filtered('tax_add_invoice'):
                    sale.get_tax_values_from_partner(self.partner_invoice_id)
            elif vals.get('partner_shipping_id'):
                for sale in self.filtered('tax_add_shipping'):
                    sale.get_tax_values_from_partner(self.partner_shipping_id)
        return res

    @api.model
    def _amount_line_tax(self, line):
        """ Include AvaTax in line tax amount """
        return super(SaleOrder, self)._amount_line_tax(line) + line.tax_amt

    @api.multi
    def _amount_all(self, field_name, arg):
        res = super(SaleOrder, self)._amount_all(field_name, arg)
        for order in self:
            res[order.id]['amount_total'] += order.amount_shipping
            # Add tax amount in case of order level computation
            if order.tax_amount and all(
                    not line.tax_amt for line in order.order_line):
                res[order.id]['amount_tax'] += order.tax_amount
                res[order.id]['amount_total'] += order.tax_amount
        return res

    @api.multi
    def button_dummy(self):
        # In this module, tax is not automatically updated using stored
        # computed fields, so when 'update taxes' is clicked in the UI,
        # actually update the tax calculation
        self.compute_tax()
        return super(SaleOrder, self).button_dummy()

    @api.multi
    def test_avalara(self):
        self.ensure_one()
        config = self.env['avalara.salestax'].with_context(
            force_company=self.company_id.id)._get_avatax_config_company()
        if not config or config.disable_tax_calculation:
            return False, False
        partner = self.get_tax_partner()
        if partner.country_id not in config.country_ids:
            return False, False
        return config, partner

    @api.multi
    def compute_tax(self):
        """ Recompute the Avalara tax amount for order and shipping lines """
        self.ensure_one()
        config, partner = self.test_avalara()
        if not config:
            self.order_line.filtered(
                lambda l: l.tax_amt).write({'tax_amt': 0.0})
            self.shipping_lines.filtered(
                lambda l: l.tax_amt).write({'tax_amt': 0.0})
            if self.tax_amount:
                self.tax_amount = 0
            # Force total recompute
            self.order_line[0].write(
                {'price_unit': self.order_line[0].price_unit})
            return
        if not self.warehouse_id.partner_id:
            ship_from_address = self.company_id.partner_id
        else:
            ship_from_address = self.warehouse_id.partner_id

        if config.address_validation and not partner.date_validation:
            if not config.validation_on_save:
                raise UserError(
                    'Address not avalara-validated: customer %s on order %s' %
                    (partner.name, self.name))
            partner.multi_address_validation()

        lines1 = self.order_line.create_avalara_lines()
        lines2 = self.shipping_lines.create_avalara_lines()

        tax_amount = 0
        if config.on_line:
            # Line level tax calculation
            # tax based on individual order line
            for line1, o_line in zip(lines1, self.order_line):
                o_line.tax_amt = self.env['account.tax']._get_compute_tax(
                    config, self.date_confirm or self.date_order,
                    self.name, 'SalesOrder', self.partner_id,
                    ship_from_address, partner, [line1], self.user_id,
                    self.exemption_code,
                    self.exemption_code_id.code).TotalTax
                tax_amount += o_line.tax_amt

            # tax based on individual shipping order line
            for line2, s_line in zip(lines2, self.shipping_lines):
                s_line.tax_amt = self.env['account.tax']._get_compute_tax(
                    config, self.date_confirm or self.date_order,
                    self.name, 'SalesOrder', self.partner_id,
                    ship_from_address, partner, [line2],
                    self.user_id, self.exemption_code,
                    self.exemption_code_id.code).TotalTax
                tax_amount += s_line.tax_amt

        else:
            # Order level tax calculation
            tax_amount = self.env['account.tax']._get_compute_tax(
                config, self.date_confirm or self.date_order,
                self.name, 'SalesOrder', self.partner_id,
                ship_from_address, partner, lines1 + lines2, self.user_id,
                self.exemption_code,
                self.exemption_code_id.code).TotalTax

            self.order_line.write({'tax_amt': 0.0})
            self.shipping_lines.write({'tax_amt': 0.0})

        self.tax_amount = tax_amount

        if self.order_line:
            # Force total recompute
            self.order_line[0].write(
                {'price_unit': self.order_line[0].price_unit})

    @api.multi
    def action_wait(self):
        res = super(SaleOrder, self).action_wait()
        for order in self:
            order.compute_tax()
        return res
