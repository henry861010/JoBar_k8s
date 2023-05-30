import json
import requests
import os
import configparser
import xmlrpc.client
from pprint import pprint
from thefuzz import fuzz, process
from datetime import timedelta, datetime as dt
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DATABASE')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

#錯誤重試
def conflictRetry(func):
    sleepSec = 0.3 #step1:setup your sleep time between two retry
    retryLimit = 5 #step2:setup your retry count
    retryCount = 0 #cur retry count(no need to setup)
    while True:
        if retryCount>=retryLimit:
            print('retryCount:',retryCount,' over retryLimit:',retryLimit)
            break
        try:
            return func
        except:
            print('sleep ',sleepSec,' sec...')
            sleep(sleepSec)
            retryCount+=1
            print('start to retry...')
            continue
        break


# odoo model 連線
def connectOdoo():
    # 創建連接
    connect = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    # connect.version()
    return connect


def endpoint_object():
    #  is used to call methods of odoo models via the execute_kw RPC function.
    return xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))


def get_uid():
    # Logging in
    connect = connectOdoo()
    uid = connect.authenticate(db, username, password, {})
    return uid


# 取得LINE客戶資料
def getUserDataByLine(models, uid, line_id):
    udata = models.execute_kw(db, uid, password,
                              'res.users', 'search_read',
                              [[['oauth_uid', '=', line_id]]],
                              {'fields': ['id', 'active', 'login', 'partner_id', 'oauth_provider_id', 'oauth_uid',
                                          'oauth_access_token']}
                              )
    if len(udata) != 0:
        result_user = udata[0]
    else:
        return [], []
    result_user['partner_id'] = result_user['partner_id'][0]

    pdata = models.execute_kw(db, uid, password,
                              'res.partner', 'search_read',
                              [[['id', '=', result_user['partner_id']]]],
                              {'fields': ['id', 'email', 'phone', 'pickup_area','user_discount', 'is_enroll']}
                              )
    if len(pdata) != 0:
        result_partner = pdata[0]
    else:
        return [], []

    return result_user, result_partner


# 取得指定ID之Partner的取貨地點
def getPartnerPUArea(models, uid, partner_id):
    adata = models.execute_kw(db, uid, password, 'res.partner', 'search_read',
                              [[['id','=',partner_id]]],
                              {'fields': ['pickup_area']}
                             )
    if len(adata) == 0 or not adata[0]['pickup_area']:
        return 0
    else:
        return adata[0]['pickup_area'][0]

# 取得指定ID的訂單資料
def getOrderData(models, uid, order_id):
    # List all records
    rdata = models.execute_kw(db, uid, password,
                              'sale.order', 'search_read',
                              [[['id', '=', order_id]]],
                              {'fields': ['id', 'partner_id', 'amount_total', 'pickup_date', 'pickup_area', 'name']}
                              )
    if len(rdata) == 0:
        return []

    # return ids of record in sale.order
    return rdata[0]

def getOrderDetail(models, uid, order_id):
    ldata = models.execute_kw(db, uid, password,
                              'sale.order.line', 'search_read',
                              [[['order_id','=',order_id]]],
                              {'fields':['id', 'name', 'price_unit','product_uom_qty']})
    return ldata

# 取得所有上架中商品
def getValidProducts(models, uid):
    tdatas = models.execute_kw(db, uid, password,
                              'product.template', 'search_read',
                              [[['sale_ok', '=', True]]],
                              {'fields': ['id', 'name', 'amount_limit', 'sale_start_date', 'sale_end_date','list_price', 'product_keywords']}
                              )

    ids = list(set([d['id'] for d in tdatas]))
    pdatas = models.execute_kw(db, uid, password,
                            'product.product', 'search_read',
                            [[['product_tmpl_id', '=', ids]]],
                            {'fields': ['id', 'product_tmpl_id']}
                            )

    result = []
    for idx, tmpl in enumerate(tdatas):
        product = [item for item in pdatas if item['product_tmpl_id'][0] == tmpl['id']][0]
        odatas = models.execute_kw(db, uid, password,
                            'sale.order.line', 'search_read',
                            [[['product_id', '=', product['id']],
                                ['create_date', '>', tmpl['sale_start_date']],
                                ['create_date', '<', tmpl['sale_end_date']],
                                ['state', '!=', 'draft'],
                                ['state', '!=', 'cancel'],
                                ]],
                            {'fields': ['id', 'product_id', 'product_uom_qty']}
                            )
        sum_sold = 0
        if len(odatas) != 0:
            for data in odatas:
                sum_sold += data['product_uom_qty']
        if tmpl['amount_limit']-sum_sold > 0:
            result.append(tmpl)
    return result

