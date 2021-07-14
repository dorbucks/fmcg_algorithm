#!/usr/bin/python3
# -*- coding: utf8 -*-
import os
from tools.web_hook import TeamsHook
from tools.plus_api import MoreToken
from dotenv import load_dotenv
from tools import feature_related as fr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import os
import pickle
import pymysql

last_date = datetime(datetime.now().year, datetime.now().month, 1).date() - timedelta(days=1)
start_date = last_date.strftime(r'%Y-%m-01')
end_date = last_date.strftime(r'%Y-%m-%d') #自動設定日期區間為前月首、末日

load_dotenv()
key_gen = MoreToken(os.getenv('API_EMAIL'), os.getenv('API_CLIENTID'))
hook = TeamsHook(os.getenv('HOOK_URI'))
mongo_uri = os.getenv('MONGO_URI')

product_list = [x for x in os.listdir('ibk_setting') if x != 'readme']

if __name__ == '__main__':
    print('start_date: %s, end_date: %s' %(start_date, end_date))

    hook.post_text("feature_related computing process start")
    #連結teams webhook功能自動貼上程式運行狀態
    try:
        output_list = []
        for file in product_list:
            print(file)
            industry = re.sub('\.xlsx$', '', file)
            product_file = pd.read_excel(f'ibk_setting/{file}', sheet_name=3)
            product_file = product_file[["產業名稱", "品牌名稱", "系列名稱", "產品名稱", "舊PRO"]]
            product_file = product_file.loc[product_file['舊PRO'].apply(lambda x: False if x is np.nan else True)]
            product_file['產品名稱'] = product_file.apply(lambda x: str(x['品牌名稱']) + '~~' + str(x['產品名稱']), axis=1)
            post_list = fr.count_feature(industry, start_date, end_date, key_gen, limit='3')
            result_list = fr.count_topic_list(mongo_uri, post_list, product_file, industry)
            if not result_list:
                hook.post_text(f'no result found in {file}!')
                continue
            output_list.append(result_list)

        print("save data on pickle")
        with open('backup/feature_related_%s.pickle' % datetime.now().strftime('%Y-%m-01'), 'wb') as pk:
            pickle.dump(output_list, pk)

        output_table = [[x[0] for x in y] for y in output_list]
        output_table = sum(output_table, [])
        output_table = pd.concat(output_table, ignore_index=True).reset_index(drop=True)
        output_table = output_table.drop(columns=['content'])
        output_table['brand'] = output_table['product'].apply(lambda x: x.split('~~')[0])
        output_table['product'] = output_table['product'].apply(lambda x: x.split('~~')[1])
        output_table = output_table[['_id', 'post_id', 'brand', 'product', 'author', 'title', 'date', 'comment_count', 'channel', 'url', 'sub_count', 'rank', 'industry', 'feature_rank', 'feature', 'apply_date']]
        print("write data to excel")
        output_table.to_excel('backup/feature_related_%s.xlsx' % datetime.now().strftime('%Y-%m-01'))

        print("write data to MYSQL")
        conn = pymysql.connect(
        host=os.getenv('SQL_HOST'),
        user=os.getenv('SQL_USER'),
        password=os.getenv('SQL_PASSWORD'),
        database='test',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        sql = "INSERT INTO `feature_related` (`comment_id`, `post_id`, `brand`, `product`, `author`, `title`, `date`, `comment_count`, `channel`, `url`, `sub_count`, `rank`, `industry`, `feature_rank`, `feature`, `apply_date`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        insert_into = output_table.values.tolist()
        cursor.executemany(sql, insert_into)
        conn.commit()
        conn.close()

        hook.post_text("feature_related computing process successed")

    except Exception as ermsg:
        hook.post_text(f"group_related computing process failed, error messsage: {ermsg}")
