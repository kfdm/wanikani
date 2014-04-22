# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.http import HttpResponse
from django.views.generic.base import View


from icalendar import Calendar, Event

from wanikani.core import WaniKani, Radical, Kanji


class WaniKaniView(View):
    def get(self, request, **kwargs):
        client = WaniKani(kwargs['api_key'])

        level = client.profile()['level']
        queue = client.query(level, items=[Radical, Kanji], include=[u'apprentice'])

        cal = Calendar()
        cal.add('prodid', '-//Wanikani Blockers//github.com/kfdm/wanikani//')
        cal.add('version', '2.0')

        for ts in sorted(queue):
            if not len(queue[ts]):
                continue

            counts = {
                Radical: 0,
                Kanji: 0,
            }

            for obj in queue[ts]:
                counts[obj.__class__] += 1

            event = Event()
            if counts[Radical] and counts[Kanji]:
                event.add('summary', u'部首: {0} 漢字: {1}'.format(
                    counts[Radical], counts[Kanji]
                ))
            elif counts[Radical]:
                event.add('summary', u'部首: {0}'.format(
                    counts[Radical]
                ))
            else:
                event.add('summary', u'漢字: {0}'.format(
                    counts[Kanji]
                ))
            event.add('dtstart', ts)
            event.add('dtend', ts)
            event['uid'] = str(ts)

            cal.add_component(event)

        return HttpResponse(
            content=cal.to_ical(),
            content_type='text/plain; charset=utf-8'
        )
