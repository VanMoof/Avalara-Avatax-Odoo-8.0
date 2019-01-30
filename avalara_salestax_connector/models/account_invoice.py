# coding: utf-8
# © 2018 Opener B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession


@job
def job_avalara_commit(session, invoice_id):
    session.env['account.invoice'].with_context(
        job_avalara_commit=True).browse(invoice_id).avalara_commit()


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def avalara_commit(self):
        self.ensure_one()
        if not self.env.context.get('job_avalara_commit'):
            session = ConnectorSession.from_env(self.env)
            return job_avalara_commit.delay(session, self.id)
        return super(AccountInvoice, self).avalara_commit()
