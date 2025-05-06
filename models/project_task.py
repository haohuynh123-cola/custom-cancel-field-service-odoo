from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    cancel_reason = fields.Text(string='Cancel Reason', readonly=True)
    reject_reason = fields.Text(string='Reject Reason', readonly=True)
    status_code = fields.Selection([
        ('N00', 'N00'),
        ('N10', 'N10'),
        ('N11', 'N11'),
        ('L00', 'L00'),
        ('L10', 'L10'),
        ('L11', 'L11'),
    ], string='Status Code', default='N00', tracking=True)

    # Các trường mới từ Google Sheet
    score = fields.Float(string='Score', default=0)
    start_date = fields.Datetime(string='Start Date')
    is_urgent = fields.Boolean(string='Is Urgent', default=False)
    account_id = fields.Text(string='Account ID')

    state = fields.Selection([
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('canceled', 'Canceled'),
    ], string='State', copy=False, default='open', required=True, tracking=True)

    # Override write method
    def write(self, vals):
        """
        Save all vals check exist user_ids change to assigned state
        """
        #check vals log
        if 'user_ids' in vals:
            vals['state'] = 'assigned'
        return super(ProjectTask, self).write(vals)


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

    def action_start(self):
        """Set task to inprocess state
            Update panned_start_date to current date
        """
        self.panned_start_date = fields.Datetime.now()
        self.write({'state': 'in_progress'})


    def action_review(self):
        """Set task to review state"""
        self.write({'state': 'review'})

    def action_reject(self):
        """Set task to rejected state"""
        self.write({'state': 'rejected'})

    def action_done(self):
        """Set task to done state"""
        self.write({'state': 'done'})

    def action_cancel(self):
        """Set task to canceled state"""
        self.write({'state': 'canceled'})

    def action_reopen(self):
        """Set task to assigned state"""
        self.write({'state': 'assigned'})

    def action_approve(self):
        """Set task to done state"""
        self.write({'state': 'done'})

    #==================== Onchange Methods ====================
    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'canceled':
            self.cancel_reason = 'Cancelled'
        else:
            self.cancel_reason = False

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        if self.user_ids:
            self.state = 'assigned'
        else:
            self.state = 'open'
