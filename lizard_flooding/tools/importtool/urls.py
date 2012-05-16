from django.conf.urls.defaults import *

urlpatterns = patterns(
    '',

    url(r'^$',
        'lizard_flooding.tools.importtool.views.overview',
        name='flooding_tools_import_overview'),

    url(r'^verifyimport/(?P<import_scenario_id>\d+)$',
        'lizard_flooding.tools.importtool.views.verify_import',
        name='flooding_tools_import_verify'),

    url(r'^newimport/$',
        'lizard_flooding.tools.importtool.views.new_import',
        name='flooding_tools_import_new'),

    url(r'^approveimport/(?P<import_scenario_id>\d+)$',
        'lizard_flooding.tools.importtool.views.approve_import',
        name='flooding_tools_import_approve'),

    url(r'^groupimport/$',
        'lizard_flooding.tools.importtool.views.group_import',
        name='flooding_tools_import_group'),

    url(r'^groupimport/download_example_csv$',
        'lizard_flooding.tools.importtool.views.group_import_example_csv',
        name='flooding_tools_import_group_download_csv'),

    url(r'^newimport/(?P<import_scenario_id>\d+)/uploadfiles$',
        'lizard_flooding.tools.importtool.views.upload_import_scenario_files',
        name='flooding_tools_upload_files'),

)
