# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^service/$',
        'lizard.presentation.views.uber_service',
        name='presentation'),

    url(r'^permissions/$',
        'lizard.presentation.views.overview_permissions',
        name='presentation_permissions'),
)
