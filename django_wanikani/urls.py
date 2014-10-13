from django.conf.urls import patterns, include, url
from django.contrib import admin

from django_wanikani.views import WaniKaniView

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'django_wanikani.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^(?P<api_key>\w+)', WaniKaniView.as_view()),
)
