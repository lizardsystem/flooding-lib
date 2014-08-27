# -*- coding: utf-8 -*-
from string import Template
import datetime
import logging
import math

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _, ungettext

from flooding_lib.forms import AttachmentForm
from flooding_lib.forms import ScenarioArchiveForm
from flooding_lib.forms import EditScenarioPropertiesForm
from flooding_lib.forms import ScenarioNameRemarksForm
from flooding_lib.models import Attachment
from flooding_lib.models import Scenario
from flooding_lib.models import ScenarioBreach
from flooding_lib.models import SobekModel
from flooding_lib.models import UserPermission
from flooding_lib.permission_manager import receives_permission_manager
from flooding_lib.permission_manager import \
    receives_loggedin_permission_manager
from flooding_presentation.models import Animation
from flooding_lib.tools.approvaltool.views import approvaltable

logger = logging.getLogger(__name__)


def format_timedelta(t_delta):
    """
    - Formats the timedelta to "x days, y hours"
    """
    nrdays = t_delta.days
    nrhours = math.floor(t_delta.seconds / 3600)
    str_days = (ungettext('%(nrdays)d day', '%(nrdays)d days', nrdays)
                % {'nrdays': nrdays})
    str_hours = (ungettext('%(nrhours)d hour', '%(nrhours)d hours', nrhours)
                 % {'nrhours': nrhours})
    return str_days + ", " + str_hours


def infowindow(request):
    # action and scenarioid can be in get or post (to keep the
    # javascript RPC-calls simple) therefore we use REQUEST instead of
    # GET or POST
    action_name = request.REQUEST.get('action')
    scenario_id = request.REQUEST.get('scenarioid')

    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if action_name == 'information':  # GET
        return infowindow_information(scenario)

    elif action_name == 'remarks':  # POST AND GET difference handled
                                    # in 'return method'
        callbackfunction = request.REQUEST.get('callback')
        form_id = request.REQUEST.get('formId')
        return infowindow_remarks(
            request, scenario, callbackfunction, form_id)

    elif action_name == 'approval':  # POST AND GET difference handled
                                     # in 'return method'
        callbackfunction = request.REQUEST.get('callback', '')
        callbackfunction.replace("%22", '"')
        form_id = request.REQUEST.get('formId')
        with_approvalobject = bool(
            request.REQUEST.get('with_approvalobject', True))

        return infowindow_approval(
            request, scenario, callbackfunction,
            form_id, with_approvalobject)

    elif action_name == 'edit':
        return infowindow_edit(request, scenario_id)

    elif action_name == 'editproperties':
        return editproperties(request, scenario_id)

    elif action_name == 'showattachments':
        return showattachments(request, scenario_id)

    elif action_name == 'archive':
        return archive_scenario(request, scenario_id)


@receives_permission_manager
def archive_scenario(request, permission_manager, scenario_id):
    """Archive scenario using the model form,
    update scenario_cache"""
    can_edit = False
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    if permission_manager.check_project_permission(
        scenario.main_project,
        UserPermission.PERMISSION_SCENARIO_EDIT):
        can_edit = True

    succeeded = False
    user = User.objects.get(username=request.user)
    template = ""
    if request.method == 'POST':
        if not can_edit:
            return HttpResponse(
                unicode(_("No permission to edit scenario or login")))
        form = ScenarioArchiveForm(request.POST,
                                   instance=scenario,
                                   action='archive',
                                   can_edit=can_edit)
        if form.is_valid():
            if form.cleaned_data['archived']:
                scenario.archived = form.cleaned_data['archived']
                scenario.archived_at = datetime.datetime.today()
                scenario.archived_by = user
            else:
                scenario.archived = False
                scenario.archived_by = None
                scenario.archived_at = None

            scenario.save()
            scenario.update_status()
            form = ScenarioArchiveForm(instance=scenario, action='archive', can_edit=can_edit)
        template = 'flooding/archiveform.html'
    else:
        form = ScenarioArchiveForm(instance=scenario, action='archive', can_edit=can_edit)
        template = 'flooding/archive.html'

    return render_to_response(
        template, {'form': form, 'succeeded': succeeded})


