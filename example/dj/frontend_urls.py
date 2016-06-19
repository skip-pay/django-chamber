import django

from django.conf.urls import url

from test_chamber import views


if django.get_version() < '1.9':
    from django.conf.urls import patterns

    urlpatterns = patterns(
        '',
        url(r'^current_time_frontend/$', views.current_datetime, name='current-datetime')
    )
else:
    urlpatterns = [
        url(r'^current_time_frontend/$', views.current_datetime, name='current-datetime')
    ]