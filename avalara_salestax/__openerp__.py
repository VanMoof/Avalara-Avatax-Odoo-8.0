# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2010 Odoo SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Avalara Avatax connector for sales tax calculation",
    "version" : "8.1.0",
    "author" : 'Kranbery Technologies',
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
    "depends" : [ 'base','sale','account','account_accountant','stock','sale_stock'],
    "data" : [
    "wizard/avalara_salestax_ping_view.xml",
    "wizard/avalara_salestax_address_validate_view.xml",
    "avalara_salestax_view.xml",
    "avalara_salestax_data.xml",
    "partner_view.xml",
    "product_view.xml",
    "account_invoice_workflow.xml",
    "account_invoice_view.xml",
    "sale_order_view.xml",
    "warning_view.xml",
    "security/avalara_salestax_security.xml",
    "security/ir.model.access.csv",
    ],
    "images" : [
        "images/main_screenshot.png",   
        "images/kranbery_logo.png",     
                
    ],
    'demo': [
        'demo.xml',
    ],    
    "test" : [],
    'installable': True,
    'auto_install': False,
    'application': True,
   

    
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
