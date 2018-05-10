# coding: utf-8
# Taken from https://github.com/fhe-odoo/avatax_connector
from openerp import fields, models


class ProductTaxCode(models.Model):
    """ Define type of tax code """
    _name = 'product.tax.code'
    _description = 'Avalara Tax Code'

    name = fields.Char('Code', required=True)
    description = fields.Char('Description')
    type = fields.Selection(
        [('product', 'Product'), ('freight', 'Freight'),
         ('service', 'Service'), ('digital', 'Digital'),
         ('other', 'Other')], 'Type',
        required=True, help="Type of tax code as defined in AvaTax")
