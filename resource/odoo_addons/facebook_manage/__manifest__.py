{
        'name': 'Facebook comment manage',
        'description': 'Analyze the comment and make it add in sale order',
        'author': 'Aaronace',
        'depends': ['base','mail'],
        'application': True,
        'version': '13.0',
        'license': 'AGPL-3',
        'installable': True,

        'data': [
            'security/facebookmanage_security.xml',
            'security/ir.model.access.csv',
            'views/facebook_manage_views.xml',
            'views/account_validate.xml',
            'views/res_config_setting_view.xml',
            ]

}

