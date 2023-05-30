from .odoo_xmlrpc import *

def feasibleOrderProductFunc(models, uid, m_user_name):
    valid_products = getValidProducts(models, uid)
    reply_content = 'Hi, ' + m_user_name + ':\n'
    reply_content += "以下為目前可訂購商品列表:\n"
    for item in valid_products:
        reply_content += "\n喊單關鍵字：" + item['product_keywords']
    reply_content += "\n請喊關鍵字+數量喔"
    reply_content += "\n\n範例:\n下單(換行)\n草莓+1(換行)\n蘋果+1"
    return reply_content