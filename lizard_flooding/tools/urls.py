from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^$',
        'lizard_flooding.tools.views.index',
        name='flooding_tools'),

    url(r'^export/',
        include('lizard_flooding.tools.exporttool.urls')),

    url(r'^import/',
        include('lizard_flooding.tools.importtool.urls')),

    url(r'^approval/',
        include('lizard_flooding.tools.approvaltool.urls')),

)
