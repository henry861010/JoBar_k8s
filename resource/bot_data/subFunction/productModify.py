from .odoo_xmlrpc import *

def productModifyFunc(models, uid, content_split):
    reply_content = 'Hi, 管理員:'

    print(content_split)
    keywords = content_split[1][4:]  # 關鍵字:
    newPickupDate = content_split[2][5:]  # 新取貨日:
    price = content_split[3][3:]  # 價格:
    print("關鍵字:{}".format(keywords))
    print("新取貨日:{}".format(newPickupDate))
    print("價格:{}".format(price))

    # 取得商品資訊
    item = getProductDataWithKeyword(models, uid, keywords)
    # 更新取貨日
    print("商品ID:{}".format(item['id']))
    print("商品價格OLD:{}".format(item['list_price']))
    result = updateProductPickupDate(models, uid, item['id'], newPickupDate, price)
    if result:
        print("成功更新商品資訊")

    if item['pickup_date'] != newPickupDate:  # 如果日期需要更新
        records = getOrderLineRecord(models, uid, item['name'], price, item['sale_start_date'],
                                     item['sale_end_date'], newPickupDate)
    else:
        records = getOrderLineRecord(models, uid, item['name'], price, item['sale_start_date'],
                                     item['sale_end_date'])
    print(records)
    print("===============開始更新==================")
    success = 0
    error = 0
    for rec in records:
        print("訂單ID:{}-產品ID:{}-數量:{} 更新成功".format(rec['order_id'], rec['product_id'],
                                                            rec['product_uom_qty']))
        # 取得舊訂單資料
        order = getOrderData(models, uid, rec['order_id'][0])
        # 取得新訂單ID
        orderId = newOrder(models, uid, order['partner_id'][0], newPickupDate,
                           order['pickup_area'][0])
        # 寫入order line
        try:
            seq = getOrderLineSequence(models, uid, orderId['id'])  # 如果是已經存在的訂單
            orderId = orderId['id']
            print("沿用舊訂單")
        except:
            seq = 8  # 新的訂單
            print("添加新訂單")
        newOrderLine(models, uid, orderId, seq + 1, rec['product_id'][0], rec['product_uom_qty'])
        # 更新舊的order line amount
        result = updateOrderLineAmount(models, uid, rec['id'], 0)
        if result:
            success += 1
            print("更新成功")
        error = len(records) - success
    reply_content += "更新成功!\n"
    reply_content += "===============\n"
    reply_content += "[成功更新筆數]:" + str(success) + '\n'
    reply_content += "[失敗更新筆數]:" + str(error) + '\n'
    reply_content += "===============\n"
    reply_content += "[總共更新筆數]:" + str(len(records))
    return reply_content