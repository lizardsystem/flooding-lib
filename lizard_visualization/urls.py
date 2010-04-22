# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns(
    '',

    url(r'^$',
        'lizard_visualization.views.uber_service',
        name='visualization'),

    url(r'^symbol/(?P<symbol>.*)$',
        'lizard_visualization.views.get_symbol',
        name='visualization_symbol'),

    url(r'^legend/$',
        'lizard_visualization.views.legend_shapedata',
        name='visualization_legend'),

    url(r'^testmapping/$',
        'lizard_visualization.views.testmapping',
        name='visualization_testmapping'),

    # url(r'^test_mpl/$',
    #     'lizard_visualization.views_dev.test_mpl'),


)
