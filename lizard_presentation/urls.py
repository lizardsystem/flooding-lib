# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^service/$',
        'lizard_presentation.views.uber_service',
        name='presentation'),

    url(r'^permissions/$',
        'lizard_presentation.views.overview_permissions',
        name='presentation_permissions'),
)