# 取得數量即將不足的產品(Line Notify Use)
def getAmountLessProducts(models, uid):
    tdatas = models.execute_kw(db, uid, password,
                              'product.template', 'search_read',
                              [[['sale_ok', '=', True]]],
                              {'fields': ['id', 'name', 'amount_limit', 'sale_start_date', 'sale_end_date','list_price', 'product_keywords']}
                              )

    ids = list(set([d['id'] for d in tdatas]))
    pdatas = models.execute_kw(db, uid, password,
                            'product.product', 'search_read',
                            [[['product_tmpl_id', '=', ids]]],
                            {'fields': ['id', 'product_tmpl_id']}
                            )

    result = []
    solded = []
    for idx, tmpl in enumerate(tdatas):
        product = [item for item in pdatas if item['product_tmpl_id'][0] == tmpl['id']][0]
        odatas = models.execute_kw(db, uid, password,
                            'sale.order.line', 'search_read',
                            [[['product_id', '=', product['id']],
                                ['create_date', '>', tmpl['sale_start_date']],
                                ['create_date', '<', tmpl['sale_end_date']],
                                ['state', '!=', 'draft'],
                                ['state', '!=', 'cancel'],
                                ]],
                            {'fields': ['id', 'product_id', 'product_uom_qty']}
                            )
        sum_sold = 0
        if len(odatas) != 0:
            for data in odatas:
                sum_sold += data['product_uom_qty']
        #if tmpl['amount_limit']-sum_sold < int(tmpl['amount_limit']*0.05) and tmpl['amount_limit']-sum_sold > 0 and tmpl['amount_limit']-sum_sold <= 10:
        if tmpl['amount_limit']-sum_sold > 0 and tmpl['amount_limit']-sum_sold <= 10:
            result.append(tmpl)
            solded.append(tmpl['amount_limit']-sum_sold)

    return result,solded


# 取得指定關鍵字的產品資料
def getProductDataWithKeyword(models, uid, product_keyword):
    tdata = models.execute_kw(db, uid, password,
                              'product.template', 'search_read',
                              [[['product_keywords', '=', product_keyword]]],
                              {'fields': ['id', 'name', 'sale_ok', 'list_price', 'amount_limit', 'sale_start_date',
                                          'sale_end_date', 'pickup_date', 'list_price']}
                              )

    if len(tdata) == 0:
        return []
    # else:
    #     return pdata[0]

    t_id = tdata[0]['id']
    pdata = models.execute_kw(db, uid, password,
                              'product.product', 'search_read',
                              [[['product_tmpl_id', '=', t_id]]],
                              {'fields': ['id']}
                              )

    tdata[0]['id']=pdata[0]['id']
    return tdata[0]


# 取得可能的產品
def searchProbProduct(models, uid, productName):
    products = getValidProducts(models,uid)
    keywords = [product["product_keywords"] for product in products]
    result = process.extract(productName, keywords, limit=5)
    result = [name for name, score in result if score>75]
    return result

