# coding: utf-8
from openerp import api, fields, models


class AvalaraSalestax(models.Model):
    _name = 'avalara.salestax'
    _description = 'AvaTax Configuration'
    _rec_name = 'account_number'

    @api.model
    def _get_avatax_config_company(self, company=None):
        """ Returns the AvaTax configuration for the user company """
        if company is None:
            if self.env.context.get(
                    'company_id') or self.env.context.get('force_company'):
                company = self.env['res.company'].browse(
                    self.env.context.get(
                        'company_id') or self.env.context['force_company'])
            else:
                company = self.env.user.company_id
        return self.search([('company_id', '=', company.id)], limit=1)

    @api.onchange('address_validation')
    def onchange_address_validation(self):
        if self.address_validation:
            self.validation_on_save = False
            self.result_in_uppercase = False

    @api.onchange('on_order')
    def onchange_on_order(self):
        if self.on_order and self.on_line:
            self.on_line = False

    @api.onchange('on_line')
    def onchange_on_line(self):
        if self.on_line and self.on_order:
            self.on_order = False

    @api.onchange('disable_tax_calculation')
    def onchange_disable_tax_calculation(self):
        if self.disable_tax_calculation and not self.disable_tax_reporting:
            self.disable_tax_reporting = True

    @api.onchange('disable_tax_reporting')
    def onchange_disable_tax_reporting(self):
        if self.disable_tax_calculation and not self.disable_tax_reporting:
            self.disable_tax_calculation = False

    @api.model
    def _get_avatax_supported_countries(self):
        """ Returns the countries supported by AvaTax Address Validation
        Service."""
        return self.env['res.country'].search([('code', 'in', ['US', 'CA'])])

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    account_number = fields.Char(
        size=64, required=True, help="Account Number provided by AvaTax")
    license_key = fields.Char(
        size=64, required=True, help="License Key provided by AvaTax")
    service_url = fields.Char(
        'Service URL', required=True, help="The url to connect with")
    date_expiration = fields.Date(
        'Service Expiration Date', readonly=True,
        help="The expiration date of the service")
    request_timeout = fields.Integer(
        help=('Defines AvaTax request time out length, AvaTax best practices '
              'prescribes default setting of 300 seconds'), default=300)
    company_code = fields.Char(
        required=True,
        help="The company code as defined in the Admin Console of AvaTax")
    logging = fields.Boolean(
        'Enable Logging',
        help="Enables detailed AvaTax transaction logging within application")
    address_validation = fields.Boolean(
        'Attempt automatic address validation', default=True,
        help="Uncheck to disable address validation")
    result_in_uppercase = fields.Boolean(
        'Return validation results in upper case',
        help="Check is address validation results desired to be in upper case")
    validation_on_save = fields.Boolean(
        'Force validate on save for customer profile',
        help="Validates customer address upon creation and modification")
    auto_generate_customer_code = fields.Boolean(
        'Automatically generate customer code', default=True,
        help=('This will generate customer code for customers in the system '
              'who do not have codes already created. Each code is unique per '
              'customer. When this is disabled, you will have to manually go '
              'to each customer and manually generate their customer code. '
              'This is required for Avatax and is only generated one time.'))
    disable_tax_calculation = fields.Boolean(
        'Disable AvaTax calculation',
        help="Check to disable avalara tax calculation and reporting")
    disable_tax_reporting = fields.Boolean(
        'Disable AvaTax reporting',
        help=('Check to disable avalara tax reporting to Avatax Service. You '
              'will not see the transactions on the Avalara transaction web '
              'portal.'))
    default_shipping_code_id = fields.Many2one(
        'product.tax.code', 'Default Shipping Code',
        help="The default shipping code which will be passed to Avalara")
    country_ids = fields.Many2many(
        'res.country', 'avalara_salestax_country_rel', 'avalara_salestax_id',
        'country_id', 'Countries',
        default=_get_avatax_supported_countries,
        help="Countries where address validation will be used")
    active = fields.Boolean(
        default=True, help="Uncheck the active field to hide the record")
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default='_get_default_company',
        help="Company which has subscribed to the AvaTax service")
    on_line = fields.Boolean(
        'Line-level', help="It will calculate tax line by line and also show.")
    on_order = fields.Boolean(
        'Order-level', default=True,
        help="It will calculate tax for order not line by line.")
    upc_enable = fields.Boolean(
        'Enable UPC Taxability',
        help=('Allows ean13 to be reported in place of Item Reference as UPC '
              'identifier.'))

    _sql_constraints = [
        ('code_company_uniq', 'unique (company_code)',
         'Avalara setting is already available for this company code'),
        ('account_number_company_uniq', 'unique (account_number, company_id)',
         'The account number must be unique per company!'),
    ]
