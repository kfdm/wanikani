from django.conf.urls import patterns, url

from django_wanikani.views import BlockersCalendar, ReviewsCalendar, MainMenu

urlpatterns = patterns(
    '',
    url(r'^$', MainMenu.as_view()),
    url(r'^calendars/(?P<api_key>\w+)/blocker.ics', BlockersCalendar.as_view(), name='blockers'),
    url(r'^calendars/(?P<api_key>\w+)/reviews.ics', ReviewsCalendar.as_view(), name='reviews'),
)
