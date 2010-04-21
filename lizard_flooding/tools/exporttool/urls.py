from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^$',
        'lizard_flooding.tools.exporttool.views.index',
        name='flooding_tools_export_index'),

    url(r'^exportdetail/(?P<export_run_id>\d+)$',
        'lizard_flooding.tools.exporttool.views.export_detail',
        name='flooding_tools_export_detail'),

    url(r'^exportdetailscenarios/(?P<export_run_id>\d+)$',
        'lizard_flooding.tools.exporttool.views.export_detail_scenarios',
        name='flooding_tools_export_detail_scenarios'),

    url(r'^newexportindex/$',
        'lizard_flooding.tools.exporttool.views.new_export_index',
        name='flooding_tools_export_new_export_index'),

    url(r'^newexport/$',
        'lizard_flooding.tools.exporttool.views.new_export',
        name='flooding_tools_export_new_export'),
)
