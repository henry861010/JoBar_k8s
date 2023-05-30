# coding=utf-8

import re
import json
import time
import requests
import configparser
from operator import itemgetter
from datetime import datetime, timedelta

from odoo_xmlrpc import *

# partner_list = [88]
# amount_list = [5]

models = endpoint_object()
uid = conflictRetry(get_uid())
uidGetTime = dt.now()

updateOrderLineAmount(models, uid, 40909, 10)

# count = 0
# for partner_id in partner_list:
#     product_fk = 159
#     day = '2022-06-24'
#     amount = amount_list[count]
#     count += 1
#     # 取得odoo UserID(partner_id)
#     # 取得User取貨地點FK
#     pickup_area = getPartnerPUArea(models, uid, partner_id)
#
#     # 新增訂單
#     #   - 填入odoo UserID
#     #   - 填入取貨地點FK
#     # 取得訂單ID
#
#     orderId = newOrder(models, uid, partner_id, day, pickup_area)
#     print('----------------------------------------')
#     print('[商品資料]')
#
#     try:
#         seq = getOrderLineSequence(models, uid, orderId['id'])  # 如果是已經存在的訂單
#         orderId = orderId['id']
#     except:
#         seq = 8  # 新的訂單
#     print("seq:{}".format(seq))
#     newOrderLine(models, uid, orderId, seq + 1, product_fk, amount)  # 0504