def infowindow_information(scenario):
    return render_to_response(
        'flooding/infowindow_information.html',
        {'grouped_fields': scenario.grouped_scenario_information(),
         'attachment_list': scenario.get_attachment_list(),
         'scenario_id': scenario.id})


@receives_loggedin_permission_manager
def infowindow_remarks(
    request, permission_manager, scenario, callbackfunction, form_id):
    """Edits scenario name and remarks"""

    if not(permission_manager.check_project_permission(
            scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_EDIT_SIMPLE)):
        return HttpResponse(
            unicode(_("No permission to import scenario or login")))
    if request.method == 'POST':
        form = ScenarioNameRemarksForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
    else:
        form = ScenarioNameRemarksForm(instance=scenario)
    return render_to_response('flooding/infowindow_remarks.html',
                              {'form': form,
                               'callbackfunction': callbackfunction,
                               'form_id': form_id})


@receives_permission_manager
def infowindow_approval(
    request, permission_manager, scenario, callbackfunction,
    form_id, with_approvalobject):
    """Calls the page to give approval to scenarios"""

    # The scenario may be part of several projects. We are looking for
    # a project in which this user has approve rights, and then let
    # him approve for that project.

    # Right now, a user isn't supposed to be the approver for more
    # than one project, if that's necessary they should make multiple
    # users.

    for project in scenario.all_projects():
        if permission_manager.check_project_permission(
            project, UserPermission.PERMISSION_SCENARIO_APPROVE):
            break
    else:
        # No project found in which the user has Approve rights for
        # this scenario.
        return HttpResponse(
            unicode(_("No permission to import scenario or login")))

    items = dict(request.REQUEST.items())

    items['callback'] = (
        'callbackFunctions["ApprovalObjectCallbackFormFunction"]()')
    items['formId'] = 'totalApprovalForm'
    url_args = '?' + '&'.join("%s=%s" % x for x in items.items())

    destroy_function = items.get('destroy_function', None)
    create_function = items.get('create_function', None)
    pane_id = items.get('pane_id', None)

    return render_to_response(
        'flooding/infowindow_approval_total.html',
        {"approval_object": approvaltable(
                request,
                scenario.approval_object(project).id, True),
         'url_args': url_args,
         'destroy_function': destroy_function,
         'create_function': create_function,
         'pane_id': pane_id
         })


@receives_permission_manager
def infowindow_edit(request, permission_manager, scenario_id):
    used_scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            used_scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        return HttpResponse(
            unicode(_("No permission to import scenario or login")))

    return render_to_response(
        'flooding/infowindow_edit.html',
        {'scenario_id': scenario_id})


