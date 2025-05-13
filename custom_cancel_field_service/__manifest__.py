{
    'name': 'Custom Field Service',
    'version': '1.0',
    'category': 'Services/Field Service',
    'summary': 'Add cancel functionality to field service orders',
    'description': """
        This module extends the field service functionality by adding:
        - Cancel button for orders in progress
        - Cancellation reason selection
        - New status for cancelled orders
        - Reject button for orders in review
        - Reject reason selection
        - New status for rejected orders
        - Urgent task decoration
    """,
    'depends': ['industry_fsm', 'sale', 'web'],
    'data': [
        # Models Security
        'security/ir.model.access.csv',

        # Views
        'views/project_task_views.xml',
        'views/project_edit_form_views.xml',

        # Wizard
        'wizard/cancel_reason_wizard_views.xml',
        'wizard/reject_reason_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
