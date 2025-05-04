from odoo import models, fields, api
from datetime import datetime

class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Wizard select reject reason'

    task_id = fields.Many2one('project.task', string='Task', required=True)
    reason = fields.Text(string='Reject Reason', required=True)

    def action_confirm(self):
        """Confirm reject and update status"""
        self.ensure_one()

        # Pause time if running
        timer = self.env['timer.timer'].search([
            ('res_model', '=', 'project.task'),
            ('res_id', '=', self.task_id.id),
            ('timer_start', '!=', False),
            ('timer_pause', '=', False)
        ], limit=1)

        if timer:
            timer.write({
                'timer_pause': fields.Datetime.now()
            })

        self.task_id.write({
            'state': 'rejected',
            'reject_reason': self.reason,
        })

        return {'type': 'ir.actions.act_window_close'}