# 取得指定ID的產品庫存
def checkInStock(models, uid, product_id, amount):
    pdata = models.execute_kw(db, uid, password,
                              'product.product', 'search_read',
                              [[['id', '=', product_id]]],
                              {'fields': ['product_tmpl_id']}
                              )

    tmpl_id = pdata[0]['product_tmpl_id'][0]
    # print(tmpl_id)
    tdata = models.execute_kw(db, uid, password,
                              'product.template', 'search_read',
                              [[['id', '=', tmpl_id]]],
                              {'fields': ['id', 'name', 'amount_limit', 'sale_start_date', 'sale_end_date']}
                              )



    odatas = models.execute_kw(db, uid, password,
                               'sale.order.line', 'search_read',
                               [[['product_id', '=', product_id],
                                 ['create_date', '>', tdata[0]['sale_start_date']],
                                 ['create_date', '<', tdata[0]['sale_end_date']],
                                 ['state', '!=', 'draft'],
				 ['state', '!=', 'cancel']]],
                               {'fields': ['id', 'product_id', 'product_uom_qty']}
                               )
    sum_sold = 0
    if len(odatas) != 0:
        for data in odatas:
            sum_sold += data['product_uom_qty']

    if amount <= tdata[0]['amount_limit'] - sum_sold:
        return True, int(tdata[0]['amount_limit'] - sum_sold)
    else:
        return False, int(tdata[0]['amount_limit'] - sum_sold)


# 取得最近一次的取貨日期(mode=0:新增訂單時用，mode=1:查詢訂單時用)
def getRecentPickupDate(mode=0):
    today = dt.now().date()
    if mode == 1: # 取貨日期顯示調整
        today = dt.now().date()-timedelta(1)
    t_year, t_week, t_weekday = today.isocalendar()
    if t_weekday >= 5:
        pd_year, pd_week, pd_weekday = (today + timedelta(days=7)).isocalendar()
        pickup_date = dt.fromisocalendar(pd_year, pd_week, 2).date().isoformat()
    elif t_weekday < 2:
        pickup_date = dt.fromisocalendar(t_year, t_week, 2).date().isoformat()
    else:
        pickup_date = dt.fromisocalendar(t_year, t_week, 5).date().isoformat()
    return pickup_date


# # 新增訂單
# def newOrder(models, uid, user_fk, pickup_date, pickup_area_fk):
#     # pickup_date = getRecentPickupDate()
#     result_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [{
#         'partner_id': user_fk,
#         'pickup_area': pickup_area_fk,
#         'pickup_date': pickup_date,
#         'state': 'sale'
#     }])
#     return result_id

def searchOrder(models, uid, user_fk, pickup_date, pickup_area_fk):
    result_id = models.execute_kw(db, uid, password, 'sale.order', 'search',
                                [[['partner_id', '=', user_fk],
                                    ['pickup_area', '=', pickup_area_fk],
                                    ['pickup_date', '=', pickup_date],
                                    ['state', '=', 'sale']]])
    return result_id

# 新增訂單
def newOrder(models, uid, user_fk, pickup_date, pickup_area_fk):
    # pickup_date = getRecentPickupDate()
    pre_search = searchOrder(models,uid, user_fk, pickup_date, pickup_area_fk)
    if len(pre_search)==0:
        result_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [{
            'partner_id': user_fk,
            'pickup_area': pickup_area_fk,
            'pickup_date': pickup_date,
            'state': 'sale'
        }])
        return result_id
    else:
        return pre_search[0]



# 取得訂單細項最大sequence
def getOrderLineSequence(models, uid, order_fk):
    result_id = models.execute_kw(db, uid, password, 'sale.order.line', 'search_read',
                                  [[['order_id', '=', order_fk]]],
                                  {'fields': ['sequence']})[-1]['sequence']
    return result_id

# 取得特定商品sale_order_line records
def getOrderLineRecord(models, uid, product_name, price, start_date, end_date, new_date=None):

    if not new_date:
        result_id = models.execute_kw(db, uid, password, 'sale.order.line', 'search_read',
                                      [[['name', '=', product_name],
                                        ['state', '=', 'sale'],
                                        ['price_unit', '!=', int(price)],
                                        ['product_uom_qty', '>', 0],
                                        ['write_date', '>=', start_date],
                                        ['write_date', '<=', end_date]]],
                                      {'fields': ['id', 'order_id', 'product_uom_qty', 'product_id']})
    else:
        result_id = models.execute_kw(db, uid, password, 'sale.order.line', 'search_read',
                                      [[['name', '=', product_name],
                                        ['state', '=', 'sale'],
                                        ['product_uom_qty', '>', 0],
                                        ['write_date', '>=', start_date],
                                        ['write_date', '<=', end_date]]],
                                      {'fields': ['id', 'order_id', 'product_uom_qty', 'product_id']})
    if len(result_id)==0:
        return []
    return result_id

