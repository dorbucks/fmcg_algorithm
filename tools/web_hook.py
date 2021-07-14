# -*- coding: utf8 -*-
import requests
import json

class TeamsHook(object):
    def __init__(self, hook_uri):
        self.hook_uri = hook_uri

    def post_text(self, text):
        requests.post(self.hook_uri, data=json.dumps({'text':text}))

if __name__ == '__main__':
    pass
