# coding: utf-8
from openerp import api, fields, models


class ExemptionCode(models.Model):
    _name = 'exemption.code'
    _description = 'Avalara exemption code'
    name = fields.Char(required=True)
    code = fields.Char()

    @api.multi
    def name_get(self):
        return [
            (code.id,
             '%s%s' % (
                 code.name,
                 ' (%s)' % code.code if code.code else ''))
            for code in self]
