# __manifest__.py

{
    'name': 'Login With Line Chat App',
    'version': '16.0',
    'sequence': 10,
    'category': 'Authentication',
    'summary': "Login With Line Chat App account",
    'description': "You can now login using your Line Chat App account.",
    'depends': ['base', 'web', 'base_setup', 'auth_signup', 'auth_oauth'],
    'data': [
        'data/auth_oauth_data_line.xml',
        'views/auth_oauth_assets.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
