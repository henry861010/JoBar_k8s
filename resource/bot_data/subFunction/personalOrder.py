from .odoo_xmlrpc import *

def personalOrderFunc(models, uid, m_user_name, m_user_id):
    reply_content = 'Hi, ' + m_user_name + ':\n'
    try:
        # 取得odoo UserID(partner_id)
        odoo_user, odoo_partner = getUserDataByLine(models, uid, m_user_id)

        odatas = getRecentOrders(models, uid, odoo_user['partner_id'])
        print(odatas)
        if len(odatas) == 0:
            # reply_content += '找不到您將在 '+getRecentPickupDate(mode=1)+' 取貨的訂單耶...\n趕快去群組下單吧!'
            reply_content += '找不到您的訂單耶...\n趕快去群組下單吧!'

        else:
            dts = sorted(list(set([d['pickup_date'] for d in odatas])))
            for dt in dts:

                reply_content += '\n以下是您在 ' + dt + ' 要取貨的訂單：'

                plas = list(set([d['pickup_area'][1] for d in odatas]))
                for pla in plas:
                    reply_content += '\n====================\n在 ' + pla + ' 取貨：\n'
                    orders = [d['id'] for d in odatas if d['pickup_area'][1] == pla and d['pickup_date'] == dt]
                    details = getOrderDetail(models, uid, orders)
                    # prdts = list(set([ d['name'] for d in details ]))
                    prdts = [{'name': d['name'], 'price': d['price_unit']} for d in details]
                    prdts = [dict(t) for t in {tuple(d.items()) for d in prdts}]
                    for product in prdts:
                        total = int(
                            sum([d['product_uom_qty'] for d in details if d['name'] == product['name']]))
                        if total > 0:
                            reply_content += '\n' + product['name'] + '(單價 ' + str(
                                int(product['price'])) + ')：' + str(total)
                    reply_content += '\n\n總計是 ' + str(int(sum([d['amount_total'] for d in odatas if
                                                                  d['pickup_area'][1] == pla and d[
                                                                      'pickup_date'] == dt]))) + ' 元整'
                if dt != dts[-1]:
                    reply_content += '\n'

    except TypeError:
        reply_content += '您好像還沒綁定帳號喔！\n請前往下方網址以Line註冊登入並且填寫相關資料\nhttps://reurl.cc/RzdgvD'

    return reply_content