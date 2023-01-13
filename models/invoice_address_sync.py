from __future__ import print_function

from odoo import models, api
import logging
import traceback
import time
_logger = logging.getLogger(__name__)


class MyOpLeadsSync(models.TransientModel):
    _name = 'cron.invoice.address.sync'

    @api.model
    def invoice_address_sync(self):
        customer_branches = self.env['res.partner'].sudo().search([('is_customer_branch', '=', True)])

        for customer_branch in customer_branches:
            try:
                time.sleep(3)
                customer_branch.sync_customer_details_from_mastersindia()
                _logger.info("evt=INVOICE_ADDRESS_SYNC res_partner_id="+str(customer_branch.id)+" msg=Updated Invoice addresses.")
            except KeyError as keyError:
                _logger.error("evt=INVOICE_ADDRESS_SYNC res_partner_id=" + str(customer_branch.id) + " msg=Key does not exist:" + str(keyError),
                              traceback.format_exc())
            except Exception as e:
                _logger.error("evt=INVOICE_ADDRESS_SYNC res_partner_id="+str(customer_branch.id)+" msg="+str(e), traceback.format_exc())
