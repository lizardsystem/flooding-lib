# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^service/$',
        'flooding_presentation.views.uber_service',
        name='presentation'),

    url(r'^permissions/$',
        'flooding_presentation.views.overview_permissions',
        name='presentation_permissions'),
)
