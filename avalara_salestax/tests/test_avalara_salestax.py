# coding: utf-8
from openerp.fields import Date
from .common import AvalaraTestSetUp


class TestAvalaraSalestax(AvalaraTestSetUp):
    def setUp(self):
        super(TestAvalaraSalestax, self).setUp()
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.config.company_id.id)], limit=1)
        warehouse.partner_id = self.config.company_id.partner_id
        pricelist = self.customer.property_product_pricelist
        pricelist.currency_id = self.env.ref('base.USD')
        self.order = self.env['sale.order'].create({
            'date_order': Date.context_today(self.env.user),
            'order_policy': 'manual',
            'partner_id': self.customer.id,
            'partner_invoice_id': self.customer.id,
            'partner_shipping_id': self.customer.id,
            'pricelist_id': pricelist.id,
            'user_id': self.env.user.id,
            'warehouse_id': warehouse.id,
        })
        self.product = self.env.ref('product.product_product_18')
        self.order_line = self.env['sale.order.line'].create({
            'name': self.product.name,
            'order_id': self.order.id,
            'price_unit': 50,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 2,
            'product_uos_qty': 2,
        })

    def test_01_sales_order(self):
        """ A tax amount is computed for a sales order that is delivered in
        the same state """
        self.assertFalse(self.order.tax_amount)
        self.order.button_dummy()
        self.assertTrue(self.order.tax_amount > 0)

    @staticmethod
    def _partner_to_vals(partner):
        """ Return a list of parameters suitable to pass to
        avalara.onthefly::address_to_latlong() """
        return [
            partner.street,
            partner.street2,
            partner.city,
            partner.zip,
            partner.state_id.code,
            partner.country_id.code,
        ]

    def test_02_on_the_fly(self):
        """ On the fly tax amount is equal to requesting order amount """
        self.order.button_dummy()
        order_amount = self.order.tax_amount
        origin = self.env['avalara.onthefly'].address_to_latlong(
            *self._partner_to_vals(self.order.warehouse_id.partner_id))
        destination = self.env['avalara.onthefly'].address_to_latlong(
            *self._partner_to_vals(self.order.partner_shipping_id))
        lines = [(self.product, 2, 50)]
        onthefly_amount = self.env['avalara.onthefly'].get_tax(
            origin[0], origin[1], destination[0], destination[1], lines)
        self.assertTrue(
            self.company.currency_id.is_zero(order_amount - onthefly_amount))
