import collections
import datetime
import json
import logging

import requests

logger = logging.getLogger(__name__)

__all__ = ['WaniKani', 'Radical', 'Kanji', 'Vocabulary']

WANIKANI_BASE = 'https://www.wanikani.com/api/v1.2/user/{0}/{1}'


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

    @property
    def unlocked(self):
        return self.raw['user_specific']['unlocked_date']

    @property
    def burned(self):
        if self.raw['user_specific']['burned']:
            return self.raw['user_specific']['burned_date']
        return None

    @property
    def srs(self):
        try:
            return self.raw['user_specific']['srs']
        except TypeError:
            # Likely an object that has not been learned yet
            return None

    def __getitem__(self, key):
        if key in self.raw:
            return self.raw[key]
        return self.raw['user_specific'][key]

    def __unicode__(self):
        return self.raw['character']

    def __str__(self):
        try:
            return self.raw['character'].encode('utf8')
        except AttributeError:
            # Certain Radicals do not have a utf8 representation
            return '?'.encode('utf8')


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
        self.session = requests.Session()

    def profile(self):
        url = WANIKANI_BASE.format(self.api_key, 'user-information')
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)
        return data['user_information']

    def level_progress(self):
        url = WANIKANI_BASE.format(self.api_key, 'level-progression')
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)
        merged = data['requested_information']
        merged['user_information'] = data['user_information']
        return merged

    def recent_unlocks(self, limit=10):
        url = WANIKANI_BASE.format(self.api_key, 'recent-unlocks')
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)

        mapping = {
            'vocabulary': Vocabulary,
            'kanji': Kanji,
            'radical': Radical,
        }

        for item in data['requested_information']:
            klass = mapping[item['type']]
            yield klass(item)

    def radicals(self, levels=None):
        """
        :param levels string: An optional argument of declaring a single or
            comma-delimited list of levels is available, as seen in the example
            as 1. An example of a comma-delimited list of levels is 1,2,5,9.

        http://www.wanikani.com/api/v1.2#radicals-list
        """
        url = WANIKANI_BASE.format(self.api_key, 'radicals')
        if levels:
            url += '/{0}'.format(levels)
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)

        for item in data['requested_information']:
            yield Radical(item)

    def kanji(self, levels=None):
        """
        :param levels: An optional argument of declaring a single or
            comma-delimited list of levels is available, as seen in the example
            as 1. An example of a comma-delimited list of levels is 1,2,5,9.
        :type levels: str or None

        http://www.wanikani.com/api/v1.2#kanji-list
        """
        url = WANIKANI_BASE.format(self.api_key, 'kanji')
        if levels:
            url += '/{0}'.format(levels)
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)

        for item in data['requested_information']:
            yield Kanji(item)

    def vocabulary(self, levels=None):
        """
        :param levels: An optional argument of declaring a single or
            comma-delimited list of levels is available, as seen in the example
            as 1. An example of a comma-delimited list of levels is 1,2,5,9.
        :type levels: str or None

        http://www.wanikani.com/api/v1.2#vocabulary-list
        """
        url = WANIKANI_BASE.format(self.api_key, 'vocabulary')
        if levels:
            url += '/{0}'.format(levels)
        result = self.session.get(url)
        result.raise_for_status()
        data = json.loads(result.text)

        if 'general' in data['requested_information']:
            for item in data['requested_information']['general']:
                yield Vocabulary(item)
        else:
            for item in data['requested_information']:
                yield Vocabulary(item)

    def upcoming(self, levels=None):
        """
        Return mapping of upcoming items

        :param levels: An optional argument of declaring a single or
            comma-delimited list of levels is available, as seen in the example
            as 1. An example of a comma-delimited list of levels is 1,2,5,9.
        :type levels: str or None
        :return: Returns dictionary of items with datetime as the key
        """
        return self.query(levels, exclude=[u'burned'])

    def burning(self):
        return self.query(include=[u'enlighten'])

    def query(self, levels=None, items=[Radical, Kanji, Vocabulary], exclude=[], include=[]):
        mapping = {
            Radical: self.radicals,
            Kanji: self.kanji,
            Vocabulary: self.vocabulary
        }

        queue = collections.defaultdict(list)
        for klass in items:
            for obj in mapping[klass](levels):
                if exclude and obj.srs in exclude:
                    continue
                if include and obj.srs not in include:
                    continue
                if obj.next_review:
                    queue[obj.next_review].append(obj)
        return queue
