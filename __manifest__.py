{
    'name': 'Custom Cancel Field Service',
    'version': '1.0',
    'category': 'Services/Field Service',
    'summary': 'Add cancel functionality to field service orders',
    'description': """
        This module extends the field service functionality by adding:
        - Cancel button for orders in progress
        - Cancellation reason selection
        - New status for cancelled orders
    """,
    'depends': ['industry_fsm'],
    'data': [
        'security/ir.model.access.csv',

        'views/project_task_views.xml',
        'wizard/cancel_reason_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}