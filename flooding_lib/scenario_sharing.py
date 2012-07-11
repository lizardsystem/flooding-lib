"""Views and helper functions for the 'scenario sharing'
functionality.

There exist two kinds of projects: normal projects and projects that
have scenarios 'shared' with them by the other projects. There are
currently two examples of such projects, ROR and 'Voor landelijk
gebruik', and those two examples are hardcoded.

Users with approval permission in a normal project can see a list of
their scenarios and offer to share them with one of the receiving
projects. Users with approval permission in those other projects can
see a list of projects offered to them and accept them. When that
happens, the scenario is added to the project and it will stay in two
projects from then on.

Approval is separate in both projects. When a scenario is added to the
ROR project, it will get a new approval object assigned to it that
relates to ROR and has ROR-specific rules.

When and how the status of that approval should be visible to merely
view-only users of ROR is an open question.

Implementation of approval objects is in approvaltool, but making sure
the scenario gets assigned its correct approval object will happen
here.

The functions in here use a model named ScenarioShareOffer from
flooding_lib.models, that presumably won't be used anywhere else.
"""

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from flooding_lib import models
from flooding_lib.permission_manager import \
    receives_loggedin_permission_manager

# Hardcode some project IDs
PROJECT_ROR = 99
PROJECT_LANDELIJK_GEBRUIK = 100
PROJECT_IDS = (PROJECT_ROR, PROJECT_LANDELIJK_GEBRUIK)


def project_field(scenario, project_id):
    """Returns a dict with a message to show in the list (has this
    scenario been offered?  Added? etc) and some extra fields that
    help with the possible Ajax actions."""

    # Possible situations:
    # Scenario is completely unrelated to project_id as yet
    #   Actions: offer it
    # Scenario is already offered to the project
    #   Actions: rescind offer
    # Scenario is already part of the project
    #   Nothing to do

    pass

@receives_loggedin_permission_manager
def list_view(request, permission_manager):
    scenarios = permission_manager.get_scenarios(
        permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE)

    project_dict = dict()
    for scenario in scenarios:
        project = scenario.main_project

        if project not in project_dict:
            project_dict[project] = []

        project_dict[project].append({
                'scenario': scenario,
                'extra_fields' : tuple(
                    project_field(scenario, project_id)
                    for project_id in PROJECT_IDS)
                })

    projects = [(project, project_dict[project])
                for project in sorted(project_dict)]

    otherprojects = (
        (str(project_id), models.Project.objects.get(pk=project_id).name)
        for project_id in PROJECT_IDS)

    return render_to_response('flooding/scenario_share_list.html', {
            'breadcrumbs': [
                {'name': _('Flooding'), 'url': reverse('flooding')},
                {'name': _('Scenarios'), 'url': reverse('flooding_scenarios_url')},
                {'name': _('Share scenarios')}
                ],
            'projects': projects,
            'otherprojects': otherprojects,
            })