# 更新訂單細項產品數量
def updateOrderLineAmount(models, uid, order_line_fk, amount):
    result_id = models.execute_kw(db, uid, password, 'sale.order.line', 'write',
                                  [[order_line_fk],
                                  {'product_uom_qty': amount}])
    pprint(result_id)
    return result_id

# 更新訂單細項產品數量
def updateProductPickupDate(models, uid, id, date, price):
    product_tmpl_id = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                  [[['id', '=', id]]],
                                  {'fields': ['id','product_tmpl_id']})[0]['product_tmpl_id']
    print("更新產品ID:{}名稱:{}".format(product_tmpl_id[0],product_tmpl_id[1]))
    print("更新產品日期:{}價錢:{}".format(date,price))
    result_id = models.execute_kw(db, uid, password, 'product.template', 'write',
                                  [[product_tmpl_id[0]],
                                  {'pickup_date': date,
                                   'list_price': price}])
    return result_id


# 新增訂單細項
def newOrderLine(models, uid, order_fk, seq, product_fk, amount):
    try:
        result_id = models.execute_kw(db, uid, password, 'sale.order.line', 'create', [{
            'order_id': order_fk,
            'sequence': seq,
            'product_id': product_fk,
            'product_uom_qty': amount,
            'state': 'sale'
        }])
    except Exception:
        print(order_fk, seq, product_fk, amount)


# 取得特定取貨地點名的完整資料
def getPickupAreas(models, uid, areaname):
    adatas = models.execute_kw(db, uid, password, 'res.pickup_area', 'search_read',
                               [[['area_name', '=', areaname]]],
                               {'fields': ['id', 'area_name']})
    return adatas


# 取得指定ID顧客最近一次取貨日的訂單
def getRecentOrders(models, uid, customer_id):
    pickup_date = dt.now().date().strftime('%Y-%m-%d')
    odatas = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
                               [[['partner_id','=', customer_id],
                                 ['pickup_date', '>=', pickup_date],
                                 ['state', '=', 'sale']]],
                               {'fields': ['id', 'name', 'access_token', 'pickup_date', 'pickup_area', 'amount_total']})
    if len(odatas)==0:
        return []
    else:
        return odatas

################Facebook################

# 取得特定ID的Facebook貼文
def getFbPost(models, uid, id):
    # models = endpoint_object()
    # uid = get_uid()
    pdatas = models.execute_kw(db, uid, password, 'facebookmanage','search_read',
                               [[['page_id', '=', id]]],
                               {'fields' : ['id', 'page_id', 'update_time']}
                              )
    if len(pdatas) == 0:
        return []
    else:
        return pdatas[0]


# 尋找特定ID的Facebook留言
def searchFbComment(models, uid, id):
    # models = endpoint_object()
    # uid = get_uid()
    cdatas = models.execute_kw(db, uid, password, 'facebookcomment','search_read',
                               [[['comment_id', '=', id]]],
                               {'fields' : ['id', 'create_time', 'partner_id', 'comment_content', 'state']}
                              )

    if len(cdatas) == 0:
        return []
    else:
        return cdatas[0]

# 尋找特定ID
def searchUsersID(models, uid, id):
    cdatas = models.execute_kw(db, uid, password, 'res.partner','search_read',
                               [[['id', '=', id]]],
                               {'fields' : ['id', 'name']}
                              )
    if len(cdatas) == 0:
        return []
    else:
        return cdatas[0]

# 新增未出現過的貼文至資料庫
def addFbPost(models, uid, postId, updatedTime, content, address, valid):
    # models = endpoint_object()
    # uid = get_uid()
    result_id = models.execute_kw(db, uid, password, 'facebookmanage', 'create', [{
        'page_id': postId,
        'update_time': updatedTime,
        'message_content': content,
        'site': address,
        'is_valid': valid
    }])

    return result_id


# 更新資料庫中現有的貼文資料
def updateFbPost(models, uid, id, updatedTime, content):
    # models = endpoint_object()
    # uid = get_uid()
    models.execute_kw(db, uid, password, 'facebookmanage', 'write', [[id], {
        'update_time': updatedTime,
        'message_content': content
    }])

    return 0


