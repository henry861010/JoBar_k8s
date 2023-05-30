import re
from .odoo_xmlrpc import *
from datetime import datetime, timedelta

def find_chinese(file):
    pattern = re.compile(r'[^\u4e00-\u9fa5\w\n+＋]')
    chinese = re.sub(pattern, '', file)
    return chinese


def utcEight(strtime):
    dt = strtime.split('T')
    time = dt[1].split('+')
    return datetime.strptime(dt[0] + ' ' + time[0], '%Y-%m-%d %H:%M:%S')  # + timedelta(hours=8)

def scratchNewPost(models, uid, post_result):
    newPostCount = 0
    for post in post_result['data']:
        postId = post['id']
        postUdTime = utcEight(post['updated_time'])
        postInfo = getFbPost(models, uid, postId)
        addr = postId.split('_')
        address = 'https://www.facebook.com/groups/' + addr[0] + '/posts/' + addr[1] + '/'
        try:
            msg = post['message']
        except:
            msg = ''
            post['message'] = ''
        postContent = find_chinese(msg)
        # print(postContent)
        postType = postContent.split('\n')[0][-3:]
        # print(postType)
        if len(postInfo) == 0:
            if postType == "到貨團":
                addFbPost(models, uid, postId, str(postUdTime), find_chinese(post['message']), address,
                                   True)
            else:
                addFbPost(models, uid, postId, str(postUdTime), find_chinese(post['message']), address,
                                   False)
            newPostCount += 1
        else:
            if postInfo['update_time'] != str(postUdTime):
                updateFbPost(models, uid, postInfo['id'], str(postUdTime), find_chinese(post['message']))

        return newPostCount