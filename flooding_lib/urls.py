from django.conf.urls.defaults import patterns, url, include
from django.conf import settings
from django.contrib import databrowse

from flooding_lib import views
from flooding_lib.views import pages
from flooding_lib.models import Project
import flooding_lib.sharedproject.urls

info_dict = {
    'queryset': Project.objects.all(),
}


urlpatterns = patterns(
    '',
    url(r'^$',
        'flooding_lib.views.index',
        name='flooding'),


    url(r'^tools/',
        include('flooding_lib.tools.urls')),

    url(r'^project/$',
        'flooding_lib.views.project_list',
        name='flooding_projects_url'),

    url(r'^project/add/$',
        'flooding_lib.views.project_addedit',
        name='flooding_project_add'),

    url(r'^project/(?P<object_id>\d+)/$',
        'flooding_lib.views.project',
        name='flooding_project_detail'),

    url(r'^project/(?P<object_id>\d+)/edit/$',
        'flooding_lib.views.project_addedit',
        name='flooding_project_edit'),

    url(r'^project/(?P<object_id>\d+)/delete/$',
        'flooding_lib.views.project_delete',
        name='flooding_project_delete'),

    url(r'^scenario/$',
        'flooding_lib.views.scenario_list',
        name='flooding_scenarios_url'),

    url(r'^scenario/add/$',
        'flooding_lib.views.scenario_addedit',
        name='flooding_scenario_add'),

    url(r'^scenario/share/$',
        'flooding_lib.scenario_sharing.list_view',
        name='flooding_scenario_share_list'),

    url(r'^scenario/share/(?P<project_id>\d+)/$',
        'flooding_lib.scenario_sharing.list_project_view',
        name='flooding_scenario_share_project_list'),

    url(r'^scenario/share/action/$',
        'flooding_lib.scenario_sharing.action_view',
        name='flooding_scenario_share_action'),

    url(r'^scenario/(?P<object_id>\d+)/$',
        'flooding_lib.views.scenario',
        name='flooding_scenario_detail'),

    url(r'^scenario/(?P<object_id>\d+)/edit/$',
        'flooding_lib.views.scenario_addedit',
        name='flooding_scenario_edit'),

    url(r'^scenario/(?P<object_id>\d+)/editnameremarks/$',
        'flooding_lib.views.scenario_editnameremarks',
        name='flooding_scenario_editnameremarks'),

    url(r'^scenario/(?P<object_id>\d+)/delete/$',
        'flooding_lib.views.scenario_delete',
        name='flooding_scenario_delete'),

    url(r'^scenario/(?P<scenario_id>\d+)/addcutofflocation/$',
        'flooding_lib.views.scenario_cutofflocation_add',
        name='flooding_scenario_cutofflocation_add'),

    url(r'^scenariocutofflocation/(?P<object_id>\d+)/delete/$',
        'flooding_lib.views.scenario_cutofflocation_delete',
        name='flooding_scenario_cutofflocation_delete'),

    url(r'^scenario/(?P<scenario_id>\d+)/addbreach/$',
        'flooding_lib.views.scenario_breach_add',
        name='flooding_scenario_breach_add'),

    url(r'^scenariobreach/(?P<object_id>\d+)/delete/$',
        'flooding_lib.views.scenario_breach_delete',
        name='flooding_scenario_breach_delete'),

    url(r'^infowindow/$',
        'flooding_lib.views.infowindow.infowindow',
        name='infowindow'),

    url(r'^fractal/$',
        'flooding_lib.views.fractal'),

    url(r'^result/$',
        'flooding_lib.views.result_list',
        name='flooding_result_list'),

    # Note -- no $ at the end! There is a file name there, which we
    # ignore. It's only there so that the downloading web browser
    # knows what to call the file.
    url(r'^result_download/(?P<result_id>\d+)/',
        'flooding_lib.views.result_download',
        name='result_download'),

    url(r'^task/$',
        'flooding_lib.views.task_list',
        name='flooding_task_list'),

    url(r'^task/(?P<object_id>\d+)/$',
        'flooding_lib.views.task',
        name='flooding_task_detail'),

    url(r'^service/$',
        'flooding_lib.services.service',
        name='flooding_service'),

    url(r'^service/project/$',
        'flooding_lib.services.service_get_projects',
        name='flooding_service_get_projects'),

    url(r'^service/project/(?P<project_id>\d+)/scenarios/$',
        'flooding_lib.services.service_get_scenarios_from_project',
        name='flooding_service_get_scenarios_from_project'),

    url(r'^service/scenario/$',
        'flooding_lib.services.service_get_scenarios',
        name='flooding_service_get_scenarios'),

    url(r'^service/regionset/$',
        'flooding_lib.services.service_get_regionsets',
        name='flooding_service_get_regionsets'),

    url(r'^service/region/$',
        'flooding_lib.services.service_get_all_regions',
        name='flooding_service_get_all_regions'),

    url(r'^service/region/(?P<region_id>\d+)/breaches/$',
        'flooding_lib.services.service_get_breaches',
        name='flooding_service_get_breaches'),

    url(r'^service/regionset/(?P<regionset_id>\d+)/regions/$',
        'flooding_lib.services.service_get_regions',
        name='flooding_service_get_regions'),

    url(r'^service/breach/(?P<breach_id>\d+)/scenarios/$',
        'flooding_lib.services.service_get_scenarios_from_breach',
        name='flooding_service_get_scenarios_from_breach'),

    url(r'^service/scenario/(?P<scenario_id>\d+)/results/$',
        'flooding_lib.services.service_get_results_from_scenario',
        name='flooding_service_get_results_from_scenario'),

    url(r'^service/scenario/(?P<scenario_id>\d+)/tasks/$',
        'flooding_lib.services.service_get_tasks_from_scenario',
        name='flooding_service_get_tasks_from_scenario'),

    url(r'^service/scenario/(?P<scenario_id>\d+)/cutofflocations/$',
        'flooding_lib.services.service_get_cutofflocations_from_scenario',
        name='flooding_service_get_cutofflocations_from_scenario'),

    url(r'^service/result/(?P<object_id>\d+)/(?P<location_nr>\d+)' +
        r'/(?P<parameter_nr>\d+)/$',
        'flooding_lib.views.service_result',
        name='flooding_service_result'),

    url(r'^excel/$',
        views.ExcelImportExportView.as_view(),
        name='flooding_excel_import_export'),

    url(r'^excel/(?P<project_id>\d+)/$',
        views.ExcelImportExportViewProject.as_view(),
        name='flooding_excel_import_export_project'),

    # Note no $ at the end, we want to add the filename
    url(r'^excel/(?P<project_id>\d+)/',
        'flooding_lib.views.excel_download',
        name='flooding_excel_download'),

    (r'^shared/', include(flooding_lib.sharedproject.urls)),

    url(r'^breachinfo/(?P<project_id>\d+)/(?P<breach_id>\d+)/$',
        pages.BreachInfoView.as_view(),
        name='flooding_breachinfo_page'),
)


if settings.DEBUG:
    #databrowse is for debugging purposes, so it is disabled in production
    urlpatterns += patterns(
        '',
        (r'^databrowse/(.*)', databrowse.site.root),
        )
