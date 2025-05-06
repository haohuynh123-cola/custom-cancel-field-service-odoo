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
    score = fields.Float(string='Score', default=0, tracking=True)
    start_date = fields.Datetime(string='Start Date', tracking=True)
    is_urgent = fields.Boolean(string='Is Urgent', default=False, tracking=True)
    account_id = fields.Text(string='Account ID', tracking=True)
    finish_time = fields.Datetime(string='Finish Time', tracking=True)

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
        res = super(ProjectTask, self).write(vals)
        if 'state' in vals or 'date_deadline' in vals or 'user_ids' in vals:
            self._compute_status_code()
        return res


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

    def action_assign(self):
        """Set task to assigned state"""
        self.write({'state': 'assigned'})
        self._compute_status_code()

    def action_start(self):
        """Set task to inprocess state
            Update planned_date_begin to current date when planned_date_begin is null
        """
        if not self.planned_date_begin:
            self.planned_date_begin = fields.Datetime.now()
        self.write({'state': 'in_progress'})
        self._compute_status_code()

    def action_review(self):
        """Set task to review state"""
        self.write({'state': 'review', 'finish_time': fields.Datetime.now()})
        self._compute_status_code()

    def action_reject(self):
        """Set task to rejected state"""
        self.write({'state': 'rejected'})
        self._compute_status_code()

    def action_reopen(self):
        """Set task back to assigned state"""
        self.write({'state': 'open'})
        self._compute_status_code()

    def action_done(self):
        """Override native action_done to handle Mark as done button"""
        self.write({'state': 'done'})
        self._compute_status_code()
        return True

    def action_approve(self):
        """Approve task and set to done"""
        self.write({'state': 'done'})
        self._compute_status_code()
        return True

    def action_cancel(self):
        """Set task to canceled state"""
        self.write({'state': 'canceled'})
        self._compute_status_code()

    #==================== Onchange Methods ====================
    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'canceled':
            self.cancel_reason = 'Cancelled'
        else:
            self.cancel_reason = False
        # Cập nhật status_code khi state thay đổi
        self._compute_status_code()

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        """
        Set task to assigned state if user_ids is not empty when state is open
        """
        if self.state == 'open' and self.user_ids:
            self.state = 'assigned'

    @api.depends('state', 'date_deadline', 'user_ids')
    def _compute_status_code(self):
        """Cập nhật status_code dựa trên quy tắc:
        - N00 - Chưa nhận, chưa trễ hạn
        - N10 - Đã nhận, chưa trễ hạn, chưa hoàn thành
        - N11 - Đã nhận và hoàn thành đúng hạn
        - L00 - Chưa nhận, đã trễ hạn
        - L10 - Đã nhận, đã trễ hạn và chưa hoàn thành
        - L11 - Đã nhận, đã hoàn thành và đã trễ hạn
        """
        for task in self:
            # Kiểm tra trễ hạn
            is_late = False
            if task.date_deadline:
                today = fields.Date.today()
                deadline_date = fields.Date.from_string(task.date_deadline)
                is_late = today > deadline_date

            # Kiểm tra đã nhận task chưa
            is_assigned = bool(task.user_ids) or task.state not in ['open', 'canceled']

            # Kiểm tra đã hoàn thành chưa
            is_done = task.state in ['done', 'rejected'] or task.state == 'review' and not is_late

            # Xác định status_code
            prefix = "L" if is_late else "N"
            middle = "1" if is_assigned else "0"
            suffix = "1" if is_done else "0"

            task.status_code = f"{prefix}{middle}{suffix}"

