# coding: utf-8
from testfixtures import LogCapture
from openerp.addons.avalara_salestax.tests.test_invoice_validation import (
    TestInvoiceValidationSetUp)
from openerp.addons.connector.queue.job import OpenERPJobStorage
from openerp.addons.connector.session import ConnectorSession


class TestInvoiceValidationJob(TestInvoiceValidationSetUp):
    def _run_connector_job(self, job):
        session = ConnectorSession.from_env(self.env)
        job_object = OpenERPJobStorage(session).load(job.uuid)
        return job_object.perform(session)

    def test_01_invoice_validation_job(self):
        """ Avalara computation is deferred to queued job """
        max_job_id = self.env['queue.job'].search(
            [], order='id desc', limit=1).id or 0

        with LogCapture(
                'openerp.addons.avalara_salestax.avalara_api') as capture:
            self.invoice.signal_workflow('invoice_open')
        self.assertNotIn('Committing',
                         ''.join(record.msg for record in capture.records))

        job = self.env['queue.job'].search([
            ('id', '>', max_job_id),
            ('func_string', 'like', '%%avalara_commit(%s)' % self.invoice.id)
        ])
        self.assertTrue(job)

        with LogCapture(
                'openerp.addons.avalara_salestax.avalara_api') as capture:
            self._run_connector_job(job)
        self.assertIn('Committing',
                      ''.join(record.msg for record in capture.records))
