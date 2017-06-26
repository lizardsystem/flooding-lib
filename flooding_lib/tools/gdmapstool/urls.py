from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_lib.tools.gdmapstool.views.index',
        name='flooding_gdmaapstool_index'),

    url(r'^gdmapdetail/(?P<gdmap_id>\d+)$',
        'flooding_lib.tools.gdmapstool.views.gdmap_details',
        name='flooding_gdmapstool_mapdetails'),

    url(r'^reusegdmap/(?P<gdmap_id>\d+)$',
        'flooding_lib.tools.gdmapstool.views.reuse_gdmap',
        name='flooding_gdmapstool_reuse_gdmap'),

    url(r'^loadgdmapform/(?P<gdmap_id>\d+)/$',
        'flooding_lib.tools.gdmapstool.views.load_gdmap_form',
        name='flooding_tools_gdmap_load_form'),

    url(r'^savegdmapform/$',
        'flooding_lib.tools.gdmapstool.views.save_gdmap_form',
        name='flooding_tools_gdmap_save_form'),
)
