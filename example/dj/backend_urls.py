from distutils.version import StrictVersion

import django

from django.conf.urls import re_path as url

from test_chamber import views  # pylint: disable=E0401


if StrictVersion(django.get_version()) < StrictVersion('1.9'):
    from django.conf.urls import patterns

    urlpatterns = patterns(
        '',
        url(r'^current_time_backend/$', views.current_datetime, name='current-datetime')
    )
else:
    urlpatterns = [
        url(r'^current_time_backend/$', views.current_datetime, name='current-datetime')
    ]