# 將符合規則的留言加入資料庫
def addComment(models, uid, partnerId, postId, commentId, content, state, createdTime):
    # models = endpoint_object()
    # uid = get_uid()
    # Create records
    models.execute_kw(db, uid, password, 'facebookcomment', 'create', [{
        'partner_id': partnerId,
        'page_id': postId,
        'comment_id': commentId,
        'state': state,
        'comment_content': content,
        'create_time': createdTime
    }])


# 取得所有未處理的Facebook留言
def getUnprocessComments(models, uid):
    # models = endpoint_object()
    # uid = get_uid()
    cdatas = models.execute_kw(db, uid, password, 'facebookcomment','search_read',
                               [[['state', '=', 'incomplete']]],
                                # [[['state', '=', 'Error#2:找不到商品'],['page_id','=',852]]],
                                # [[['id','=','1819']]],
                               {'fields' : ['id', 'create_time', 'partner_id', 'comment_content']}
                              )
    if len(cdatas) == 0:
        return []
    else:
        return cdatas

def getTestComments(models, uid):
    cdatas = models.execute_kw(db, uid, password, 'facebookcomment','search_read',
                               [[['state', '=', 'test']]],
                                # [[['state', '=', 'Error#1:格式錯誤']]],
                                # [[['id','=','1819']]],
                               {'fields' : ['id', 'create_time', 'partner_id', 'comment_content']}
                              )
    if len(cdatas) == 0:
        return []
    else:
        return cdatas

# 取得所有等待驗證註冊的留言
def getForEnrollComments(models, uid):
    # models = endpoint_object()
    # uid = get_uid()
    cdatas = models.execute_kw(db, uid, password, 'facebookcomment','search_read',
                               [[['state', '=', 'for enroll']]],
                                # [[['state', '=', 'Error#1:格式錯誤']]],
                                # [[['id','=','1819']]],
                               {'fields' : ['id', 'create_time', 'partner_id', 'comment_content']}
                              )
    if len(cdatas) == 0:
        return []
    else:
        return cdatas

# 更新留言
def updatePartnerContent(models, uid, comment_id, content):
    # models = endpoint_object()
    # uid = get_uid()
    # Update records

    models.execute_kw(db, uid, password, 'facebookcomment', 'write', [[comment_id], {
        'comment_content': content,
    }])
    return 0

# 更新留言ID
def updatePartnerID(models, uid, comment_id, partner_id):
    # models = endpoint_object()
    # uid = get_uid()
    # Update records

    models.execute_kw(db, uid, password, 'facebookcomment', 'write', [[comment_id], {
        'partner_id': int(partner_id),
    }])
    return 0

# 更新留言處理狀態
def updateCommentState(models, uid, comment_id, state):
    # models = endpoint_object()
    # uid = get_uid()
    # Update records

    models.execute_kw(db, uid, password, 'facebookcomment', 'write', [[comment_id], {
        'state': state,
    }])
    return 0


# 取得Facebook開發者token
def getFacebookToken(models, uid):
    # models = endpoint_object()
    # uid = get_uid()
    token = models.execute_kw(db, uid, password,
                              'facebookconfig', 'search_read',
                              [[['id', '=', 1]]])

    return token[0]['accesstoken']

# 取得貼文內容
def getValidPostMessage(models, uid):
    # models = endpoint_object()
    # uid = get_uid()
    pdatas = models.execute_kw(db, uid, password,
                                'facebookmanage', 'search_read',
                                [[['is_valid', '=', True]]],
                                {'fields': ['site','message_content']})
    site = []
    content = []

    for post in pdatas:
        site.append(post['site'])
        content.append(post['message_content'])

    return site, content


# 取得需要擷取的貼文
def getValidPost(models, uid):
    # models = endpoint_object()
    # uid = get_uid()
    pdatas = models.execute_kw(db, uid, password,
                                'facebookmanage', 'search_read',
                                [[['is_valid', '=', True]]],
                                {'fields': ['page_id','site','message_content']})
    result = []

    for post in pdatas:
        result.append(post['page_id'])
    return result

