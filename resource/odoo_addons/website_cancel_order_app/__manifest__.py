# -*- coding: utf-8 -*-
{
    "name" : "Website Cancel Order",
    "author": "Edge Technologies",
    "version" : "13.0.1.0",
    "live_test_url":'https://youtu.be/TRsMKXkkGUE',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Apps for Website Order cancel apps helps the user to request for cancel Order from website eCommerce cancel order webshop order cancel eCommerce order cancel webhop order cancel from eCommerce sale order cancel from website cancel order from my account web',
    "description": """
        This app helps user to request to cancel the order in the website.
    """,
    "license" : "OPL-1",
    "depends" : ['base','website','website_sale','sale_management'],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order_cancel.xml',
        'views/sale_template.xml',
    ],
    "auto_install": False,
    "installable": True,
    "price": 18,
    "currency": 'EUR',
    "category" : "eCommerce",
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
