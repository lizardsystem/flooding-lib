from django.conf.urls.defaults import patterns, url

from flooding_lib.sharedproject import views


urlpatterns = patterns(
    '',
    url(r'^ror/$',
        views.Dashboard.as_view(project_name="ror"),
        name='sharedproject_dashboard'),
    url(r'^ror/(?P<province_id>\d+)/$',
        views.Dashboard.as_view(project_name="ror"),
        name='sharedproject_dashboard_province'),
    url(r'^(?P<project_name>[a-z]+)/(?P<province_id>\d+)/excel/',
        views.excel,
        name='sharedproject_dashboard_excel'),
)
