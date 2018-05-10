# coding: utf-8
from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tax_code_id = fields.Many2one(
        'product.tax.code', 'Avalara Tax Code',
        help='When left empty, the tax code of the product category is used')
