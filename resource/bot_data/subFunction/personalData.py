from .odoo_xmlrpc import *

def personalDataFunc(models, uid, m_user_id, m_user_name):
    reply_content = 'Hi, ' + m_user_name + ':\n'
    try:
        # 取得odoo UserID(partner_id) ['id', 'email', 'phone', 'pickup_area','user_discount', 'is_enroll']
        odoo_user, odoo_partner = getUserDataByLine(models, uid, m_user_id)
        print(odoo_user)
        print(odoo_partner)

        id = "C" + str(odoo_partner['id']).zfill(6)
        enroll = "成功" if odoo_partner['is_enroll'] == True else "失敗"
        reply_content += '[個人編號]:' + str(id) + '\n'
        reply_content += '[Email]:' + str(odoo_partner['email']) + '\n'
        reply_content += '[取貨區域]:' + str(odoo_partner['pickup_area']) + '\n'
        reply_content += '[購物金]:$' + str(odoo_partner['user_discount']) + '\n'
        reply_content += '[註冊狀態]:' + str(enroll) + '\n'
        reply_content += '[備註]:\n非臉書用戶註冊狀態失敗請忽略'

    except TypeError:
        reply_content += '您好像還沒綁定帳號喔！\n請前往下方網址以Line註冊登入並且填寫相關資料\nhttps://reurl.cc/RzdgvD'

    return reply_content