def getValidPostId(models,uid):
    pdatas = models.execute_kw(db, uid, password,
                                'facebookmanage', 'search_read',
                                [[['is_valid', '=', True]]],
                                {'fields': ['id','page_id','site','message_content']})
    result = []

    for post in pdatas:
        result.append(post['id'])
    return result

#
def getGroupPosts(groupId, token):
    # 擷取前7天更新的貼文(一小時3600秒)
    minus_time = str(int(dt.now().timestamp()) - 3600*24*7)
    raw_result = requests.get(
        "https://graph.facebook.com/v15.0/" + groupId \
        + "/feed?fields=id,updated_time,message&limit=10" \
        + "&since=" + minus_time\
        +"&access_token=" + token)
    #print(raw_result)
    return raw_result.json()


def getGroupCommentsForEachPost(token, postId, commentamount):
    #擷取前一小時的留言(一小時3600秒)
    # minus_time = str(int(datetime.now().timestamp()) - 3600)
    raw_result = requests.get(
        "https://graph.facebook.com/v15.0/" + postId\
        + "/comments?fields=id,from{id,name},created_time,message" \
        # + "&since=" + minus_time\
        + "&summary=can_comment" \
        + "&limit=" + commentamount \
        + "&access_token=" + token)
    return raw_result.json()

# 更新fb_app_id & is_enroll
def updateUserFBId(models, uid, partner_id, fb_id):

    models.execute_kw(db, uid, password, 'res.partner', 'write', [[partner_id], {
        'fb_app_id': fb_id,'is_enroll': 'true',
    }])
    return 0

def getGroupCommentsOnlyForEnroll(token, postId, commentamount):
    #擷取前3天前的留言(一小時3600秒)
    minus_time = str(int(dt.now().timestamp()) - 3600*24*3)
    raw_result = requests.get(
        "https://graph.facebook.com/v13.0/" + postId\
        + "/comments?fields=id,from{id,name},created_time,message" \
        + "&since=" + minus_time\
        + "&summary=can_comment" \
        + "&limit=" + commentamount \
        + "&access_token=" + token)
    #print(raw_result.json())
    return raw_result.json()


# 取得Facebook客戶資料
def getUserDataByFb(models, uid, fb_id):
    # models = endpoint_object()
    # uid = get_uid()
    pdata = models.execute_kw(db, uid, password,
                              'res.partner', 'search_read',
                              [[['fb_app_id', '=', fb_id]]],
                              {'fields': ['id', 'email', 'phone', 'pickup_area', 'is_enroll']}
                              )
    if len(pdata) != 0:
        result_partner = pdata[0]
    else:
        return []

    return result_partner

# 透過ID取得客戶資料
def getUserDataByID(models, uid, id):
    # models = endpoint_object()
    # uid = get_uid()
    pdata = models.execute_kw(db, uid, password,
                              'res.partner', 'search_read',
                              [[['id', '=', id]]],
                              {'fields': ['id', 'email', 'phone', 'pickup_area', 'is_enroll']}
                              )
    if len(pdata) != 0:
        result_partner = pdata[0]
    else:
        return []

    return result_partner

def updatePostState(models, uid, post_id, state):
    # models = endpoint_object()
    # uid = get_uid()
    # Update records
    pdatas = models.execute_kw(db, uid, password, 'facebookmanage', 'search', [[['page_id', '=', post_id]]])
    print(pdatas)
    models.execute_kw(db, uid, password, 'facebookmanage', 'write', [ pdatas, {
        'is_valid': state
    }])
    return 0

def returnGrabFreqAndRecoedID(models, uid):
    renew_freq = models.execute_kw(db, uid, password,
                                   'res.config.settings', 'search_read',
                                   [[['id', '!=', 1]]],
                                   {'fields': ['id', 'getComment_freq']})
    id , freq = renew_freq[-1]['id'],renew_freq[-1]['getComment_freq']
    return id , freq


def writeFacebookStatus(models, uid, id, message):
    models.execute_kw(db, uid, password, 'res.config.settings', 'write', [id, {
        'facebook_status': message
    }])
    return 0
