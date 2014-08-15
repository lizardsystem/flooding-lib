from django.conf.urls import patterns
from django.conf.urls import include
from django.conf.urls import url
from django.conf import settings

from django.contrib import admin

admin.autodiscover()

config_pattern = r'^service/configuration/(?P<configuration_id>\d+)'
filter_pattern = config_pattern + r'/filter/(?P<filter_id>[_A-Za-z0-9]*)/'

urlpatterns = patterns(
    '',
    # The old lizard.base urls that were previously mounted under /service.
    # We now mount them there directly.
    url(r'^service/$',
        'flooding_base.views.service_uberservice',
        name='base_service_uberservice'),

    url(r'^service/configuration/$',
        'flooding_base.views.service_get_configurations',
        name='base_service_get_configurations'),

    url(config_pattern + r'/filter/$',
        'flooding_base.views.service_get_filters',
        name='base_service_get_filters'),

    url(filter_pattern + r'location/$',
        'flooding_base.views.service_get_locations',
        name='base_service_get_locations'),

    url(filter_pattern + r'parameter/$',
        'flooding_base.views.service_get_parameters',
        name='base_service_get_parameters'),

    url(config_pattern + r'/location/(?P<location_id>[_/A-Za-z0-9]*)/$',
        'flooding_base.views.service_get_location',
        name='base_service_get_location'),

    url(config_pattern + r'/timeseries/$',
        'flooding_base.views.service_get_timeseries',
        name='base_service_get_timeseries'),

    # URLs that were previously defined in the old lizard root urls.py but
    # that have to do with base.

    url(r'^$',
        'flooding_base.views.gui',
        name='root_url'),

    url(r'^get_config.js$',
        'flooding_base.views.gui_config',
        name='gui_config'),

    url(r'^get_translated_strings.js$',
        'flooding_base.views.gui_translated_strings',
        name='gui_translated_strings'),

    url(r'^admin/(.*)', include(admin.site.urls)),

    url(r'^help/$',
        'flooding_base.views.help',
        name='help_url'),

    url(r'^userconfiguration/$',
        'flooding_base.views.userconfiguration',
        name='userconfiguration_url'),

    url(r'^base/testdatabase/$',
        'flooding_base.views.testdatabase_list',
        name='testdatabase_list',
        ),

    url(r'^base/testdatabase/(?P<configuration_id>\d+)/$',
        'flooding_base.views.testdatabase',
        name='testdatabase_detail'),

    url(r'^accounts/login/$',
         'django.contrib.auth.views.login',
        #{'template_name': 'registration/login.html'},
        name='login_url'),

    url(r'^accounts/logout/$',
        'django.contrib.auth.views.logout',
        name='logout_url'),

    url(r'^accounts/password_change/$',
        'django.contrib.auth.views.password_change',
        name='password_change_url'),

    url(r'^accounts/password_change_done/$',
        'django.contrib.auth.views.password_change_done'),


    )


if settings.DEBUG:
    # Add this also to the projects that use this application.
    urlpatterns += patterns('',
        (r'', include('django.contrib.staticfiles.urls')),
    )
