import collections
import datetime
import json
import logging

import requests

logger = logging.getLogger(__name__)

__all__ = ['WaniKani', 'Radical', 'Kanji', 'Vocabulary']

WANIKANI_BASE = 'http://www.wanikani.com/api/v1.2/user/{0}/{1}'


class BaseObject(object):
    def __init__(self, raw):
        self.raw = raw

    @property
    def next_review(self):
        if self.raw['user_specific'] is None:
            return None
        return datetime.datetime.fromtimestamp(
            self.raw['user_specific']['available_date']
            )

    def __unicode__(self):
        return self.raw['character']


class Radical(BaseObject):
    def __repr__(self):
        if self.raw['character']:
            return '<Radical: {0}>'.format(self.raw['character'].encode('utf8'))
        # Some characters do not have a unicode representation
        return '<Radical: No Unicode>'


class Kanji(BaseObject):
    def __repr__(self):
        return '<Kanji: {0}>'.format(self.raw['character'].encode('utf8'))


class Vocabulary(BaseObject):
    def __unicode__(self):
        return '{0} [{1}]'.format(self.raw['character'], self.raw['kana'])

    def __repr__(self):
        return '<Vocabulary: {0}>'.format(self.raw['character'].encode('utf8'))


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

    def recent_unlocks(self, limit=10):
        url = WANIKANI_BASE.format(self.api_key, 'recent-unlocks')
        result = requests.get(url)
        data = json.loads(result.text)

        return {
            'items': data['requested_information'],
            'user_information': data['user_information'],
        }

    def radicals(self, levels=None):
        url = WANIKANI_BASE.format(self.api_key, 'radicals')
        result = requests.get(url)
        data = json.loads(result.text)

        for item in data['requested_information']:
            yield Radical(item)

    def kanji(self, levels=None):
        url = WANIKANI_BASE.format(self.api_key, 'kanji')
        result = requests.get(url)
        data = json.loads(result.text)

        for item in data['requested_information']:
            yield Kanji(item)

    def vocabulary(self, levels=None):
        url = WANIKANI_BASE.format(self.api_key, 'vocabulary')
        result = requests.get(url)
        data = json.loads(result.text)

        for item in data['requested_information']['general']:
            yield Vocabulary(item)

    def upcoming(self):
        queue = collections.defaultdict(list)

        mapping = {
            Radical: self.radicals,
            Kanji: self.kanji,
            Vocabulary: self.vocabulary
        }

        for klass in mapping:
            for obj in mapping[klass]():
                if obj.next_review:
                    queue[obj.next_review].append(obj)
        return queue
