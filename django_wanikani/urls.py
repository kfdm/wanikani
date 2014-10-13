from django.conf.urls import patterns, include, url
from django.contrib import admin

from django_wanikani.views import BlockersCalendar, ReviewsCalendar

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'django_wanikani.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^calendars/(?P<api_key>\w+)/blocker.ics', BlockersCalendar.as_view(), name='blockers'),
    url(r'^calendars/(?P<api_key>\w+)/reviews.ics', ReviewsCalendar.as_view(), name='reviews'),
)
