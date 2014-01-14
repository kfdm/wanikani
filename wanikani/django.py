from __future__ import absolute_import

import os
import logging

from django.http import HttpResponse
from django.views.generic.base import View


from icalendar import Calendar, Event

from wanikani.core import WaniKani, Radical, Kanji

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.wanikani')

with open(CONFIG_PATH) as fp:
    API_KEY = fp.read()

logger = logging.getLogger(__name__)


class WaniKaniView(View):
    def get(self, request, *args, **kwargs):
        client = WaniKani(API_KEY)

        level = client.profile()['level']
        queue = client.upcoming(level)

        cal = Calendar()
        cal.add('prodid', '-//My calendar product//mxm.dk//')
        cal.add('version', '2.0')

        for ts in sorted(queue):
            if not len(queue[ts]):
                continue

            counts = {
                Radical: 0,
                Kanji: 0,
            }

            for obj in queue[ts]:
                if obj.srs != u'apprentice':
                    continue
                if isinstance(obj, Radical):
                    counts[Radical] += 1
                if isinstance(obj, Kanji):
                    counts[Kanji] += 1

            if counts[Radical] == 0 and counts[Kanji] == 0:
                continue

            event = Event()
            event.add('summary', 'R: {0} K: {1}'.format(
                counts[Radical], counts[Kanji]
            ))
            event.add('dtstart', ts)
            event.add('dtend', ts)
            event['uid'] = str(ts)

            cal.add_component(event)

        return HttpResponse(
            content=cal.to_ical(),
            content_type='text/plain; charset=utf-8'
        )
