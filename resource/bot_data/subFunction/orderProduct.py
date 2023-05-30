from .odoo_xmlrpc import *

def orderProductFunc(models, uid, m_user_name,m_user_id, content_split):
    reply_content = 'Hi, ' + m_user_name + ':\n'

    sign_rules = {
        'plus sign': '+',
        '加': '+',
        '＋': '+',
        '十': '+',
        '十': '+',
        '(': '',
        ')': '',
        '囗': '口',
        '*': '+',
    }
    number_rules = {
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'night': '9',
        'zero': '0',
        '一': '1',
        '二': '2',
        '三': '3',
        '四': '4',
        '五': '5',
        '六': '6',
        '七': '7',
        '八': '8',
        '九': '9',
        '零': '0',
        '１': '1',
        '２': '2',
        '３': '3',
        '４': '4',
        '５': '5',
        '６': '6',
        '７': '7',
        '８': '8',
        '９': '9',
        '０': '0'
    }
    flag = 0  # 判斷格式正確

    # 判斷是否有取貨地點start
    endRow = len(content_split)
    customPUAreaFK = 0

    if content_split[len(content_split) - 1].find("取") > 0:
        flag = 6
        adata = getPickupAreas(models, uid,
                               #    content_split[len(content_split) - 1][:content_split[len(content_split) - 1].find("取")]
                               content_split[-1].split('取')[0].replace('囗', '口').replace('*', '+').strip()
                               )
        if len(adata) != 0:
            customPUAreaFK = adata[0]['id']
            flag = 0

        endRow = endRow - 1
    # 判斷是否有自己加取貨地點結束
    # print(endRow)
    problem = []
    pickup_dates = {}  # 0504
    for i in range(1, endRow):
        for rep, val in sign_rules.items():
            content_split[i] = content_split[i].replace(rep, val)
        content = content_split[i].strip().split('+')
        # 如果下單項目被+號切割後數量不等於2或數量不等於整數
        if len(content) != 2:
            flag = 1
            break
        for rep, val in number_rules.items():
            content[1] = content[1].replace(rep, val)
        try:
            content[1] = int(content[1].strip())
        except ValueError:
            flag = 1
            break
        if content[1] == 0:
            flag = 1
            break

        # 用關鍵字搜尋商品
        check = getProductDataWithKeyword(models, uid, content[0].strip())
        # except TypeError:
        if len(check) == 0 or check['sale_ok'] == False:
            if len(check) == 0:
                # searchProbProduct(models, uid, content[0].strip())
                problem.append(content[0].strip())
            flag = 2
            break
        else:
            if check['pickup_date'] in pickup_dates.keys():
                pickup_dates[check['pickup_date']].append((check['id'], content[1]))
            else:
                pickup_dates[check['pickup_date']] = [(check['id'], content[1])]

        # 檢查商品庫存
        s_status, s_inStock = checkInStock(models, uid, check['id'], int(content[1]))
        if not s_status:
            if s_inStock > 0:
                reply_content += check['name'] + '數量不足了\n'
                flag = 5
            else:
                reply_content += '{} 已經賣完了🥲\n'.format(check['name'])
                flag = 7
            break

    # 取得odoo UserID(partner_id)
    # 取得User取貨地點FK
    odoo_user, odoo_partner = getUserDataByLine(models, uid, m_user_id)
    # print(odoo_partner, '\n-----------------------------------------')
    if odoo_user == [] or odoo_partner == []:
        flag = 3
    else:
        if not odoo_partner['pickup_area'] and customPUAreaFK == 0:
            flag = 4

    if flag == 0:
        # 新增訂單
        #   - 填入odoo UserID
        #   - 填入取貨地點FK
        # 取得訂單ID
        for day in pickup_dates.keys():
            if customPUAreaFK == 0:
                orderId = newOrder(models, uid, odoo_user['partner_id'], day,
                                   odoo_partner['pickup_area'][0])
            else:
                orderId = newOrder(models, uid, odoo_user['partner_id'], day, customPUAreaFK)
            print('----------------------------------------')
            print('[商品資料]')
            try:
                seq = getOrderLineSequence(models, uid, orderId['id'])  # 如果是已經存在的訂單
                orderId = orderId['id']
                print("沿用舊訂單:", orderId)
            except:
                seq = 8  # 新的訂單
                print("添加新訂單", orderId)
            for i, item in enumerate(pickup_dates[day]):  # 0504
                print(item)  # 0504
                newOrderLine(models, uid, orderId, seq + 1 + i, item[0], item[1])  # 0504

        reply_content += '下單成功🤩'
    elif flag == 1:
        reply_content += '糟糕😰格式好像哪裡出錯了\n請確認之後再試一遍🥺'
    elif flag == 2:
        reply_content += '我找不到這樣商品耶...😅\n請確認關鍵字正確之後再試一遍😘'
    elif flag == 3:
        reply_content += '您好像還沒綁定帳號喔🧐\n請前往下方網址以Line註冊登入並且填寫相關資料\nhttps://reurl.cc/an9xXX'
    elif flag == 4:
        reply_content += '您尚未設定有效的取貨地點哦😮\n請前往下方網址設定!\nhttps://reurl.cc/an9xXX'
    elif flag == 5:
        reply_content += '請您調整數量後再嘗試🥲'
    elif flag == 6:
        reply_content += '糟糕😰取貨地點好像打錯了\n請確認之後再試一遍🥲'
    elif flag == 7:
        reply_content += '請您調整下單內容後再試一次😣'

    return reply_content