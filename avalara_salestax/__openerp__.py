# -*- coding: utf-8 -*-
# © 2015 Kranbery Technologies
# © 2018 Opener B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name" : "Avalara Avatax connector for sales tax calculation",
    "version" : '8.0.1.1.0',
    "author" : 'Kranbery Technologies, Opener B.V.',
    'summary': 'Sales tax is hard. We make it easy.',
    "description": """ 
    
The Avatax module automates the complex task of sales tax calculation with ease.  Sale tax calculations are based on prevalidated shop, warehouse and customer address.  This app plugs into your current installation of odoo with minimal configuration and just works.  Your sales orders, invoices and refunds activity is automatically calculated from Avalara's calc service returning the proper sales tax and places the tax into the order/invoice seamlessly.  
 
This module has Following Features:

1. Customer and Company Address Validation
2. Line or Total Order amount sale tax calculation 
3. Handling of Customer Refunds
4. Customer Exemption handling
5. Calculation of Shipping Cost tax
6. Use both Avalara and Odoo Taxes etc
7. International support
8. Discount management
9. Reporting record through an avalara management console to verify transactions
10. Documentation included


Download module and call Avalara toll free at 877-780-4848 to get started!

http://kranbery.com/avatax-openerp-module/

http://www.avalara.com/


Note: We always recommend testing the module before deploying to a production environment


""",
    "category" : "Generic Modules/Accounting",
    "website" : "http://kranbery.com/avatax-openerp-module/",
    "depends" : [
        'sale_stock',
    ],
    "data" : [
        'data/avalara_salestax_data.xml',
        'security/res_groups.xml',
        'views/menu.xml',  # must come first
        'views/account_invoice.xml',
        # ping action is refered to from avalara_salestax.xml
        'views/avalara_salestax_ping.xml',
        'views/avalara_salestax.xml',
        'views/avalara_salestax_address_validate.xml',
        'views/exemption_code.xml',
        'views/shipping_rate_config.xml',
        'views/product_category.xml',
        'views/product_tax_code.xml',
        'views/product_template.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        "security/avalara_salestax_security.xml",
        "security/ir.model.access.csv",
    ],
    "images" : [
        "images/main_screenshot.png",   
        "images/kranbery_logo.png",     
    ],
    'installable': True,
}
