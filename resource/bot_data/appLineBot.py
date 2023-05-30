import os
from dotenv import load_dotenv

from subFunction.customerService import customerServiceFunc
from subFunction.feasibleOrderProduct import feasibleOrderProductFunc
from subFunction.instructionHelper import instructionHelperFunc
from subFunction.orderProduct import orderProductFunc
from subFunction.personalData import personalDataFunc
from subFunction.personalOrder import personalOrderFunc
from subFunction.productDelete import productDeleteFunc
from subFunction.productModify import productModifyFunc
from subFunction.odoo_xmlrpc import *
from datetime import datetime as dt, timedelta as td
from flask import Flask, request, abort
from gevent.pywsgi import WSGIServer
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError, LineBotApiError)
from linebot.models import (
    MessageEvent, FollowEvent, JoinEvent, MemberJoinedEvent, TextMessage, ImageMessage, TextSendMessage,
    ImageSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageTemplateAction, URITemplateAction
)

load_dotenv()
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os. getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os. getenv('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN, timeout=(10.0, 10.0))
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# xmlrpc建立連線
models = endpoint_object()
uid = conflictRetry(get_uid())
uidGetTime = dt.now()

@app.route("/callback", methods=['POST'])
def callback():
    global uidGetTime
    checkTime = dt.now()
    if (checkTime - uidGetTime) > td(minutes=10):
        models = endpoint_object()
        uid = conflictRetry(get_uid())
        uidGetTime = dt.now()
        print("Connect & UID updated!!")

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # app.logger.info("Request body: " + body)

    print("====================================================\n[Request Body]\n" + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
        print('===================================================')
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    m_user_id = event.source.user_id
    m_content = event.message.text.upper().strip()

    try:
        m_user_profile = line_bot_api.get_profile(m_user_id)
    except LineBotApiError:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="嗨嗨！這位朋友\n我還不認識你，可以把我加入好友嗎OwO/"))

    m_user_name = m_user_profile.display_name

    m_chatroom_name = "未知的聊天室"
    reply_content = ""

    # TODO
    # 驗證過的GROUP才能使用功能
    # 需要驗證使用者身分


    if m_content == "/link" or m_content == "/LINK":
        reply_content = "https://liff.line.me/1661139702-8mxWLJ6n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

    # 在群組時做的事
    if event.source.type == 'group':
        m_chatroom_name = line_bot_api.get_group_summary(event.source.group_id).group_name
        content_split = m_content.split('\n')

        if content_split[0] == "/小幫手":
            reply_content = instructionHelperFunc(m_user_name)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply_content))

        if content_split[0] == "取貨更新" and len(content_split) >= 2:
            reply_content = productModifyFunc(models, uid, content_split)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

        if content_split[0] == "貨品刪除" and len(content_split) >= 2:
            reply_content = productDeleteFunc(models, uid, content_split)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

        # 「可訂商品」關鍵字適用於群組及個人
        if m_content == '可訂商品':
            reply_content = feasibleOrderProductFunc(models, uid, m_user_name)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply_content))

        if content_split[0].strip() == '下單' and len(content_split) > 1:
            reply_content = orderProductFunc(models, uid, m_user_name, m_user_id, content_split)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply_content))


    # 在個人聊天室時做的事
    elif event.source.type == 'user':
        m_chatroom_name = "自己的聊天室"

        if m_content.strip() == '個人訂單' or m_content.strip() == '取貨總額':
            reply_content = personalOrderFunc(models, uid, m_user_name, m_user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply_content))

        if m_content == '取貨資訊':
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(
                    original_content_url='https://haohaochi.subuy.net/web/image/3026/S__119816203_0.jpg',
                    preview_image_url='https://haohaochi.subuy.net/web/image/3026/S__119816203_0.jpg'
                )
            )

        if m_content == '客服聯繫':
            reply_content = customerServiceFunc(m_user_name)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

        # 「可訂商品」關鍵字適用於群組及個人
        if m_content == '可訂商品':
            reply_content = feasibleOrderProductFunc(models, uid, m_user_name)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

        if m_content == '個人資訊':
            reply_content = personalDataFunc(models, uid, m_user_id, m_user_name)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_content))

    print('-----------------------------------------')
    print('[訊息內容]')
    print(m_user_name + " 在 ", m_chatroom_name + " 說：\n" + m_content)
    if reply_content != "":
        print('-----------------------------------------')
        print('[已回覆的內容]\n')
        print(reply_content)

@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    print('-----------------------------------------')
    print('收到了一張圖片')


if __name__ == "__main__":
    # app.run()
    # waitress.serve(app, host='0.0.0.0', port='5000')
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()