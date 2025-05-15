from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

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

    # Mapping trạng thái theo tên
    STAGE_MAPPING = {
        'OPEN':  {'id': 14, 'name': 'OPEN', 'code': 'OPEN'},
        'ASSIGNED':  {'id': 15, 'name': 'ASSIGNED', 'code': 'ASSIGNED'},
        'IN-PROGRESS':  {'id': 16, 'name': 'IN-PROGRESS', 'code': 'IN-PROGRESS'},
        'COMPLETED':  {'id': 17, 'name': 'COMPLETED', 'code': 'COMPLETED'},
        'CANCELED':  {'id': 18, 'name': 'CANCELED', 'code': 'CANCELED'},
        'REJECTED':  {'id': 26, 'name': 'REJECTED', 'code': 'REJECTED'},
        'REVIEW':  {'id': 48, 'name': 'REVIEW', 'code': 'REVIEW'},
    }

    stage_code = fields.Char(compute='_compute_stage_code', store=True)

    # Thêm trường tính toán để lọc user theo project
    available_user_ids = fields.Many2many('res.users', compute='_compute_available_users', store=False)

    @api.depends('stage_id')
    def _compute_stage_code(self):
        for rec in self:
            # Tìm key tương ứng với stage_id.id
            for key, value_dict in self.__class__.STAGE_MAPPING.items():
                if value_dict['id'] == rec.stage_id.id:
                    rec.stage_code = value_dict['code']
                    break
            else:
                rec.stage_code = ''

    # state = fields.Selection([
    #     ('open', 'Open'),
    #     ('assigned', 'Assigned'),
    #     ('in_progress', 'In Progress'),
    #     ('01_in_progress', '01 In Progress'),
    #     ('review', 'Review'),
    #     ('rejected', 'Rejected'),
    #     ('done', 'Done'),
    #     ('canceled', 'Canceled'),
    # ], string='State', copy=False, default='open', required=True, tracking=True)

    # Override write method
    # def write(self, vals):
    #     """
    #     Save all vals check exist user_ids change to assigned state
    #     """
    #     #check vals log
    #     if 'user_ids' in vals:
    #         vals['state'] = 'assigned'
    #     res = super(ProjectTask, self).write(vals)
    #     if 'state' in vals or 'date_deadline' in vals or 'user_ids' in vals:
    #         self._compute_status_code()
    #     return res


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
        self.write({'stage_id': self.STAGE_MAPPING['ASSIGNED']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['ASSIGNED']['code']})
        self._compute_status_code()

    def action_start(self):
        """Set task to in process state
            Update planned_date_begin to current date when planned_date_begin is null
        """
        if not self.planned_date_begin:
            self.planned_date_begin = fields.Datetime.now()
        self.write({'stage_id': self.STAGE_MAPPING['IN-PROGRESS']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['IN-PROGRESS']['code']})
        self._compute_status_code()

    def action_review(self):
        """Set task to review state"""
        self.write({'stage_id': self.STAGE_MAPPING['REVIEW']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['REVIEW']['code']})
        self.write({'finish_time': fields.Datetime.now()})
        self._compute_status_code()

    def action_reject(self):
        """Set task to rejected state"""
        self.write({'stage_id': self.STAGE_MAPPING['REJECTED']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['REJECTED']['code']})
        self._compute_status_code()

    def action_reopen(self):
        """Set task back to assigned state"""
        self.write({'stage_id': self.STAGE_MAPPING['ASSIGNED']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['ASSIGNED']['code']})
        self._compute_status_code()

    def action_approve(self):
        """Approve task and set to COMPLETED"""
        self.write({'stage_id': self.STAGE_MAPPING['COMPLETED']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['COMPLETED']['code']})
        self._compute_status_code()
        return True

    def action_cancel(self):
        """Set task to canceled state"""
        self.write({'stage_id': self.STAGE_MAPPING['CANCELED']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['CANCELED']['code']})
        self._compute_status_code()

    def action_un_task(self):
        """
            Un task remove user_ids to empty
        """
        self.write({'user_ids': [(5, 0, 0)]})
        self.write({'stage_id': self.STAGE_MAPPING['OPEN']['id']})
        self.write({'stage_code': self.STAGE_MAPPING['OPEN']['code']})
        self._compute_status_code()


    #==================== Onchange Methods ====================
    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        """
        Set task to assigned state if user_ids is not empty when state is open
        """
        if self.stage_id == self.STAGE_MAPPING['OPEN']['id'] and self.user_ids:
            self.stage_id = self.STAGE_MAPPING['ASSIGNED']['id']
            self.write({'stage_code': self.STAGE_MAPPING['ASSIGNED']['code']})
            self._compute_status_code()
        else:
            self.stage_id = self.STAGE_MAPPING['OPEN']['id']
            self.stage_code = self.STAGE_MAPPING['OPEN']['code']
            self._compute_status_code()

    @api.depends('project_id', 'project_id.user_ids')
    def _compute_available_users(self):
        for task in self:
            if task.project_id and task.project_id.user_ids:
                task.available_user_ids = task.project_id.user_ids
            else:
                task.available_user_ids = self.env['res.users'].browse([])

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Khi thay đổi project, cập nhật domain cho user_ids để chỉ hiển thị người dùng trong project
        """
        if self.project_id:
            # Xóa user đã chọn trước đó
            self.user_ids = [(5, 0, 0)]

            # Lấy danh sách user từ project
            project_users = self.project_id.user_ids

            if project_users:
                _logger.info("Project ID: %s, Project Users: %s", self.project_id.id, project_users.ids)
                # Gán trực tiếp domain mới
                return {'domain': {'user_ids': [('id', 'in', project_users.ids)]}}

        # Nếu không có project hoặc không có users
        return {'domain': {'user_ids': [('id', '=', -1)]}}  # Domain không có kết quả

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
            is_assigned = bool(task.user_ids) or task.stage_id not in [self.STAGE_MAPPING['OPEN']['id'], self.STAGE_MAPPING['REVIEW']['id']]

            # Kiểm tra đã hoàn thành chưa
            is_done = task.stage_id in [self.STAGE_MAPPING['REVIEW']['id'], self.STAGE_MAPPING['COMPLETED']['id']] or task.stage_id == self.STAGE_MAPPING['CANCELED']['id'] and not is_late

            # Xác định status_code
            prefix = "L" if is_late else "N"
            middle = "1" if is_assigned else "0"
            suffix = "1" if is_done else "0"

            task.status_code = f"{prefix}{middle}{suffix}"


    #==================== Override Methods ====================
    # Khi task được tạo, thì auto assign cho user đầu tiên trong project:user_ids,schedule_config,limit_task
    @api.model
    def create(self, vals):
            """
            Tạo task mới và tự động assign cho user đầu tiên trong project
            Check 	AMZ10011 có trùng với task khác trong project không
            """
            if vals.get('name'):
                #check title có trùng với task khác trong project không
                existing_task = self.search([
                    ('project_id', '=', vals['project_id']),
                    ('name', '=', vals['name'])
                ])
                if existing_task:
                    raise UserError("Task code already exists in the project")

            if vals.get('project_id'):
                _logger.info("Creating task with vals: %s", vals)
                project = self.env['project.project'].browse(vals['project_id'])
                #get schedule_config
                schedule_config = project.schedule_config
                #get limit_task
                limit_task = project.limit_task
                #get user_ids
                user_ids = project.user_ids
                if schedule_config == 'balanced':
                    if user_ids:
                        # Get the list of users in the project
                        project_user_ids = user_ids.ids

                        if project_user_ids:
                            # Count tasks assigned to each user in this project
                            user_task_counts = {}
                            for user_id in project_user_ids:
                                task_count = self.search_count([
                                    ('project_id', '=', project.id),
                                    ('user_ids', 'in', [user_id]),
                                    ('stage_id', 'not in', [
                                        self.STAGE_MAPPING['COMPLETED']['id'],
                                        self.STAGE_MAPPING['CANCELED']['id']
                                    ])
                                ])
                                user_task_counts[user_id] = task_count

                            # Find the user with the fewest tasks
                            min_tasks = float('inf')
                            selected_user_id = None

                            for user_id, count in user_task_counts.items():
                                # Skip users who have reached the task limit
                                if limit_task and count >= limit_task:
                                    continue

                                if count < min_tasks:
                                    min_tasks = count
                                    selected_user_id = user_id

                            # Assign task to the selected user if found
                            if selected_user_id:
                                vals['user_ids'] = [(6, 0, [selected_user_id])]
                                _logger.info("Balanced assignment: Task assigned to user ID %s with %s existing tasks",
                                            selected_user_id, min_tasks)
                            else:
                                _logger.warning("All users have reached the task limit (%s). Task left unassigned.", limit_task)

                elif schedule_config == 'limited':
                    #chia theo số lượng task
                    if project.user_ids:
                        vals['user_ids'] = [(6, 0, project.user_ids.ids)]
                elif schedule_config == 'manual':
                    #get user_ids
                    if project.user_ids:
                        vals['user_ids'] = [(6, 0, project.user_ids.ids)]
            return super(ProjectTask, self).create(vals)


