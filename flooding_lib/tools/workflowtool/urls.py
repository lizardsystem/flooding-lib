from django.conf.urls.defaults import patterns, url
from flooding_lib.tools.workflowtool.views import (
    ScenarioWorkflowView, CountPagesView)
from flooding_lib.tools.workflowtool.views import execute_scenario


urlpatterns = patterns(
    '',

    url(r'^$',
        'flooding_lib.tools.workflowtool.views.index',
        name='flooding_tools_workflow_index'),
    url(r'^scenarios_processing/$', ScenarioWorkflowView.as_view(),
        name="workflow_scenarios_processing"),
    url(r'^workflow_context/$', CountPagesView.as_view(),
        name="workflow_last_pagenumber"),
    url(r'^start_scenario/$', 
        'flooding_lib.tools.workflowtool.views.execute_scenario',
        name="workflow_start_scenario"),
    url(r'^start_scenarios/$',
        'flooding_lib.tools.workflowtool.views.execute_scenarios',
        name="workflow_start_scenarios"),
    url(r'^rowstoselect/$',
        'flooding_lib.tools.workflowtool.views.rowstoload_options',
        name='workflow_tools_rowstoload'),
)
