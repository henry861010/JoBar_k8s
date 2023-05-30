from .odoo_xmlrpc import *

def productDeleteFunc(models, uid, content_split):
    reply_content = 'Hi, 管理員:'
    keywords = content_split[1][4:]  # 關鍵字:
    item = getProductDataWithKeyword(models, uid, keywords)
    print(item['name'])
    print(item['list_price'])
    print(item['sale_start_date'])
    print(item['sale_end_date'])
    records = getOrderLineRecord(models, uid, item['name'], int(item['list_price']), item['sale_start_date'],
                                 item['sale_end_date'], '1971-01-01')  # 最後面添加一個日期方便取得所有紀錄(無意義)
    print("待處理紀錄:{}筆".format(len(records)))
    print("===============開始更新==================")
    success = 0
    error = 0
    for rec in records:
        try:
            # 更新舊的order line amount
            result = updateOrderLineAmount(models, uid, rec['id'], 0)
            print("訂單ID:{}-產品ID:{}-數量:{}-刪除成功(數量更新為0)".format(rec['order_id'], rec['product_id'],
                                                                             rec['product_uom_qty']))
            if result:
                print("更新完畢")
                success += 1
        except:
            error += 1

    reply_content += "刪除成功!\n"
    reply_content += "===============\n"
    reply_content += "[成功刪除筆數]:" + str(success) + '\n'
    reply_content += "[失敗刪除筆數]:" + str(error) + '\n'
    reply_content += "===============\n"
    reply_content += "[總共刪除筆數]:" + str(len(records))

    return reply_content