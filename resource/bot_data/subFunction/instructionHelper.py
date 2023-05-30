def instructionHelperFunc(m_user_name):
    reply_content = 'Hi, ' + m_user_name + ':\n'
    reply_content += '👇以下為機器人指令👇\n'
    reply_content += '\n'
    reply_content += '[貨品更新]\n'
    reply_content += '取貨更新\n關鍵字:{}\n新取貨日:YYYY-MM-DD\n價格:{}\n'
    reply_content += '\n'
    reply_content += '[貨品刪除]\n'
    reply_content += '貨品刪除\n關鍵字:{}'
    return reply_content