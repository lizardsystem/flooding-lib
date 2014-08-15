# -*- coding: utf-8 -*-
from django.conf.urls import *


urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_visualization.views.uber_service',
        name='visualization'),

    url(r'^symbol/(?P<symbol>.*)$',
        'flooding_visualization.views.get_symbol',
        name='visualization_symbol'),

    url(r'^legend/$',
        'flooding_visualization.views.legend_shapedata',
        name='visualization_legend'),

    url(r'^testmapping/$',
        'flooding_visualization.views.testmapping',
        name='visualization_testmapping'),
)
