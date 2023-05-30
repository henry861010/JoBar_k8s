import time
import os
from bot_data.subFunction.processComment import processCommentFunc
from bot_data.subFunction.scratchNewComment import scratchNewCommentFunc
from bot_data.subFunction.scratchNewPost import scratchNewPost
from subFunction.odoo_xmlrpc import *
from dotenv import load_dotenv


def main():
    group_id = '777119749887059'  # 好好吃

    models = endpoint_object()
    uid = conflictRetry(get_uid())
    config_id, grab_freq = returnGrabFreqAndRecoedID(models, uid)
    writeFacebookStatus(models, uid, int(config_id), '程式執行中...（超過3分鐘為異常）')

    facebook_status = ""
    print('[程式開始執行]從Facebook取得社團貼文清單中...')
    post_result = getGroupPosts(group_id, getFacebookToken(models, uid))
    try:
        post_result['data']
        print('貼文抓取完畢！')
    except:
        facebook_status += "貼文抓取失敗"
        print('貼文抓取失敗')
    #     TODO
    # Notify


    new_post_count = scratchNewPost(models, uid, post_result)  # 重新命名變數
    if new_post_count != 0:
        print("這次新增了{}篇貼文。".format(new_post_count))
    else:
        print("這次沒有新增貼文。")

    print('更新完成！抓取各則貼文留言中......')
    facebook_status = scratchNewCommentFunc()

    print('從資料庫取得未完成留言中......')
    comments = getUnprocessComments(models, uid)
    print('完成，共有{}則未處理留言。'.format(len(comments)))
    # 處理留言內容
    processCommentFunc(comments)
    # 將狀態傳回網頁
    if facebook_status == '': facebook_status = '無異常狀況'
    writeFacebookStatus(models, uid, config_id, facebook_status)

while True:
    load_dotenv()
    main()
    FACEBOOK_GRAB_GAP = int(os.getenv('FACEBOOK_GRAB_GAP'))
    time.sleep(60*FACEBOOK_GRAB_GAP)