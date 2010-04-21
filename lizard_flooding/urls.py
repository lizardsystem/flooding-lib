from django.conf.urls.defaults import *
from django.contrib import databrowse

from lizard.flooding.models import Project, Scenario

info_dict = {
    'queryset': Project.objects.all(),
}

#databrowse is for debugging purposes, remove when in a production environment!

urlpatterns = patterns(
    '',
    url(r'^$',
        'lizard.flooding.views.index',
        name='flooding'),
    
    (r'^databrowse/(.*)', databrowse.site.root),
        
    url(r'^tools/', 
        include('lizard.flooding.tools.urls')),
        
    url(r'^project/$', 
        'lizard.flooding.views.project_list',
        name='flooding_projects_url'),

    url(r'^project/add/$', 
        'lizard.flooding.views.project_addedit',
        name='flooding_project_add'),
    
    url(r'^project/(?P<object_id>\d+)/$',
        'lizard.flooding.views.project',
        name='flooding_project_detail'),

    url(r'^project/(?P<object_id>\d+)/edit/$',
        'lizard.flooding.views.project_addedit',
        name='flooding_project_edit'),

    url(r'^project/(?P<object_id>\d+)/delete/$',
        'lizard.flooding.views.project_delete',
        name='flooding_project_delete'),

    url(r'^scenario/$', 
        'lizard.flooding.views.scenario_list', 
        name='flooding_scenarios_url'),

    url(r'^scenario/add/$', 
        'lizard.flooding.views.scenario_addedit', 
        name='flooding_scenario_add'),

    url(r'^scenario/(?P<object_id>\d+)/$', 
        'lizard.flooding.views.scenario', 
        name='flooding_scenario_detail'),

    url(r'^scenario/(?P<object_id>\d+)/edit/$', 
        'lizard.flooding.views.scenario_addedit', 
        name='flooding_scenario_edit'),

    url(r'^scenario/(?P<object_id>\d+)/editnameremarks/$', 
        'lizard.flooding.views.scenario_editnameremarks', 
        name='flooding_scenario_editnameremarks'),

    url(r'^scenario/(?P<object_id>\d+)/delete/$', 
        'lizard.flooding.views.scenario_delete', 
        name='flooding_scenario_delete'),

    url(r'^scenario/(?P<scenario_id>\d+)/addcutofflocation/$', 
        'lizard.flooding.views.scenario_cutofflocation_add', 
        name='flooding_scenario_cutofflocation_add'),

    url(r'^scenariocutofflocation/(?P<object_id>\d+)/delete/$', 
        'lizard.flooding.views.scenario_cutofflocation_delete', 
        name='flooding_scenario_cutofflocation_delete'),

    url(r'^scenario/(?P<scenario_id>\d+)/addbreach/$', 
        'lizard.flooding.views.scenario_breach_add', 
        name='flooding_scenario_breach_add'),

    url(r'^scenariobreach/(?P<object_id>\d+)/delete/$', 
        'lizard.flooding.views.scenario_breach_delete', 
        name='flooding_scenario_breach_delete'),

    url(r'^infowindow/$',
        'lizard.flooding.views_infowindow.infowindow',
        name='infowindow'),     
        
    url(r'^fractal/$',
        'lizard.flooding.views.fractal'),

    url(r'^result/$', 
        'lizard.flooding.views.result_list',
        name='flooding_result_list'),

    url(r'^task/$',
        'lizard.flooding.views.task_list',
        name='flooding_task_list'),

    url(r'^task/(?P<object_id>\d+)/$',
        'lizard.flooding.views.task',
        name='flooding_task_detail'),

    
    url(r'^service/$',
        'lizard.flooding.services.service',
        name='flooding_service'),
    
    url(r'^service/project/$',
        'lizard.flooding.services.service_get_projects',
        name='flooding_service_get_projects'),
    
    url(r'^service/project/(?P<project_id>\d+)/scenarios/$',
        'lizard.flooding.services.service_get_scenarios_from_project',
        name='flooding_service_get_scenarios_from_project'),
    
    url(r'^service/scenario/$',
        'lizard.flooding.services.service_get_scenarios',
        name='flooding_service_get_scenarios'),
    
    url(r'^service/regionset/$',
        'lizard.flooding.services.service_get_regionsets',
        name='flooding_service_get_regionsets'),
    
    url(r'^service/region/$',
        'lizard.flooding.services.service_get_all_regions',
        name='flooding_service_get_all_regions'),
    
    url(r'^service/region/(?P<region_id>\d+)/breaches/$',
        'lizard.flooding.services.service_get_breaches',
        name='flooding_service_get_breaches'),
    
    url(r'^service/regionset/(?P<regionset_id>\d+)/regions/$',
        'lizard.flooding.services.service_get_regions',
        name='flooding_service_get_regions'),        
    
    url(r'^service/breach/(?P<breach_id>\d+)/scenarios/$',
        'lizard.flooding.services.service_get_scenarios_from_breach',
        name='flooding_service_get_scenarios_from_breach'),
    
    url(r'^service/scenario/(?P<scenario_id>\d+)/results/$',
        'lizard.flooding.services.service_get_results_from_scenario',
        name='flooding_service_get_results_from_scenario'),
    
    url(r'^service/scenario/(?P<scenario_id>\d+)/tasks/$',
        'lizard.flooding.services.service_get_tasks_from_scenario',
        name='flooding_service_get_tasks_from_scenario'),
    
    url(r'^service/scenario/(?P<scenario_id>\d+)/cutofflocations/$',
        'lizard.flooding.services.service_get_cutofflocations_from_scenario',
        name='flooding_service_get_cutofflocations_from_scenario'),

    url(r'^service/result/(?P<object_id>\d+)/(?P<location_nr>\d+)/(?P<parameter_nr>\d+)/$',
        'lizard.flooding.views_dev.service_result',
        name='flooding_service_result'),   
 
        
    #url(r'^floodingsa/$',
    #    'lizard.flooding.views.service_get_dict_for_lizardsa'),        
    
    
)
