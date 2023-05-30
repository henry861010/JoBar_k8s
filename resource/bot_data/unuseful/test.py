from odoo_xmlrpc import *

models = endpoint_object()
uid = get_uid()

raw_result = getGroupCommentsForEachPost(getFacebookToken(models, uid), '777119749887059_1049771485955216', '500')

succ=0
fail=0
for comment in raw_result['data']:
    try:
        commentFromId = comment['from']['id']
        partnerData = getUserDataByFb(models, uid, commentFromId)
        # print(commentFromId, comment['from']['name'], ':\n', comment['id'], '-', str(comment['message']),  sep='')
        if len(partnerData) != 0:
            commentId = comment['id']
            searchResult = searchFbComment(models, uid, commentId)
            if len(searchResult) == 0:
                commentContent = str(comment['message'])
                # content_split = commentContent.split('\n')
                # if content_split[0] == '下單' and len(content_split) > 1:
                rawCreatedTime = comment['created_time']
                commentCreatedTime = utcEight(rawCreatedTime)
                # print(commentCreatedTime)
                addComment(models, uid, partnerData['id'], pageId, commentId, commentContent, 'incomplete', str(commentCreatedTime))
                # print('Add a comment:')
                # print(comment)
                addCount += 1
            # print('is memeber\n')
            else:
                if searchResult['state'][:4]!='Done':
                    updateCommentState(models, uid, searchResult['id'], 'incomplete')
            succ += 1
        else:
            #有成功授權但是沒比對到正確的ID
            commentFromName=comment['from']['name']
            commentId = comment['id']
            searchResult = searchFbComment(models, uid, commentId)
            if len(searchResult) == 0:
                commentContent = str(comment['message'])
                # content_split = commentContent.split('\n')
                # if content_split[0] == '下單' and len(content_split) > 1:
                rawCreatedTime = comment['created_time']
                commentCreatedTime = utcEight(rawCreatedTime)
                # print(commentCreatedTime)
                addComment(models, uid, 2, pageId, commentId, commentContent, '未成功連動:'+commentFromName, str(commentCreatedTime))
                addCount += 1
            fail += 1
    except KeyError:
        # print('Comment KeyError:')
        # print(comment)
        # print()
        # 沒有取得from return
        commentId = comment['id']
        searchResult = searchFbComment(models, uid, commentId)
        if len(searchResult) == 0:
            commentContent = str(comment['message'])
            # content_split = commentContent.split('\n')
            # if content_split[0] == '下單' and len(content_split) > 1:
            rawCreatedTime = comment['created_time']
            commentCreatedTime = utcEight(rawCreatedTime)
            # print(commentCreatedTime)
            addComment(models, uid, 2, pageId, commentId, commentContent, '沒有授權社團app',str(commentCreatedTime))
            addCount += 1
        fail += 1
        # time.sleep(0.1)
        continue
    # time.sleep(0.3)

print('Done')