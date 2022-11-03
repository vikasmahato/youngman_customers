# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError

import logging


_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    in_beta = fields.Boolean(default=False, string="Add Customer To Beta")

    # def write(self, vals):
    #     if self.team_id.user_id.id == self._uid:
    #         return super(CrmLead, self).write(vals)
    #
    #     if self.lead_qual:
    #         if (self._uid != self.user_id.id) and self.type == 'lead':
    #             raise ValidationError(_('You cant change Salesperson unless you are assigned to it!'))
    #         elif (self.lead_qual.lower() not in self.user_id.name.lower()) and self.type == 'lead':
    #             raise ValidationError(_('You cant change Salesperson unless you are assigned as LQ to it!'))
    #     return super(CrmLead, self).write(vals)

