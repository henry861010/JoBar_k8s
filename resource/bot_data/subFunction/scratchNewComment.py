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

def scratchNewCommentFunc():
    facebook_status = ""
    for postId in getValidPost(models, uid):
        checkTime = datetime.now()
        if (checkTime - uidGetTime) > timedelta(minutes=10):
            models = endpoint_object()
            uid = conflictRetry(get_uid())
            uidGetTime = datetime.now()
            print("Connect & UID updated!!")
        print('=======================================\n從Facebook取得貼文 {} 的留言中....'.format(postId))
        raw_result = getGroupCommentsForEachPost(getFacebookToken(models, uid), postId, "500")
        # print(raw_result)
        print('抓取完畢，開始更新貼文留言資訊......')
        succ = 0
        fail = 0
        addCount = 0
        postInfo = getFbPost(models, uid, postId)
        pageId = postInfo['id']
        print(pageId)
        try:
            postCanComment = raw_result['summary']['can_comment']
        except:
            postCanComment = False
        try:
            print('貼文有{}則留言'.format(len(raw_result['data'])))
            for comment in raw_result['data']:
                addCount += 1
                try:
                    commentId = comment['id']
                    searchResult = searchFbComment(models, uid, commentId)

                    commentContent = find_chinese(str(comment['message'].replace('*', '+')))
                    rawCreatedTime = comment['created_time']
                    commentCreatedTime = utcEight(rawCreatedTime)

                    try:
                        user_id = ""
                        rawComment = comment['message'].replace("號", "").replace("：", ":").split("\n")
                        rawComment[0] = rawComment[0].strip().upper()
                        if rawComment[0].find('C') != -1:
                            user_id = int(rawComment[0][rawComment[0].find("C") + 1:])
                        elif rawComment[0].find('c') != -1:
                            user_id = int(rawComment[0][rawComment[0].find("c") + 1:])
                        elif rawComment[0].find(':') != -1:
                            user_id = int(rawComment[0][rawComment[0].find(":") + 1:])
                        else:
                            user_id = int(rawComment[0])

                        # print(user_id)

                        if len(searchUsersID(models, uid, user_id)) == 0:
                            user_id = 2
                    except:
                        user_id = 2

                    if len(searchResult) == 0:
                        if user_id != 2:
                            addComment(models, uid, user_id, pageId, commentId, commentContent, 'incomplete',
                                       str(commentCreatedTime))
                        else:
                            addComment(models, uid, user_id, pageId, commentId, commentContent, '未留言編號',
                                       str(commentCreatedTime))
                    else:
                        if searchResult['state'][:4].upper().strip() != 'DONE':
                            # print(searchResult['state'])
                            if user_id != 2 and int(
                                    searchResult['partner_id'][0]) == 2:  # 如果有找到新的ID替代原本的Odoobot
                                updatePartnerID(models, uid, searchResult['id'], user_id)
                                print("成功更新ID:{}_{}".format(user_id, comment['from']['name']))
                                updateCommentState(models, uid, searchResult['id'], 'incomplete')  # 如果有更新ID要重新抓
                            if searchResult['comment_content'] != find_chinese(
                                    str(comment['message'].replace('*', '+'))) \
                                    and int(searchResult['partner_id'][0]) != 100:  # 也不等於業主的留言# 如果留言有更新就寫入
                                print("Old:{}\n".format(searchResult['comment_content']))
                                print("New:{}\n".format(str(comment['message'])))
                                updatePartnerContent(models, uid, searchResult['id'],
                                                     find_chinese(str(comment['message'].replace('*', '+'))))
                                print("成功更新留言:{}{}\n".format(searchResult['id'], str(comment['message'])))
                                updateCommentState(models, uid, searchResult['id'], 'incomplete')  # 如果有更新留言要重新抓
                            if searchResult['state'][:7] == 'Error#3' or searchResult['state'][:4] == '沒有授權':
                                updateCommentState(models, uid, searchResult['id'], 'incomplete')  # 如果庫存不足要重新抓
                    succ += 1
                except KeyError:
                    commentId = comment['id']
                    searchResult = searchFbComment(models, uid, commentId)
                    if len(searchResult) == 0:
                        commentContent = str(comment['message'])
                        rawCreatedTime = comment['created_time']
                        commentCreatedTime = utcEight(rawCreatedTime)
                        addComment(models, uid, 2, pageId, commentId, commentContent, '未留言編號',
                                   str(commentCreatedTime))
                    fail += 1
                    continue
            if len(raw_result['data']) != 0:
                print('共有{}則留言成功註冊並授權，{}則有誤。本次增加{}則留言...'.format(succ, fail, addCount))
            if postCanComment == False:
                updatePostState(models, uid, postId, False)
        except KeyError:
            print('No comment!!')
            facebook_status += "留言抓取失敗\n"
            continue
        except Exception as e:
            print('Error:', comment, sep='\n')
            print(e)
            facebook_status += e + '\n'
            # a = input("Can I continue?")
            continue

        # a = input('Press Enter again.')
    print('=======================================\n留言新增/更新完畢......\n')
    return facebook_status