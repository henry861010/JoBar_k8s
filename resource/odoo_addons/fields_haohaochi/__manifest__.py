# -*- coding: utf-8 -*-
{
    'name': "Fong Mei Shih Costumer Order management",
    'version': '14.0.2.1.0',
    'summary': 'Costum development for HAO HAO CHI Fong Mei Shih',
    'description': 'Costum development for HAO HAO CHI Fong Mei Shih',
    'author': 'Aaronace',
    'license': 'AGPL-3',
    'version': '1.0',
    'depends': ['base','sale','mail','product',],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/contacts_view.xml',
        'views/product_view.xml',
        
        
        ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}