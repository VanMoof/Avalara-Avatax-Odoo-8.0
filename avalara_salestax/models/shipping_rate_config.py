# coding: utf-8
from openerp import fields, models
from openerp.addons import decimal_precision as dp


class ShippingRateConfig(models.Model):
    """ Shipping Rate Configuration with shipping cost, Shipping method and
    also shipping account. TODO: make multicompany aware. """
    _name = 'shipping.rate.config'
    _description = "Configuration for shipping rate"
    name = fields.Char(
        'Shipping Method Name',
        help='Shipping method name. Displayed in the wizard.')
    active = fields.Boolean(default=True)
    shipping_cost = fields.Float(
        'Shipping Cost', digits=dp.get_precision('Account'))
    account_id = fields.Many2one(
        'account.account', 'Account', domain=[('type', '!=', 'view')],
        help='This account represents the g/l account for shipping revenue')
