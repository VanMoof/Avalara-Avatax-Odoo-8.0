# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
from openerp.osv import osv

class sale_order(osv.osv):
    _inherit = "sale.order"
    

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
        """Override method to add new fields values.
        @param part- update vals location code which is the abbreviation of warehouse abbreviation
        """        
        res = super(sale_order, self).onchange_warehouse_id(cr, uid, ids, warehouse_id, context=context)        
        val = res
        if warehouse_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
            if warehouse.code:
                val['location_code'] = warehouse.code

        return {'value': val} 
    
    
sale_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
