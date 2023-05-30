import configparser
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from subFunction.odoo_xmlrpc import *
import time

load_dotenv()
ANNOUNCE_NOTIFY = os.getenv('ANNOUNCE_NOTIFY')
configs = configparser.ConfigParser()
configs.read('announce.ini', 'utf-8')

models = endpoint_object()
uid = conflictRetry(get_uid())

def main():
    print('檢查產品數量是否充足...檢查中')
    product_announce, amount_announce = getAmountLessProducts(models, uid)

    # 找尋對應FB post
    print('匯出臉書貼文...')
    site, content = getValidPostMessage(models, uid)

    print("開始發送警示訊息...")
    for index in range(len(product_announce)):
        for item in range(len(content)):
            if content[item].find(product_announce[index]['product_keywords']) != -1:
                year = str(datetime.now().date().strftime("%Y"))
                month = str(datetime.strptime(product_announce[0]['sale_end_date'], "%Y-%m-%d %H:%M:%S").month).zfill(2)
                product = product_announce[index]['product_keywords']
                try:
                    rec_amount = configs[year+month][product]
                except:
                    rec_amount = 9999
                print("產品名稱:{} 剩餘數量:{}".format(product, amount_announce[index]))

                if int(rec_amount) > int(amount_announce[index]) and int(amount_announce[index]) < 10 :
                    try:
                        configs.add_section(year+month)
                    except:
                        print("Error occured while adding section to config.")
                    configs.set(year+month, product, str(int(amount_announce[index])))

                    messages = "\n[{}]已經剩下最後{}份\n請前往下方網址關閉留言:\n{}".format(product_announce[index]['name'],
                                                                                           int(amount_announce[index]),
                                                                                           site[item])
                    url = 'https://notify-api.line.me/api/notify'
                    payload = {'message': messages}
                    headers = {'Authorization': 'Bearer {}'.format(ANNOUNCE_NOTIFY)}
                    res = requests.post(url, data=payload, headers=headers)
                    if res.status_code == 200:
                        print("Line Notify 警示訊息已發送")
                    else:
                        print("Line Notify 警示訊息請求失敗，響應狀態碼：{}".format(res.status_code))

    with open('announce.ini', 'w', encoding='utf-8') as configfile:
        configs.write(configfile)

    print("檢查完畢")

if __name__ == '__main__':
    while True:
        main()
        ANNOUNCE_GAP = int(os.getenv('ANNOUNCE_GAP'))
        time.sleep(60*ANNOUNCE_GAP)
