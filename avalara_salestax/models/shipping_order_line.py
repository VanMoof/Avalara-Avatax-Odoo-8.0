# coding: utf-8
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class ShippingOrderLine(models.Model):
    """ Create shipping order line class and perform all operation same as
    sale order line """
    _name = 'shipping.order.line'
    _description = 'Shipping Order lines'

    @api.model
    def get_default_ship_code(self):
        """ Get or create a tax code of type 'freight' """
        return self.env['product.tax.code'].search(
            [('type', '=', 'freight')],
            limit=1) or self.env['product.tax.code'].create({
                'name': 'FR',
                'description': 'Default Shipping Code',
                'type': 'freight',
            })

    @api.onchange('ship_method_id')
    def onchange_ship_method_id(self):
        self.name = self.ship_method_id.name
        self.shipping_cost = self.ship_method_id.shipping_cost
        self.sale_account_id = self.ship_method_id.account_id

    name = fields.Char(
        'Shipping Method',
        help='Shipping method name. Displayed in the wizard.')
    ship_method_id = fields.Many2one(
        'shipping.rate.config', 'Ship By', required=True)
    shipping_cost = fields.Float(
        'Shipping Cost', digits=dp.get_precision('Account'))
    ship_code_id = fields.Many2one(
        'product.tax.code', 'Ship Code', required=True,
        domain=[('type', '=', 'freight')], default=get_default_ship_code,
        help='Shipping tax code')
    sale_account_id = fields.Many2one(
        'account.account', 'Shipping Account',
        help='This account represents the g/l account for shipping revenue.')
    tax_amt = fields.Float(
        'Avalara Tax', help='Tax amount based on shipping cost',
        digits=dp.get_precision('Account'))
    sale_ship_id = fields.Many2one(
        'sale.order', 'Sale Ship ID', readonly=True, required=True)
    invoice_ship_id = fields.Many2one(
        'account.invoice', 'Invoice', readonly=True)

    @api.multi
    def create_avalara_lines(self, sign=1):
        """ Shipping line creation for calculating ship tax amount using Avalara
        shipping codes """
        return [{
            'qty': 1,
            'itemcode': 'Ship/Freight',
            'description': 'Ship/Freight',
            'amount': sign * line.shipping_cost,
            'tax_code': line.ship_code_id.name,
        } for line in self]
