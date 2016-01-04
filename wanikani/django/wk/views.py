# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections
import logging

from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
from icalendar import Calendar, Event
from django.core.cache import cache
from wanikani.core import Kanji, Radical, WaniKani


logger = logging.getLogger(__name__)

class ApiForm(forms.Form):
    api_key = forms.CharField(max_length=32)


class CachedWaniKani(WaniKani):
    def get(self, url, *args, **kwargs):
        result = cache.get(url)
        if result is not None:
            logger.info('Found cache for %s', url)
            return result
        result = self.session.get(url, *args, **kwargs)
        result.raise_for_status()
        data = result.json()
        logger.info('Caching for %s', url)
        cache.set(url, data)
        return data

class MainMenu(View):
    def post(self, request):
        form = ApiForm(request.POST)
        if form.is_valid():
            request.session['api_key'] = form.cleaned_data['api_key']

        return self.get(request)

    def get(self, request):
        form = ApiForm()
        if request.session.get('api_key'):
            return render(request, 'main.html', {
                'api_key': request.session.get('api_key'),
                'form': form,
            })
        else:
            return render(request, 'login.html', {'form': form})


class Dashboard(View):
    def get(self, request):
        client = CachedWaniKani(request.session.get('api_key'))


class BlockersCalendar(View):
    '''
    Calendar to graph all the blockers for the next level
    '''
    def get(self, request, **kwargs):
        client = CachedWaniKani(kwargs['api_key'])

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
            content_type='text/calendar; charset=utf-8'
        )


class ReviewsCalendar(View):
    '''
    Show the number of reviews for that day
    '''
    def get(self, request, **kwargs):
        client = CachedWaniKani(kwargs['api_key'])
        queue = client.upcoming()

        cal = Calendar()
        cal.add('prodid', '-//Wanikani Reviews//github.com/kfdm/django-wanikani//')
        cal.add('version', '2.0')

        newqueue = collections.defaultdict(list)
        for ts in list(queue.keys()):
            newts = ts.date()
            newqueue[newts] += queue.pop(ts)
        queue = newqueue

        for ts in sorted(queue):
            if not len(queue[ts]):
                continue

            event = Event()
            event.add('summary', '復習 {0}'.format(len(queue[ts])))
            event.add('dtstart', ts)
            cal.add_component(event)

        return HttpResponse(
            content=cal.to_ical(),
            content_type='text/calendar; charset=utf-8'
        )
