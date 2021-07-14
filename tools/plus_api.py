# -*- coding: utf8 -*-
import requests

class MoreToken(object):
    uri = "https://ser.kong.srm.pw/dashboard/token/authorize"

    def __init__(self, email, clientId):
        self.email = email
        self.clientId = clientId

    def get_token(self):
        response = requests.post(self.uri, json={"email":self.email, "clientId":self.clientId})
        self.token = response.json()['accessToken']
        return self.token

class PlusApi(object):
    api_dict = dict(
        total_count="https://www.more.org.tw/voc/industry/total-count.jsp",
        article_list="https://www.more.org.tw/voc/industry/article-list.jsp",
        hot_feature="https://www.more.org.tw/voc/industry/hot-feature.jsp",
        feature_article="https://www.more.org.tw/voc/industry/feature-article-list.jsp"
    )

    def __init__(self, api):
        self.api = api
        self.uri = self.api_dict.get(api)

    def post(self, data):
        response = requests.post(self.uri, data=data)
        return response.json()


if __name__ == '__main__':
    pass