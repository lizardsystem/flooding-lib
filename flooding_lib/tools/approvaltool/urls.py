from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'table/(?P<approvalobject_id>\d+)$',
        'flooding_lib.tools.approvaltool.views.approvaltable_page',
        name='flooding_tools_approval_table'
        ),


)
