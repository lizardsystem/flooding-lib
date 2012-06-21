from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_lib.tools.importtool.views.overview',
        name='flooding_tools_import_overview'),

    url(r'^verifyimport/(?P<import_scenario_id>\d+)$',
        'flooding_lib.tools.importtool.views.verify_import',
        name='flooding_tools_import_verify'),

    url(r'^newimport/$',
        'flooding_lib.tools.importtool.views.new_import',
        name='flooding_tools_import_new'),

    url(r'^approveimport/(?P<import_scenario_id>\d+)$',
        'flooding_lib.tools.importtool.views.approve_import',
        name='flooding_tools_import_approve'),

    url(r'^groupimport/$',
        'flooding_lib.tools.importtool.views.group_import',
        name='flooding_tools_import_group'),

    url(r'^groupimport/download_example_csv$',
        'flooding_lib.tools.importtool.views.group_import_example_csv',
        name='flooding_tools_import_group_download_csv'),

    url(r'^newimport/(?P<import_scenario_id>\d+)/uploadfiles$',
        'flooding_lib.tools.importtool.views.upload_import_scenario_files',
        name='flooding_tools_upload_files'),

)
