# -*- coding: utf8 -*-
from tools.plus_api import PlusApi
from pymongo import MongoClient
from bson.objectid import ObjectId
import pandas as pd
import numpy as np
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from tools.key_search import key_search
from multiprocessing import Pool
from itertools import repeat
from datetime import datetime
import re

class ParSearch(object):
    def __init__(self, core=10):
        self.pool = Pool(core)

    def search_pro(self, content, key):
        return(self.pool.starmap(key_search, zip(repeat(content), list(key))))

    def close(self):
        self.pool.close()
        self.pool.join()

class MongoWorker(object):
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)

    def retrive_post_data(self, db, collection, object_id):
        self.db = self.client[db]
        self.collection = self.db[collection]
        return self.collection.find({"_id":ObjectId(object_id)},{"_id":1, "title":1, "content":1})

    def retrive_comment_data(self, db, collection, object_id):
        self.db = self.client[db]
        self.collection = self.db[collection]
        return self.collection.find({"_id":ObjectId(object_id)},{"_id":1 ,"post_id":1, "content":1})

    def close(self):
        self.client.close()


def count_feature(industry, start_date, end_date, key_gen, limit='30'):
    api_key = key_gen.get_token()
    conn = PlusApi('hot_feature')
    data = dict(
        industry=industry,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        api_key=api_key
        )

    feature_list = conn.post(data=data)
    feature_list = [x.get('feature') for x in feature_list['result']]

    post_list = []
    for feature in feature_list:
        conn = PlusApi('feature_article')
        data = dict(
            industry=industry,
            features=feature,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
            page_num='1'
            )

        post_temp = []
        feature_article = conn.post(data=data)
        while feature_article['result']:
            post_temp += feature_article['result']
            data['page_num'] = str(int(data['page_num'])+1)
            feature_article = conn.post(data=data)
        post_list.append((feature, post_temp))
    return post_list

def count_topic_list(mongo_uri, post_list, product_file, industry, core=10):
    '''
    報表產生主函式 回撈mongo內容進行關鍵字比對並製作內容排名報表
    post_list 為 plus_api 回傳總結的list，其element架構為 (feature=str, post=list(dict))
    product_file 為 公司內部設定檔(xlsx -> pandas.DataFrame)
    industry 為 產業欄位名稱
    core 為 平行運算分配的核心數，作為args導入 par_search類建立

    函式回傳的資料為 pandas.DataFrame表單
    '''
    client = MongoWorker(mongo_uri)
    result_list = []
    par_worker = ParSearch(core)
    feature_rank = 0
    for feature in post_list:
        output_data = pd.DataFrame([], columns=["_id", "post_id", "content", "product", "author", "title", "date", "comment_count"])
        feature_rank += 1
        for post in feature[1]:
            post_data = pd.DataFrame(client.retrive_post_data('Indexasia', 'post', post['post_id']))
            if post_data.empty:
                continue
            post_data['content'] = post_data['title'] + post_data['content']
            post_data = post_data.rename(columns={"title":"post_id"})
            post_data['post_id'] = post_data['_id']
            comment_data = pd.DataFrame(client.retrive_comment_data('Indexasia', 'comment', post['post_id']))
            if comment_data.empty:
                comment_data = pd.DataFrame([], columns=["_id", "post_id", "content"])
            build_data = pd.concat([post_data, comment_data], ignore_index=True)
            build_data = build_data.loc[build_data['content'].apply(lambda x: feature[0] in x)].reset_index(drop=True)
            build_data['product'] = build_data['content'].apply(lambda x: list(product_file.loc[par_worker.search_pro(x, product_file['舊PRO'])]['產品名稱'])) ###
            build_data = build_data.loc[build_data['product'].apply(lambda x: [] != x)].reset_index(drop=True)
            build_data['author'] = post['author']
            build_data['title'] = post['title']
            build_data['date'] = post['date']
            build_data['comment_count'] = post['comment_count']
            build_data['channel'] = post['channel']
            build_data['url'] = post['url']
            output_data = pd.concat([output_data, build_data], ignore_index=True)
        if output_data.empty:
            continue
        output_data['content'] = output_data['content'].apply(lambda x: ILLEGAL_CHARACTERS_RE.sub(r'', x))
        output_data['title'] = output_data['title'].apply(lambda x: ILLEGAL_CHARACTERS_RE.sub(r'', x))
        ranking = pd.Series(np.concatenate(output_data['product']))
        ranking = ranking.value_counts().rename_axis('product').reset_index(name='freq')
        rank_list = []
        count = 0
        for product in ranking['product']:
            count += 1
            if count > 3:
                break
            rank_n = output_data.loc[output_data['product'].apply(lambda x: product in x)].reset_index(drop=True)
            rank_n['product'] = product
            rank_n.drop_duplicates(subset=['post_id'], inplace=True)
            rank_n['sub_count'] = len(rank_n)
            rank_n['rank'] = count
            rank_n.sort_values(by='comment_count', inplace=True, ascending=False, ignore_index=True)
            if rank_n.shape[0] > 3:
                rank_n = rank_n[0:3]
            rank_list.append(rank_n)
        rank_list = pd.concat(rank_list)
        rank_list['industry'] = industry
        rank_list['feature_rank'] = feature_rank
        rank_list['feature'] = feature[0]
        rank_list['apply_date'] = datetime.now().strftime('%Y-%m-01 00:00:00')
        rank_list['_id'] = rank_list['_id'].apply(str)
        rank_list['post_id'] = rank_list['post_id'].apply(str)
        rank_list['title'] = rank_list['title'].apply(lambda x: re.sub(r"\n+", " ", x))
        result_list.append((rank_list, ranking, output_data))
    client.close()
    par_worker.close()
    return result_list

if __name__ == '__main__':
    pass