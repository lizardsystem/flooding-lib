"""Views and helper functions for the 'scenario sharing'
functionality.

There exist two kinds of projects: normal projects and projects that
have scenarios 'shared' with them by the other projects. There are
currently two examples of such projects, ROR and 'Voor landelijk
gebruik', and those two examples are hardcoded.

Users with approval permission in a normal project can see a list of

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

import json
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST

from flooding_lib import models
from flooding_lib.permission_manager import \
    receives_loggedin_permission_manager
from flooding_lib.tools.importtool import models as importmodels
from flooding_lib.tools.approvaltool import models as approvalmodels

logger = logging.getLogger(__name__)

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
    #   Scenario has all required metadata filled-in
    #      Actions: offer it
    #   It does not
    #      Say so
    # Scenario is already offered to the project
    #   Actions: rescind offer
    # Scenario is already part of the project
    #   Nothing to do

    fielddict = {
        'scenario_id': scenario.id,
        'project_id': project_id,
        }

    if models.ScenarioShareOffer.objects.filter(
        scenario=scenario, new_project__id=project_id).exists():
        fielddict.update({
            'message': _("Offered"),
            'action': 'rescind',
            })
    else:
        try:
            scenarioproject = (
                models.ScenarioProject.objects.select_related("project").
                get(scenario=scenario, project__id=project_id))
        except models.ScenarioProject.DoesNotExist:
            # Scenario not in project
            if scenario.has_values_for(importmodels.InputField.objects.all()):
                fielddict.update({
                        'message': _("Offer to project"),
                        'action': 'add',
                        })
            else:
                fielddict.update({
                        'message': _("Not all required data present"),
                        'action': '',
                        })
        else:
            # Scenario in project
            scenarioproject.ensure_has_approvalobject()
            approvalobject = scenarioproject.approvalobject
            if approvalobject.approved:
                status = _('approved')
                fielddict['approvalobject'] = approvalobject
            elif approvalobject.disapproved:
                status = _('disapproved')
                fielddict['approvalobject'] = approvalobject
            else:
                status = _('not yet approved')

            fielddict.update({
                    'message': "{message} ({status})". format(
                        message=_("Added to project"), status=status),
                    'action': '',
                    })

    fielddict['is_url'] = bool(fielddict['action'])

    return fielddict


@require_GET
@receives_loggedin_permission_manager
def list_view(request, permission_manager):
    projects = permission_manager.get_projects(
        permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE)
    if len(projects) == 0:
        return HttpResponse(
            unicode(_("You do not have approval permission in any project.")))

    if projects[0].id in PROJECT_IDS:
        # Handle these in a separate function
        return list_view_accepting_project(request, permission_manager)

    return render_to_response('flooding/scenario_share_project_list.html', {
            'breadcrumbs': [
                {'name': _('Flooding'),
                 'url': reverse('flooding')},
                {'name': _('Scenarios'),
                 'url': reverse('flooding_scenarios_url')},
                {'name': _('Share scenarios')}
                ],
            'projects': projects,
            })


@require_GET
@receives_loggedin_permission_manager
def list_project_view(request, permission_manager, project_id):
    project = models.Project.objects.get(pk=project_id)

    if not permission_manager.check_project_permission(
        project,
        permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE):
        return HttpResponse(
            unicode(_("You do not have approval permission in this project.")))

    scenarios = project.original_scenarios()

    project_dict = dict()
    for scenario in scenarios:
        if project not in project_dict:
            project_dict[project] = []

        project_dict[project].append({
                'scenario': scenario,
                'extra_fields': tuple(
                    project_field(scenario, project_id)
                    for project_id in PROJECT_IDS)
                })

    for project in project_dict:
        project_dict[project].sort(
            cmp=lambda a, b:
                cmp(a['scenario'].name, b['scenario'].name))

    projects = [(project, project_dict[project])
                for project in sorted(project_dict,
                                      cmp=lambda a, b: cmp(a.name, b.name))]

    otherprojects = (
        (str(project_id), models.Project.objects.get(pk=project_id).name)
        for project_id in PROJECT_IDS)

    return render_to_response('flooding/scenario_share_list.html', {
            'breadcrumbs': [
                {'name': _('Flooding'),
                 'url': reverse('flooding')},
                {'name': _('Scenarios'),
                 'url': reverse('flooding_scenarios_url')},
                {'name': _('Share scenarios')}
                ],
            'projects': projects,
            'otherprojects': otherprojects,
            })


def list_view_accepting_project(request, permission_manager):
    # Find out in which accepting project this user can approve We
    # don't support users accepting in two projects, make another user
    # please.

    for project_id in PROJECT_IDS:
        toproject = models.Project.objects.get(pk=project_id)
        if permission_manager.check_project_permission(
            toproject, models.UserPermission.PERMISSION_SCENARIO_APPROVE):
            break
    else:
        # In neither. But then how did we get in this function?
        return HttpResponse(
            "You do not have approval permission in "
            "any of the accepting projects.")

    scenarios = tuple(
        {
            'scenario': shared.scenario,
            'shared_by': shared.shared_by,
            'project': shared.scenario.main_project  # Slow
            }
        for shared in models.ScenarioShareOffer.objects.filter(
            new_project=toproject))
    logger.debug(scenarios)

    project_dict = dict()
    for scenario in scenarios:
        project = scenario['project']
        if project not in project_dict:
            project_dict[project] = []
        project_dict[project].append(scenario)

    for project in project_dict:
        project_dict[project].sort(
            cmp=lambda a, b: cmp(a['scenario'].name, b['scenario'].name))

    projects = [(project, project_dict[project]) for project in
                sorted(project_dict, cmp=lambda a, b: cmp(a.name, b.name))]

    return render_to_response('flooding/scenario_accept_list.html', {
            'breadcrumbs': [
                {'name': _('Flooding'),
                 'url': reverse('flooding')},
                {'name': _('Scenarios'),
                 'url': reverse('flooding_scenarios_url')},
                {'name': _('Accept scenarios')}
                ],
            'toproject': toproject,
            'projects': projects,
            })


@require_POST
@receives_loggedin_permission_manager
def action_view(request, permission_manager):
    action = request.POST['action']
    scenario_id = request.POST['scenario_id']
    project_id = request.POST['project_id']

    scenario = models.Scenario.objects.get(pk=scenario_id)
    project = models.Project.objects.get(pk=project_id)

    if action == 'add':
        models.ScenarioShareOffer.objects.create(
            scenario=scenario, new_project=project, shared_by=request.user)

    if action == 'rescind':
        models.ScenarioShareOffer.objects.filter(
            scenario=scenario, new_project=project).delete()

    if action == 'accept':
        models.ScenarioShareOffer.objects.filter(
            scenario=scenario, new_project=project).delete()

        # Add the scenario
        scenarioproject = project.add_scenario(scenario)

        # Hardcoded: set the check for metadata completeness automatically
        scenarioproject.ensure_has_approvalobject()
        metadata_complete_rule = approvalmodels.ApprovalRule.objects.get(pk=6)
        success = scenario.has_values_for(
            importmodels.InputField.objects.all())
        scenarioproject.approvalobject.approve(
            rule=metadata_complete_rule,
            success=success,
            creator=request.user.username,
            remarks=(
                "Set automatically while adding to project {0}."
                .format(project)))

        return HttpResponse(json.dumps({'message': ''}))

    field = project_field(scenario, project.id)

    return HttpResponse(json.dumps(field))
