import json
import logging

import requests

logger = logging.getLogger(__name__)

__all__ = ['WaniKani']

WANIKANI_BASE = 'http://www.wanikani.com/api/user/{0}/{1}'


class WaniKani(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def profile(self):
        url = WANIKANI_BASE.format(self.api_key, 'user-information')
        result = requests.get(url)
        data = json.loads(result.text)
        return data['user_information']

    def level_progress(self):
        url = WANIKANI_BASE.format(self.api_key, 'level-progression')
        result = requests.get(url)
        data = json.loads(result.text)
        merged = data['requested_information']
        merged['user_information'] = data['user_information']
        return merged
