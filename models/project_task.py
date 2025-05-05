from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    cancel_reason = fields.Text(string='Cancel Reason', readonly=True)
    reject_reason = fields.Text(string='Reject Reason', readonly=True)

    #==================== Action Methods ====================
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

    def action_open_reject_wizard(self):
        """Open wizard to select reject reason"""
        self.ensure_one()
        return {
            'name': 'Reject Task',
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            }
        }

    #==================== Onchange Methods ====================
    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'canceled':
            self.cancel_reason = 'Cancelled'
        else:
            self.cancel_reason = False
