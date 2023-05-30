# coding=utf-8

import re
import json
import time
import requests
import configparser
from operator import itemgetter
from datetime import datetime, timedelta

from odoo_xmlrpc import *

# coding=utf-8

def find_chinese(file):
    pattern = re.compile(r'[^\u4e00-\u9fa5\w\n+＋]')
    chinese = re.sub(pattern, '', file)
    return chinese


def utcEight(strtime):
    dt = strtime.split('T')
    time = dt[1].split('+')
    return datetime.strptime(dt[0] + ' ' + time[0], '%Y-%m-%d %H:%M:%S') #+ timedelta(hours=8)



debug = 0
test = 0
managers = [100]
models = endpoint_object()
uid = conflictRetry(get_uid())
uidGetTime = dt.now()

postId = "777119749887059_1059923164940048"
pageId = 491

if debug==0:
    
    checkTime = datetime.now()
    if (checkTime - uidGetTime) > timedelta(minutes=10):
        models = endpoint_object()
        uid = conflictRetry(get_uid())
        uidGetTime = datetime.now()
        print("Connect & UID updated!!")
    print('[程式開始執行]\n\n從Facebook取得註冊貼文留言中......')
    raw_result = getGroupCommentsOnlyForEnroll(getFacebookToken(models, uid), postId, "1000")
    print('抓取完畢，開始更新貼文留言資訊......')
    addCount = 0

    try:
        print('近三天有{}則留言'.format(len(raw_result['data'])))
        for comment in raw_result['data']:
            commentId = commnet['id']
            searchResult = searchFbComment(models, uid, commentId)
            rawCreatedTime = comment['created_time']
            commentCreatedTime = utcEight(rawCreatedTime)
            commentContent = str(comment['message'])
            try:
                commentFromId = comment['from']['id']
            except KeyError:
                if len(searchResult) == 0:
                    addComment(models, uid, 2, pageId, commentId, commentContent, '沒有授權社團app',
                               str(commentCreatedTime))
                continue
            partnerData = getUserDataByFb(models, uid, commentFromId)
            if len(partnerData) != 0:
                if partnerData['id'] in managers:
                    continue
                if len(searchResult) == 0:
                    addComment(models, uid, partnerData['id'], pageId, commentId, commentContent, 'for enroll',
                               str(commentCreatedTime))
                else:
                    if searchResult['state'] != '註冊成功' and partnerData['is_enroll'] == False:
                        if searchResult['partnerId'] == 2:
                            updatePartnerID(models, uid, searchResult['id'], int(partnerData['id']))
                        if searchResult['comment_content'] != commentContent:
                            updatePartnerContent(models, uid, searchResult['id'], commentContent)
                        updateCommentState(models, uid, searchResult['id'], 'for enroll')
                
            else: # 有成功授權但沒有找到正確ID
                commentFromName = comment['from']['name']
                if len(searchResult) == 0:
                    addComment(models, uid, 2, pageId, commentId, commentContent, '未成功連動:' + commentFromName + comment['from']['id'],
                               str(commentCreatedTime))

    except KeyError:
        print("No Comment!!")
    except Exception as e:
        print('Error: ', comment, sep='\n')
        print(e)

    print('=======================================\n留言新增/更新完畢......\n')

if debug == 0:
    comments = getForEnrollComments(models, uid)
    if len(comments) != 0:
        for comment in comments:
            flag = 0
            checkTime = datetime.now()
            if (checkTime - uidGetTime) > timedelta(minutes=10):
                models = endpoint_object()
                uid = conflictRetry(get_uid())
                uidGetTime = datetime.now()
                print("Connect & UID updated!!")
            if len(comment['comment_content'].strip()) > 0:
                m_content = comment['comment_content'].upper().strip()
                content_split = m_content.split('\n')
                if len(content_split) == 2:               
                    p1 = re.compile("C\d{6}")
                    p2 = re.compile("\d{3}")
                    valid_id = p1.findall(content_split[0].strip())
                    valid_num = p2.findall(content_split[1].strip())
                    
                    if len(valid_id)!=1 or len(valid_num)!=1:
                        flag = 1
                    else:
                        custId = int(valid_id[0][1:])
                        custPhone = valid_num[0]
                        partnerData = getUserDataByID(models, uid, comment['partner_id'])
                        if partnerData['phone'] == False:
                            flag = 2
                        else:
                            if custPhone != partnerData[-3:]:
                                flag = 3
                            else:
                                if partnerData['is_enroll'] == True:
                                    flag = 4
                else:
                    flag = 1
            else:
                flag = 1

            if flag == 0:
                updateCommentState(models, uid, comment['id'], '註冊成功')
                
                

                
                

        print("處理留言完成！")
    else:
        print("沒有需要處理的留言。")
                
