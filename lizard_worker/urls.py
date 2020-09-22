# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf import settings
from django.conf.urls import handler404
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseServerError
from django.template import Context
from django.template import loader
from lizard_worker.views import (
    WorkflowTasksView, WorkflowsView, LoggingView)

admin.autodiscover()
handler404  # pyflakes

urlpatterns = patterns(
    '',
    url(r'^scenario/(?P<scenario_id>\d*)/$',
        WorkflowsView.as_view(),
        name='lizard_worker_scenario'),
    url(r'^workflow/(?P<workflow_id>\d+)/tasks/$',
        WorkflowTasksView.as_view(),
        name='lizard_worker_workflow_task'),
    url(r'^scenario/(?P<scenario_id>\d*)/workflow/(?P<workflow_id>\d+)/loggings/$',
        LoggingView.as_view(),
        name='lizard_worker_workflow_logging'),
    url(r'^scenario/(?P<scenario_id>\d*)/workflow/(?P<workflow_id>\d+)/loggings/step/(?P<step>\d+)$',
        LoggingView.as_view(),
        name='lizard_worker_workflow_logging'),
    url(r'^scenario/(?P<scenario_id>\d*)/workflow/(?P<workflow_id>\d+)/task/(?P<task_id>\d*)/loggings/$',
        LoggingView.as_view(),
        name='lizard_worker_workflow_task_logging'),
    url(r'^scenario/(?P<scenario_id>\d*)/workflow/(?P<workflow_id>\d+)/task/(?P<task_id>\d*)/loggings/stap/(?P<step>\d+)$',
        LoggingView.as_view(),
        name='lizard_worker_workflow_task_logging'),
    (r'^admin/', include(admin.site.urls)),
    )


if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns(
        '', (r'', include('django.contrib.staticfiles.urls')))


def handler500(request):
    """500 error handler which includes ``request`` in the context.

    Simple test:

      >>> handler500({})  #doctest: +ELLIPSIS
      <django.http.response.HttpResponseServerError object at ...>

    """
    t = loader.get_template('lizard_worker/500.html')
    return HttpResponseServerError(
        t.render(Context({'request': request})))
