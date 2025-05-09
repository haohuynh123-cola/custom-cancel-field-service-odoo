from odoo import models, fields, api

class ProjectProjectTaskConfig(models.Model):
    _inherit = 'project.project'

    user_ids = fields.Many2many(
        'res.users',
        string='User',
        ondelete='cascade',
        index=True,
    )

    schedule_config = fields.Selection(  [
        ('balanced', 'Balanced'),
        ('limited', 'Limited'),
        ('manual', 'Manual'),
    ], string='Schedule Config', default='balanced')

    limit_task = fields.Integer(string='Limit Task', default=10)



    




