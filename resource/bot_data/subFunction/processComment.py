from operator import itemgetter
from datetime import datetime, timedelta
from .odoo_xmlrpc import *

sign_rules = {
    'plus sign': '+',
    '加': '+',
    '＋': '+',
    '十': '+',
    '十': '+',
    '(': '',
    ')': '',
    '囗': '口',
    ' ': '',
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

def processCommentFunc(comments):
    # 如果回傳長度不為0
    if len(comments) != 0:
        # 按留言時間進行排序
        comments = sorted(comments, key=itemgetter('create_time'))

        print('開始處理未完成留言......')
        for comment in comments:
            checkTime = datetime.now()
            if (checkTime - uidGetTime) > timedelta(minutes=10):
                models = endpoint_object()
                uid = conflictRetry(get_uid())
                uidGetTime = datetime.now()
                print("Connect & UID updated!!")
            print(comment)

            if len(comment['comment_content'].strip()) > 0:

                m_content = comment['comment_content'].upper().strip()
                content_split = m_content.split('\n')

                # if content_split[-1].find("取") == -1:
                #     content_split = content_split[:-1]

                # if content_split[0] == '下單' and len(content_split) > 1:

                flag = 0  # 紀錄最後處理狀態

                # 判斷留言是否有取貨地點
                endRow = len(content_split)
                customPUAreaFK = 0

                print(content_split)
                if content_split[-1].find("取") > 0:
                    flag = -1
                    adata = getPickupAreas(models, uid,content_split[-1].split('取')[0].replace('囗', '口').strip())
                    if len(adata) != 0:
                        customPUAreaFK = adata[0]['id']
                        flag = 0
                    else:
                        flag = 4
                    endRow = endRow - 1

                if endRow == 0:
                    flag = 1
                else:
                    # 對每行留言進行分析
                    pickup_dates = {}  # 0504
                    for i in range(1, endRow):
                        for rep, val in sign_rules.items():
                            content_split[i] = content_split[i].replace(rep, val)
                        content = content_split[i].strip().split('+')
                        print(content)
                        # 如果下單項目被+號切割後數量不等於2或數量不等於整數
                        if len(content) != 2:
                            flag = 1
                            break
                        try:
                            content[1] = int(content[1].strip())
                        except ValueError:
                            flag = 1
                            break
                        if content[1] == 0:
                            flag = 1
                            break

                        # 檢查商品是否存在
                        check = getProductDataWithKeyword(models, uid, content[0].strip())
                        if len(check) == 0 or check['sale_ok'] == False:
                            flag = 2
                            break
                        else:
                            if check['pickup_date'] in pickup_dates.keys():
                                pickup_dates[check['pickup_date']].append((check['id'], content[1]))
                            else:
                                pickup_dates[check['pickup_date']] = [(check['id'], content[1])]

                        # 檢查商品庫存數量是否足夠
                        s_status, s_inStock = checkInStock(models, uid, check['id'], int(content[1]))
                        if not s_status:
                            flag = 3
                            break

                        if customPUAreaFK == 0:
                            customPUAreaFK = getPartnerPUArea(models, uid, comment['partner_id'][0])
                            if not customPUAreaFK:
                                flag = 4

                        if comment['partner_id'][0] == 2:
                            flag = 7

                if flag == 0:
                    orderName = ""
                    for day in pickup_dates.keys():
                        print(comment['partner_id'][0], day, customPUAreaFK)
                        orderId = newOrder(models, uid, comment['partner_id'][0], day, customPUAreaFK)
                        print(orderId)
                        for i, item in enumerate(pickup_dates[day]):  # 0504
                            # print(item) # 0504
                            newOrderLine(models, uid, orderId, 10 - 1 + i, item[0], item[1])  # 0504
                        order_result = getOrderData(models, uid, orderId)
                        if orderName == "":
                            orderName += order_result['name']
                        else:
                            orderName += '&{}'.format(order_result['name'])
                    print(orderName)
                    updateCommentState(models, uid, comment['id'], 'Done=' + orderName)
                    print('[' + str(comment['id']) + ': Done=' + orderName + ']')
                elif flag == 1:
                    updateCommentState(models, uid, comment['id'], 'Error#1:格式錯誤')
                    print('[' + str(comment['id']) + ': Error_1=格式錯誤]')
                elif flag == 2:
                    updateCommentState(models, uid, comment['id'], 'Error#2:找不到商品')
                    print('[' + str(comment['id']) + ': Error_2=找不到商品]')
                elif flag == 3:
                    updateCommentState(models, uid, comment['id'], 'Error#3:庫存不足')
                    print('[' + str(comment['id']) + ': Error_3=庫存不足]')
                elif flag == 4:
                    updateCommentState(models, uid, comment['id'], 'Error#4:取貨地點有誤')
                    print('[' + str(comment['id']) + ': Error_4=取貨地點有誤]')
                elif flag == 5:
                    updateCommentState(models, uid, comment['id'], 'Error#5:ID與資料庫未配對')
                    print('[' + str(comment['id']) + ': Error_5=ID與資料庫未配對]')
                elif flag == 6:
                    updateCommentState(models, uid, comment['id'], 'Error#6:未註冊or授權')
                    print('[' + str(comment['id']) + ': Error_6=未註冊or授權]')
                elif flag == 7:
                    updateCommentState(models, uid, comment['id'], 'Error#7:ID填寫錯誤')
                    print('[' + str(comment['id']) + ': Error_7=ID填寫錯誤]')
            else:
                updateCommentState(models, uid, comment['id'], 'Error#1:格式錯誤')
                print('[' + str(comment['id']) + ': Error_1=格式錯誤]')
        print('處理留言完成。')
    else:
        print('沒有需要處理的留言。')