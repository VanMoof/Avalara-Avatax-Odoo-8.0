# coding: utf-8
from openerp import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    tax_code_id = fields.Many2one(
        'product.tax.code', 'Avalara Tax Code',
        help=('This setting can be overridden by setting a tax code on the'
              'product itself'))
