# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns(
    '',

    url(r'^$',
        'lizard.visualization.views.uber_service',
        name='visualization'),

    url(r'^symbol/(?P<symbol>.*)$',
        'lizard.visualization.views.get_symbol',
        name='visualization_symbol'),

    url(r'^legend/$',
        'lizard.visualization.views.legend_shapedata',
        name='visualization_legend'),

    url(r'^testmapping/$',
        'lizard.visualization.views.testmapping',
        name='visualization_testmapping'),

    url(r'^test_mpl/$',
        'lizard.visualization.views_dev.test_mpl'),


)
