import collections
import datetime
import json
import logging

import requests

logger = logging.getLogger(__name__)

__all__ = ['WaniKani', 'Radical', 'Kanji', 'Vocabulary']

WANIKANI_BASE = 'https://www.wanikani.com/api/v1.4/user/{0}/{1}'


def split(func):
    # From http://stackoverflow.com/a/21767522/622650
    def iter_baskets_contiguous(items, maxbaskets=3, item_count=None):
        '''
        generates balanced baskets from iterable, contiguous contents
        provide item_count if providing a iterator that doesn't support len()
        '''
        item_count = int(item_count or len(items))
        baskets = min(item_count, maxbaskets)
        items = iter(items)
        floor = int(item_count // baskets)
        ceiling = floor + 1
        stepdown = item_count % baskets
        for x_i in range(int(baskets)):
            length = ceiling if x_i < stepdown else floor
            yield [next(items) for _ in range(length)]

    def wrapper(self, levels):
        # If levels is None, then we're getting all levels for the user
        # and may need to split it up into multiple queries to avoid timeouts
        if levels is None:
            logger.debug('Splitting levels %s', levels)
            level = self.profile()['level']
            step = level / 10
            for basket in iter_baskets_contiguous(range(1, level + 1), step):
                logger.debug('Loading chunk %s', basket)
                for item in func(self, ','.join([str(i) for i in basket])):
                    yield item
        else:
            for item in func(self, levels):
                yield item
    return wrapper


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

    @property
    def srs_numeric(self):
        try:
            return self.raw['user_specific']['srs_numeric']
        except (AttributeError, TypeError):
            return 0

    def __getitem__(self, key):
        if key in self.raw:
            return self.raw[key]
        if self.raw['user_specific'] is not None:
            return self.raw['user_specific'][key]

    def __str__(self):
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
    def __str__(self):
        return '{0} [{1}]'.format(self.raw['character'], self.raw['kana'])

    def __repr__(self):
        return '<Vocabulary: {0}>'.format(self.raw['character'].encode('utf8'))


class WaniKani(object):
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def get(self, *args, **kwargs):
        result = self.session.get(*args, **kwargs)
        result.raise_for_status()
        return result.json

    def profile(self):
        url = WANIKANI_BASE.format(self.api_key, 'user-information')
        data = self.get(url)
        return data['user_information']

    def level_progress(self):
        url = WANIKANI_BASE.format(self.api_key, 'level-progression')
        data = self.get(url)
        merged = data['requested_information']
        merged['user_information'] = data['user_information']
        return merged

    def recent_unlocks(self, limit=10):
        url = WANIKANI_BASE.format(self.api_key, 'recent-unlocks')
        data = self.get(url)

        mapping = {
            'vocabulary': Vocabulary,
            'kanji': Kanji,
            'radical': Radical,
        }

        for item in data['requested_information']:
            klass = mapping[item['type']]
            yield klass(item)

    def critical_items(self, percentage=75):
        url = WANIKANI_BASE.format(self.api_key, 'critical-items')
        if percentage:
            url += '/{0}'.format(percentage)
        data = self.get(url)

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
        data = self.get(url)

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
        data = self.get(url)

        for item in data['requested_information']:
            yield Kanji(item)

    @split
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
        data = self.get(url)

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
