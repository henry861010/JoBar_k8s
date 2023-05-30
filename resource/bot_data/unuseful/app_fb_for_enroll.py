# coding=utf-8

import re
import json
import time
import requests
import configparser
from operator import itemgetter
from datetime import datetime, timedelta

from odoo_xmlrpc import *


def find_chinese(file):
    pattern = re.compile(r'[^\u4e00-\u9fa5\w\n]')
    chinese = re.sub(pattern, '', file)
    return chinese


def utcEight(strtime):
    dt = strtime.split('T')
    time = dt[1].split('+')
    return datetime.strptime(dt[0] + ' ' + time[0], '%Y-%m-%d %H:%M:%S')


groupId = '777119749887059'  # 好好吃
# groupId = '1672105386472269' #不好吃
debug = 0
test = 0

models = endpoint_object()
uid = conflictRetry(get_uid())
uidGetTime = dt.now()

if debug == 0:
    postId = "777119749887059_1059923164940048"
    checkTime = datetime.now()
    print('=======================================\n從Facebook取得貼文 {} 的留言中....'.format(postId))
    raw_result = getGroupCommentsOnlyForEnroll(getFacebookToken(models, uid), postId, "1000")
    print('抓取完畢，開始更新貼文留言資訊......')
    succ = 0
    fail = 0
    addCount = 0
    # postInfo = getFbPost(models, uid, postId)
    # pageId = postInfo['id']
    pageId = 491
    # postCanComment = raw_result['summary']['can_comment']
    try:
        print('過去3天貼文有{}則留言'.format(len(raw_result['data'])))
        for comment in raw_result['data']:
            addCount += 1
            print(addCount)
            print("原始訊息:{}".format(comment))
            try:
                commentFromId = comment['from']['id']
                partnerData = getUserDataByFb(models, uid, commentFromId)
                commentId = comment['id']
                searchResult = searchFbComment(models, uid, commentId)
                commentContent = str(comment['message'])
                rawCreatedTime = comment['created_time']
                commentCreatedTime = utcEight(rawCreatedTime)
                comment_msg = ""
                user_id = ""
                user_phone = ""

                try:
                    cust_Id, comment_phone = commentContent.split('\n')
                    # print(cust_Id)
                    # print(comment_phone)
                    if cust_Id.find('C') != -1:
                        user_id = int(cust_Id[cust_Id.find("C") + 1:].strip())
                    elif cust_Id.find('c') != -1:
                        user_id = int(cust_Id[cust_Id.find("c") + 1:].strip())
                    elif cust_Id.find(':') != -1:
                        user_id = int(cust_Id[cust_Id.find(":") + 1:].strip())
                    else:
                        user_id = int(cust_Id)

                    if comment_phone.find(":") != -1:
                        user_phone = comment_phone[comment_phone.find(":") + 1:]
                    else:
                        user_phone = comment_phone
                    partnerDatas = getUserDataByID(models, uid, user_id)
                    # print(partnerDatas)
                    # print(len(partnerDatas))
                    if user_id == -1 or user_id == "":
                        print("ID資料錯誤:{}".format(user_id))
                        user_id = 2
                        comment_msg = "ID資料錯誤"
                    elif partnerDatas['phone'] == False:
                        print("會員資料電話未填寫")
                        comment_msg = "會員資料電話未填寫"
                    elif str(user_phone.strip()) != str(partnerDatas['phone'][-3:]):
                        print("電話驗證失敗-原始:{} 填寫:{}".format(partnerDatas['phone'][-3:], user_phone))
                        comment_msg = "聯絡電話驗證失敗"
                    elif partnerDatas['is_enroll'] == True:
                        print("重複註冊或是留言ID填寫錯誤")
                        comment_msg = "重複註冊或是留言ID填寫錯誤"
                    else:
                        comment_msg = "註冊成功"
                except:
                    comment_msg = "資料填寫錯誤"
                    user_id = 2
                if user_id =="":
                    user_id = 2

                print("會員編號:{}".format(user_id))
                try:
                    print("會員電話 原始:{} 填寫:{}".format(str(partnerDatas['phone'][-3:]), str(user_phone)))
                except:
                    print("會員電話未填寫")
                print("會員ID:{}".format(commentFromId))
                print("留言時間:{}".format(commentCreatedTime))
                print("留言狀態:{}".format(comment_msg))

                if len(partnerData) == 0:
                    if len(searchResult) == 0 and comment_msg == '註冊成功':
                        updateUserFBId(models, uid, user_id, commentFromId)
                        addComment(models, uid, str(user_id), pageId, commentId, commentContent,
                                   comment_msg, str(commentCreatedTime))
                        print("留言添加成功")
                        succ += 1
                    elif len(searchResult) == 0 and comment_msg != '註冊成功':
                        addComment(models, uid, str(user_id), pageId, commentId, commentContent,
                                   comment_msg+":"+commentFromId, str(commentCreatedTime))
                        succ += 1
                    elif len(searchResult) >=1 and comment_msg == '註冊成功' and user_id != 2:
                        updateUserFBId(models, uid, user_id, commentFromId)
                        updatePartnerID(models, uid, searchResult['id'], user_id)
                        updateCommentState(models, uid, searchResult['id'], '註冊成功')
                        print("留言添加成功")
                    elif len(searchResult) >= 1 and comment_msg != '註冊成功':
                        updatePartnerID(models, uid, searchResult['id'], user_id)
                        updateCommentState(models, uid, searchResult['id'], comment_msg+":"+commentFromId)
                    succ += 1
                elif len(partnerData) != 0 and partnerData['is_enroll']==False:
                    if len(searchResult) == 0 and comment_msg == '註冊成功':
                        updateUserFBId(models, uid, user_id, commentFromId)
                        addComment(models, uid, str(user_id), pageId, commentId, commentContent,
                                   comment_msg, str(commentCreatedTime))
                        print("留言添加成功")
                    elif len(searchResult) == 0 and comment_msg != '註冊成功':
                        addComment(models, uid, str(user_id), pageId, commentId, commentContent,
                                   comment_msg+":"+commentFromId, str(commentCreatedTime))
                    elif len(searchResult) >= 1 and comment_msg == '註冊成功':
                        updateUserFBId(models, uid, user_id, commentFromId)
                        updatePartnerID(models, uid, searchResult['id'], user_id)
                        updateCommentState(models, uid, searchResult['id'], '註冊成功')
                        print("留言添加成功")
                    elif len(searchResult) >= 1 and comment_msg != '註冊成功':
                        updateCommentState(models, uid, searchResult['id'], comment_msg+":"+commentFromId)
                    succ += 1
                    print("\n")

            except KeyError:
                commentId = comment['id']
                searchResult = searchFbComment(models, uid, commentId)
                if len(searchResult) == 0:
                    commentContent = str(comment['message'])
                    rawCreatedTime = comment['created_time']
                    commentCreatedTime = utcEight(rawCreatedTime)
                    addComment(models, uid, 2, pageId, commentId, commentContent, '沒有授權社團app', str(commentCreatedTime))
                fail += 1
                continue
        if len(raw_result['data']) != 0:
            print('共有{}則留言成功註冊並授權，{}則有誤。本次增加{}則留言...'.format(succ, fail, addCount))
    except KeyError:
        print('No comment!!')
    except Exception as e:
        print('Error:', comment, sep='\n')
        print(e)