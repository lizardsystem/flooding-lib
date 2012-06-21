from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_lib.tools.views.index',
        name='flooding_tools'),

    url(r'^export/',
        include('flooding_lib.tools.exporttool.urls')),

    url(r'^import/',
        include('flooding_lib.tools.importtool.urls')),

    url(r'^approval/',
        include('flooding_lib.tools.approvaltool.urls')),

)
