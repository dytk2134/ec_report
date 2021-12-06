#!/usr/bin/env python
# -*- coding: utf-8 -*-
from celery import Celery
from celery.schedules import crontab
from app import create_app
import datetime
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
import config
import requests
import urllib.parse
from urllib.parse import parse_qs
import time
import pandas
import re

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

def make_celery(app):
    app.config.from_object(config)

    _celery = Celery(
        app.import_name,
        backend=app.config['REDIS'],
        broker=app.config['REDIS'],
    )

    _celery.conf.update(app.config)

    class ContextTask(_celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    _celery.Task = ContextTask
    return _celery

celery = make_celery(create_app())

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls read_sheet 每天0點0分
    sender.add_periodic_task(
        crontab(minute=0, hour=0, day_of_week='*', day_of_month='*', month_of_year='*'),
        #crontab(minute='*/5'),
        read_sheet.s(),
    )
    # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=15, minute=0, day_of_week=1),
    #     read_sheet.s(),
    # )

def get_order(username, password):
    # 只抓兩個月內的資料
    today = datetime.datetime.now()
    orders = dict()
    with requests.Session() as session:
        login_post = session.post('https://your.domain/admin/index.php?route=login', data={'username': username, 'password': password})
        parsed = urllib.parse.urlparse(login_post.url)
        user_token = parse_qs(parsed.query)['user_token'][0]
        page = 1
        while True:
            target_url = 'https://your.domain/admin/index.php?route=sale/order&user_token=%s&page=%s' % (user_token, str(page))
            source = session.get(target_url).text
            df_list = pandas.read_html(source)
            order_date = today
            exit_while = False
            for idx, order_id in enumerate(df_list[0]['訂單編號']):
                try:
                    order_number = int(order_id)
                    order_date = datetime.datetime.strptime(df_list[0]['產生日期'][idx], '%Y-%m-%d  %H:%M:%S')
                    if today - datetime.timedelta(weeks=9) > order_date:
                        # 9週前的資料就不抓了
                        exit_while = True
                        break
                    orders[order_number] = {
                        'status': df_list[0]['狀態'][idx],
                        'last_update': df_list[0]['修改日期'][idx],
                        'detail': list()
                    }
                except ValueError:
                    # 尚無資料
                    exit_while = True
                    break
            if exit_while:
                break
            page += 1
        # 獲取訂單詳細資訊
        for order_number in orders:
            order_infos = list()
            target_url = 'https://your.domain/admin/index.php?route=sale/order/info&user_token=%s&order_id=%s' % (user_token, str(order_number))
            source = session.get(target_url).text
            df_list = pandas.read_html(source)
            order_date = datetime.datetime.strptime(df_list[0][1][1], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d')
            total_price = 0
            final_price = 0
            highest_idx = 0
            total_discount = 0
            discount_code = ''
            for idx, rowheader in enumerate(reversed(df_list[4]['圖片'])):
                if pandas.isnull(rowheader):
                    price = int(df_list[4]['總計'][len(df_list[4]['圖片'])-1-idx][1:].replace(',',''))
                    # 折扣金額用正的處理
                    discount = price * (total_price-final_price) // total_price
                    total_discount += discount
                    order_info = [
                        '%s%s' % (order_date, str(order_number)), # 訂單編號
                        df_list[1][1][0], # 會員名稱
                        df_list[1][1][3] if not pandas.isnull(df_list[1][1][3]) else '', # 連絡電話
                        df_list[4]['商品名稱'][len(df_list[4]['圖片'])-1-idx],# 商品名稱
                        df_list[4]['型號'][len(df_list[4]['圖片'])-1-idx],# 商品型號
                        int(df_list[4]['數量'][len(df_list[4]['圖片'])-1-idx]),# 數量
                        df_list[2][1][0] if not pandas.isnull(df_list[2][1][0]) else '',# 發票號碼
                        discount_code,# 折扣碼
                        discount,# 折扣金額
                        price - discount,# 銷貨金額
                        orders[order_number]['status'],# 訂單狀態
                        orders[order_number]['last_update'],# 出貨日
                    ]
                    order_infos.append(order_info)
                    if int(df_list[4]['總計'][idx][1:].replace(',','')) < int(df_list[4]['總計'][len(df_list[4]['圖片'])-1-idx][1:].replace(',','')):
                        highest_idx = len(order_infos)-1
                elif rowheader == '商品合計':
                    total_price = int(df_list[4]['總計'][len(df_list[4]['圖片'])-1-idx][1:].replace(',',''))
                elif rowheader == '訂單總計':
                    final_price = int(df_list[4]['總計'][len(df_list[4]['圖片'])-1-idx][1:].replace(',',''))
                elif '折價券' in rowheader:
                    discount_code = re.search('折價券 \((.*)\)', rowheader).group(1)

            order_infos[highest_idx][8] += total_price - final_price - total_discount # 折扣金額
            order_infos[highest_idx][9] -= total_price - final_price - total_discount # 銷貨金額
            orders[order_number]['detail'].extend(order_infos)
    return orders

@celery.task()
def read_sheet():
    print(datetime.datetime.now().strftime('%Y%m%d'))
    scopes = ["https://spreadsheets.google.com/feeds"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(celery.conf['SERVER_ACCOUNT_JSON'], scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(celery.conf['SHEET_ID']).sheet1
    rows = sheet.get_all_values()
    orders = get_order(celery.conf['EC_USERNAME'], celery.conf['EC_PASSWORD'])
    exists_orders = set()
    # 更新訂單狀態
    for idx, row in enumerate(rows[1:]):
        if row[0] != '':
            # 表格的訂單編號為訂單日期+訂單號碼(e.g. 202106251648)
            order_number = int(row[0][8:])
            if order_number in orders:
                if row[10] != orders[order_number]['status']:
                    time.sleep(2)
                    sheet.update('K'+str(idx+1+1), orders[order_number]['status'])
                if row[11] != orders[order_number]['last_update']:
                    time.sleep(2)
                    sheet.update('L'+str(idx+1+1), orders[order_number]['last_update'])
                exists_orders.add(order_number)
    # 補上沒有在表上的訂單
    for order_number in orders:
        if order_number not in exists_orders:
            for detail in orders[order_number]['detail']:
                time.sleep(2)
                sheet.append_row(detail)


def get_googleauth():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(celery.conf['GDRIVE_CREDENTIALSFILE'])
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    return gauth

