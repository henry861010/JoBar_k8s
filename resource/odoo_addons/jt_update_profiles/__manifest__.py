# -*- coding: utf-8 -*-
{
    'name': 'Update Profiles',
    'summary': 'Update profile picture from website',
    'version': '13.0.0.1.0',
    'category': 'Website',
    'depends': ['website', 'portal'],
    'data': [
        'views/update_profile_template.xml',
        'views/test.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'images': ['static/description/poster_image.png'],
}
