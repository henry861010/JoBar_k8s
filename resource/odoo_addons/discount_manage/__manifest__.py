{
        'name': 'Discount manage',
        'description': 'Record user using discount',
        'author': 'Aaronace',
        'depends': ['base','mail'],
        'application': True,
        'version': '13.0',
        'license': 'AGPL-3',
        'installable': True,

        'data': [
            'security/security.xml',
            'security/ir.model.access.csv',
            'views/discount_manage_views.xml',
            ]

}

