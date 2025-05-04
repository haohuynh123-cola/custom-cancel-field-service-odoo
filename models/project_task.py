from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    cancel_reason = fields.Text(string='Cancel Reason', readonly=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('inprocess', 'Inprocess'),
        ('review', 'Review'),
        ('rejected', 'Rejected'),
        ('canceled', 'Cancel'),
    ], string='State', copy=False, default='open', required=True, tracking=True)

    def action_open_cancel_wizard(self):
        """Open wizard to select cancel reason"""
        self.ensure_one()
        return {
            'name': 'Cancel Task',
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            }
        }

    def action_assign(self):
        """Set task to assigned state"""
        self.write({'state': 'assigned'})

    def action_start(self):
        """Set task to inprocess state"""
        self.write({'state': 'inprocess'})

    def action_review(self):
        """Set task to review state"""
        self.write({'state': 'review'})

    def action_reject(self):
        """Set task to rejected state"""
        self.write({'state': 'rejected'})

    def action_reopen(self):
        """Set task back to open state"""
        self.write({'state': 'open'})

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'canceled':
            self.cancel_reason = 'Cancelled'
        else:
            self.cancel_reason = False

