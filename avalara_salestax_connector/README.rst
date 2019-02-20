Avalara Salestax Job Queue Integration
======================================

When salestax is committed (at the time of the validation of the invoice),
delegate the Avalara communication to an asynchronous job so that this
communication only takes place when the transaction in Odoo is committed.

This prevents inconsistencies between Odoo and Avalara when transactions
are rolled back in Odoo.