def showattachments(request, scenario_id):
    """Calls the page to give approval to scenarios"""
    succeeded = False
    sobekmodel_choices = []
    object_name_and_path_map = {
        'inundationmodel': (_('Inundation model'),
                            Template('inundationmodels/$id/')),
        'breachmodel': (_('Sobek models'), Template('sobekmodels/$id/')),
        'scenario': (_('Scenario'), Template('scenarios/$id/')),
        'project': (_('Project'), Template('projects/$id/'))}

    used_scenario = get_object_or_404(Scenario, pk=scenario_id)
    request_related_to = request.REQUEST.get('relatedto')

    if request_related_to == 'inundationmodel':
        attachments = used_scenario.sobekmodel_inundation.attachments.order_by(
            'uploaded_date').reverse()
        related_to_object = used_scenario.sobekmodel_inundation
    elif request_related_to == 'breachmodel':
        #Get contenttype of the sobekmodel.
        #Needed for generic relation search for multiple breaches
        c = ContentType.objects.get(model='sobekmodel')

        #Get the the sobekmodels
        for breach in used_scenario.breaches.all():
            for sobekmodel in breach.sobekmodels.all():
                sobekmodel_choices += [[
                        sobekmodel.id,
                        (sobekmodel.get_sobekmodeltype_display() +
                         ' : ' + str(sobekmodel.sobekversion))]]

        #Get the attachments of all sobekmodels related to this scenario
        attachments = Attachment.objects.filter(
            content_type=c,
            object_id__in=[sm[0] for sm in sobekmodel_choices]
            ).order_by('uploaded_date')
    elif request_related_to == 'scenario':
        attachments = used_scenario.attachments.order_by(
            'uploaded_date').reverse()
        related_to_object = used_scenario
    elif request_related_to == 'project':
        attachments = used_scenario.main_project.attachments.order_by(
            'uploaded_date').reverse()
        related_to_object = used_scenario.main_project

    if request.method == 'POST':

        form = AttachmentForm(sobekmodel_choices, request.POST, request.FILES)
        if form.is_valid():
            if 'Sobekmodel' in form.cleaned_data:
                related_to_object = SobekModel.objects.get(
                    pk=int(form.cleaned_data['Sobekmodel']))

            newAttachment = Attachment(
                uploaded_by=request.user.username,
                uploaded_date=datetime.datetime.now(),
                content_object=related_to_object,
                content_type=ContentType.objects.get_for_model(
                    related_to_object),
                object_id=related_to_object.id,
                file=None,
                name=form.cleaned_data['name'],
                remarks=form.cleaned_data['remarks'])

            # got it only working with creating explicitly the
            # contentfile and saving it as the 'file' of the
            # 'newAttachment'
            file_content = ContentFile(request.FILES['file'].read())
            newAttachment.file.save(request.FILES['file'].name, file_content)
            newAttachment.save()
            succeeded = True
    else:
        form = AttachmentForm(sobekmodel_choices)

    related_to = object_name_and_path_map[request_related_to][0]
    action_url = ('/flooding/infowindow/?scenarioid=' + scenario_id +
                  '&action=showattachments&relatedto=' + request_related_to)
    return render_to_response(
        'flooding/showattachments.html', {
            'form': form,
            'succeeded': succeeded,
            'related_to': related_to,
            'attachments': attachments,
            'scenario_id': scenario_id,
            'action_url': action_url})


@receives_permission_manager
def editproperties(request, permission_manager, scenario_id):
    """ Renders the page for editing properties of the scenario

    For this method the right permissions are required

    """
    used_scenario = get_object_or_404(Scenario, pk=scenario_id)

    if not(permission_manager.check_project_permission(
            used_scenario.main_project,
            UserPermission.PERMISSION_SCENARIO_EDIT)):
        return HttpResponse(
            unicode(_("No permission to import scenario or login")))

    succeeded = False
    if request.method == "POST":
        form = EditScenarioPropertiesForm(request.POST)
        if form.is_valid():
            cleaned_animation_start = form.cleaned_data['animation_start']
            scenario_breaches = ScenarioBreach.objects.filter(
                scenario=used_scenario)
            for sb in scenario_breaches:
                #tstartbreach is in days, but input in hours
                sb.tstartbreach = float(cleaned_animation_start) / 24
                sb.save()
            for pl in used_scenario.presentationlayer.all():
                animation = Animation.objects.filter(presentationlayer=pl)
                if animation.count() > 0:
                    # the model guarantees that there is only one animation
                    anim = animation[0]  # needed for correct saving
                                         # (weird thing in
                                         # Django... (JMV))
                    anim.startnr = cleaned_animation_start
                    anim.save()
            succeeded = True
    else:
        scenario_breaches = ScenarioBreach.objects.filter(
            scenario=used_scenario)
        #tstartbreach is in days, but input in hours
        min_value = min([int(round(sb.tstartbreach * 24))
                         for sb in scenario_breaches])
        form = EditScenarioPropertiesForm({'animation_start': min_value})

    return render_to_response('flooding/edit_scenario_properties.html',
                              {'scenario': used_scenario,
                               'form': form,
                               'succeeded': succeeded})
