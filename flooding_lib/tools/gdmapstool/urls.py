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

    # url(r'^exportdetail/(?P<export_run_id>\d+)$',
    #     'flooding_lib.tools.exporttool.views.export_detail',
    #     name='flooding_tools_export_detail'),

    # url(r'^exportdetailscenarios/(?P<export_run_id>\d+)$',
    #     'flooding_lib.tools.exporttool.views.export_detail_scenarios',
    #     name='flooding_tools_export_detail_scenarios'),

    # url(r'exportdetail/(?P<export_run_id>\d+)/togglearchive/$',
    #     'flooding_lib.tools.exporttool.views.toggle_archived_export',
    #     name='flooding_tools_archive_export'),

    # url(r'exportdetail/(?P<export_run_id>\d+)/delete/$',
    #     'flooding_lib.tools.exporttool.views.delete_archived_export',
    #     name='flooding_tools_delete_export'),

    # url(r'^newexportindex/$',
    #     'flooding_lib.tools.exporttool.views.new_export_index',
    #     name='flooding_tools_export_new_export_index'),

    # url(r'^newexport/$',
    #     'flooding_lib.tools.exporttool.views.new_export',
    #     name='flooding_tools_export_new_export'),

    # url(r'^loadexportform/(?P<export_run_id>\d+)/$',
    #     'flooding_lib.tools.exporttool.views.load_export_form',
    #     name='flooding_tools_export_load_export_form'),

    # url(r'^reuseexport/(?P<export_run_id>\d+)$',
    #     'flooding_lib.tools.exporttool.views.reuse_export',
    #     name='flooding_tools_reuse_export'),

    # url(r'^reuseexport/(?P<export_run_id>\w+)/scenarios$',
    #     'flooding_lib.tools.exporttool.views.export_run_scenarios',
    #     name='flooding_tools_reuse_export_scenarios'),
)
