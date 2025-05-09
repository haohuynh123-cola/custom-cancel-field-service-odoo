# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean(
        string="Sales Order Approval",
        help="Requires approval for sales orders before they can be confirmed.",
        config_parameter='sale.order.approval'
    )

    so_double_validation_limit = fields.Integer(
        string="Sales Order Double Validation Limit",
        help="Number of times a sales order can be validated by different users.",
        config_parameter='sale.order.double.validation.limit'
    )
