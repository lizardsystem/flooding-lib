from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_lib.tools.exporttool.views.index',
        name='flooding_tools_export_index'),

    url(r'^exportdetail/(?P<export_run_id>\d+)$',
        'flooding_lib.tools.exporttool.views.export_detail',
        name='flooding_tools_export_detail'),

    url(r'^exportdetailscenarios/(?P<export_run_id>\d+)$',
        'flooding_lib.tools.exporttool.views.export_detail_scenarios',
        name='flooding_tools_export_detail_scenarios'),

    url(r'^newexportindex/$',
        'flooding_lib.tools.exporttool.views.new_export_index',
        name='flooding_tools_export_new_export_index'),

    url(r'^newexport/$',
        'flooding_lib.tools.exporttool.views.new_export',
        name='flooding_tools_export_new_export'),

    url(r'^reuseexport/(?P<export_run_id>\d+)$',
        'flooding_lib.tools.exporttool.views.reuse_export',
        name='flooding_tools_reuse_export'),

    url(r'^reuseexport/(?P<export_run_id>\w+)/scenarios$',
        'flooding_lib.tools.exporttool.views.export_run_scenarios',
        name='flooding_tools_reuse_export_scenarios'),
)
