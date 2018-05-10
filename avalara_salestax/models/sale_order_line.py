# coding: utf-8
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tax_amt = fields.Float(
        'Avalara Tax', digits=dp.get_precision('Account'),
        help='Tax calculated by Avalara')

    @api.multi
    def create_avalara_lines(self):
        res = []
        for line in self:
            tax_code = (line.product_id.tax_code_id or
                        line.product_id.categ_id.tax_code_id).name or None

            res.append({
                'qty': line.product_uom_qty,
                'itemcode': line.product_id.default_code or None,
                'description': line.name or None,
                'amount': line.product_uom_qty * (
                    line.price_unit * (1 - (line.discount or 0.0)/100.0)),
                'tax_code': tax_code or None,
            })
        return res
