# -*- coding: utf-8 -*-
from string import Template
import datetime
import math
import os.path
import string

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext_lazy as _, ungettext

from lizard_flooding.forms import AttachmentForm
from lizard_flooding.forms import EditScenarioPropertiesForm,ScenarioNameRemarksForm, TaskApprovalForm
from lizard_flooding.models import Attachment, ExternalWater, Scenario
from lizard_flooding.models import ScenarioBreach, SobekModel, Task, TaskType
from lizard_flooding.models import UserPermission, ExtraInfoField
from lizard_flooding.permission_manager import PermissionManager
from lizard_flooding.tools.approvaltool.views import approvaltable
from lizard_presentation.models import Animation


def format_timedelta(t_delta):
    """
    - Formats the timedelta to "x days, y hours"
    """
    nrdays = t_delta.days
    nrhours = math.floor(t_delta.seconds / 3600)
    str_days = ungettext('%(nrdays)d day', '%(nrdays)d days', nrdays) % {'nrdays' : nrdays}
    str_hours = ungettext('%(nrhours)d hour', '%(nrhours)d hours', nrhours) % {'nrhours' : nrhours}
    return str_days + ", " + str_hours

def infowindow(request):
    # action and scenarioid can be in get or post (to keep the javascript RPC-calls simple)
    # therefore we use REQUEST instead of GET or POST
    action_name = request.REQUEST.get('action')
    scenario_id = request.REQUEST.get('scenarioid')

    if action_name == 'information': #GET
        return infowindow_information(request, scenario_id)

    elif action_name == 'remarks': #POST AND GET difference handled in 'return method'
        callbackfunction = request.REQUEST.get('callback')
        form_id = request.REQUEST.get('formId')
        return infowindow_remarks(request, scenario_id, callbackfunction, form_id)

    elif action_name == 'approval': #POST AND GET difference handled in 'return method'
        callbackfunction = request.REQUEST.get('callback')
        callbackfunction.replace("%22","\"")
        form_id = request.REQUEST.get('formId')
        with_approvalobject = request.REQUEST.get('with_approvalobject', 1)
        if int(with_approvalobject) == 0:
            with_approvalobject = False
        else:
            with_approvalobject = True


        return infowindow_approval(request, scenario_id, callbackfunction, form_id,with_approvalobject)

    elif action_name == 'edit':
        return infowindow_edit(request, scenario_id)

    elif action_name == 'editproperties':
        return editproperties(request, scenario_id)

    elif action_name == 'showattachments':
        return showattachments(request, scenario_id)


def get_intervalstring_from_dayfloat(input):

    if input == None:
        return ""

    if input <0:
        sign = '-'
    else:
        sign = ''

    days = math.floor(input)
    input = (input - days)*24
    hours = math.floor(input)
    input = (input -  hours)*60
    minutes = math.floor(input)

    return  sign + ("%i d "%days) + ("%2i:"%hours).replace(' ', '0') + ("%2i"%minutes).replace(' ', '0')


def infowindow_information(request, scenario_id):
    """
    - Returns the information for in the infowindow
    - The information is collected from several tables in the database
    """
    scenario = get_object_or_404(Scenario, pk=scenario_id)

    #Get general information
    general_info_list = list()
    breach_names = ', '.join([b.name for b in scenario.breaches.all()])
    region_names = ', '.join([b.region.name for b in scenario.breaches.all()])

    general_info_list.append((_('Scenario name'), scenario.name))
    general_info_list.append((_('Breach locations'), breach_names))
    general_info_list.append((_('Region'), region_names))
    general_info_list.append((_('Project'), scenario.project.friendlyname))

    extrafields = scenario.extrascenarioinfo_set.filter(extrainfofield__header = ExtraInfoField.HEADER_GENERAL,
                                        extrainfofield__use_in_scenario_overview = True).order_by('-extrainfofield__position')
    for field in extrafields:
        general_info_list.append((field.extrainfofield.name, field.value))

    #Get metadata information
    metadata_info_list = list()

    metadata_info_list.append((_('Scenario id'), scenario.id))
    metadata_info_list.append((_('Scenario remarks'), scenario.remarks))
    #metadata_info_list.append((_('Project remarks'), TO_CREATE_IN_DB))
    extrafields = scenario.extrascenarioinfo_set.filter(extrainfofield__header = ExtraInfoField.HEADER_METADATA,
                                        extrainfofield__use_in_scenario_overview = True).order_by('-extrainfofield__position')
    for field in extrafields:
        metadata_info_list.append((field.extrainfofield.name, field.value))

    attachment_list = list()
    inundationmodel_attachments = scenario.sobekmodel_inundation.attachments.order_by('uploaded_date').reverse()
    scenario_attachments = scenario.attachments.order_by('uploaded_date').reverse()
    project_attachments = scenario.project.attachments.order_by('uploaded_date').reverse()

    #Needed for generic relation search for multiple breaches
    c = SobekModel
    #ContentType.objects.get(model='sobekmodel')
    sobekmodel_choices=[]

    #Get the the sobekmodels
    for breach in scenario.breaches.all():
        for sobekmodel in breach.sobekmodels.all():
            sobekmodel_choices+=[[sobekmodel.id]]
    #xxxxxx
    breachmodel_attachments = Attachment.objects.filter(content_type=c, object_id__in=[sm[0] for sm in sobekmodel_choices]).order_by('uploaded_date')

    scen_atts = [(f.file.name, os.path.split(f.file.name)[1]) for f in scenario_attachments]
    proj_atts = [(f.file.name, os.path.split(f.file.name)[1]) for f in project_attachments]
    inun_atts = [(f.file.name, os.path.split(f.file.name)[1]) for f in inundationmodel_attachments]
    brea_atts = [(f.file.name, os.path.split(f.file.name)[1]) for f in breachmodel_attachments]

    attachment_list.append((_('Scenario attachments'), scen_atts))
    attachment_list.append((_('Project attachments'), proj_atts))
    attachment_list.append((_('Inundationmodel attachments'), inun_atts))
    attachment_list.append((_('Externalwater model attachments'), brea_atts))


    #Get breach 'set' information
    breachset_info_list = list()

    for br in scenario.breaches.all():
        #Get breach information
        br_info_list = list()
        scenariobreach = scenario.scenariobreach_set.get(breach=br)

        br_info_list.append((_('Name'), br.name))
        # Put here 'if fixed' or 'if automatic' instead of True and False
        if True:
            pass
            #br_info_list.append((_('Width of breach'), TO_CREATE_IN_DB))
        elif False:
            br_info_list.append((_('Materiaal kering (ENGELS)'), scenariobreach.ucritical))

        br_info_list.append((_('Initial breach width'), scenariobreach.widthbrinit))
        br_info_list.append((_('Duration till breach has maximal depth'), get_intervalstring_from_dayfloat(scenariobreach.tmaxdepth)))


        extrafields = scenario.extrascenarioinfo_set.filter(extrainfofield__header = ExtraInfoField.HEADER_BREACH,
                                        extrainfofield__use_in_scenario_overview = True).order_by('-extrainfofield__position')
        for field in extrafields:
            br_info_list.append((field.extrainfofield.name, field.value))
        #Get external water info
        extw_info_list = list()

        extw_info_list.append((_('Externalwater name'), br.externalwater.name))
        extw_info_list.append((_('Externalwater type'), br.externalwater.get_type_display()))
        if scenariobreach.manualwaterlevelinput:
            extw_info_list.append((_('Maximal water level'), _('manual input used')))
            extw_info_list.append((_('Repeating period duration'), _('manual input used')))            
        else:    
            extw_info_list.append((_('Maximal water level'), scenariobreach.extwmaxlevel))
            extw_info_list.append((_('Repeating period duration'), scenariobreach.extwrepeattime))
        
        extw_info_list.append((_('Bottom level breach'), scenariobreach.bottomlevelbreach))
        extw_info_list.append((_('Pit depth'), scenariobreach.pitdepth))

        if br.externalwater.type == ExternalWater.TYPE_SEA:
            if scenariobreach.manualwaterlevelinput:
                extw_info_list.append((_('Duration storm'), _('manual input used')))
                extw_info_list.append((_('Duration peak'), _('manual input used')))
                extw_info_list.append((_('Tide shift'), _('manual input used')))
            else:
                extw_info_list.append((_('Duration storm'), get_intervalstring_from_dayfloat(scenariobreach.tstorm)))
                extw_info_list.append((_('Duration peak'), get_intervalstring_from_dayfloat(scenariobreach.tpeak)))
                extw_info_list.append((_('Tide shift'), get_intervalstring_from_dayfloat(scenariobreach.tdeltaphase)))
            if scenariobreach.tide != None:
                extw_info_list.append((_('Tide properties'), scenariobreach.tide.name))
        elif br.externalwater.type == ExternalWater.TYPE_LAKE:
            extw_info_list.append((_('Duration storm'), get_intervalstring_from_dayfloat(scenariobreach.tstorm)))
            extw_info_list.append((_('Duration peak'), get_intervalstring_from_dayfloat(scenariobreach.tpeak)))

        elif br.externalwater.type == ExternalWater.TYPE_CANAL:
            pass
        elif br.externalwater.type == ExternalWater.TYPE_INTERNAL_LAKE:
            pass
        elif br.externalwater.type == ExternalWater.TYPE_INTERNAL_CANAL:
            pass
        elif br.externalwater.type == ExternalWater.TYPE_RIVER:
            pass
        elif br.externalwater.type == ExternalWater.TYPE_LOWER_RIVER:
            extw_info_list.append((_('Duration storm'), get_intervalstring_from_dayfloat(scenariobreach.tstorm)))
            extw_info_list.append((_('Duration peak'), get_intervalstring_from_dayfloat(scenariobreach.tpeak)))
            if scenariobreach.tide != None:
                extw_info_list.append((_('Tide properties'), scenariobreach.tide.name))

        extrafields = scenario.extrascenarioinfo_set.filter(extrainfofield__header = ExtraInfoField.HEADER_EXTERNALWATER,
                                        extrainfofield__use_in_scenario_overview = True).order_by('-extrainfofield__position')
        for field in extrafields:
            extw_info_list.append((field.extrainfofield.name, field.value))

        breachset_info_list.append((br.name, br_info_list, br.externalwater.name, extw_info_list))



    return render_to_response('flooding/infowindow_information.html',
                              {'general_info_list': general_info_list,
                               'metadata_info_list': metadata_info_list,
                               'breachset_info_list': breachset_info_list,
                               'attachment_list': attachment_list,
                               'scenario_id': scenario_id})

@login_required
def infowindow_remarks(request, scenario_id, callbackfunction, form_id):
    """Edits scenario name and remarks"""
    scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(scenario.project, UserPermission.PERMISSION_SCENARIO_EDIT_SIMPLE)):
        return HttpResponse(_("No permission to import scenario or login"))
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


def infowindow_approval(request, scenario_id, callbackfunction, form_id, with_approvalobject ):
    """Calls the page to give approval to scenarios"""

    used_scenario = get_object_or_404(Scenario, pk=scenario_id)

    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(used_scenario.project, UserPermission.PERMISSION_SCENARIO_APPROVE)):
        return HttpResponse(_("No permission to import scenario or login"))

    if request.method == 'POST':
        form = TaskApprovalForm(request.POST)
        if form.is_valid():
            newTask = Task(scenario = used_scenario,
                           remarks = form.cleaned_data['remarks'],
                           tasktype = TaskType.objects.get(id=190),
                           tstart = datetime.datetime.now(),
                           tfinished = datetime.datetime.now(),
                           creatorlog = request.user.username
                           )
            # Convert string values to boolean (the None option, will be handled correctly)
            if form.cleaned_data['successful'] == 'True':
                newTask.successful = True
            elif form.cleaned_data['successful'] == 'False':
                newTask.successful = False
            newTask.save()
    else:
       form = TaskApprovalForm()

    approved_tasks = Task.objects.filter(Q(scenario=used_scenario), Q(tasktype=TaskType.TYPE_SCENARIO_APPROVE))
    ordered_approved_tasks = approved_tasks.order_by('tfinished')

    if used_scenario.approvalobject and with_approvalobject:
        items = {}
        for label, value in request.REQUEST.items():
            items[label] = value

        items['callback'] = 'callbackFunctions["ApprovalObjectCallbackFormFunction"]()'
        items['formId'] = 'totalApprovalForm'
        url_args = '?' + string.join([ "%s=%s"%x for x in items.items()], "&")

        destroy_function = request.REQUEST.get('destroy_function', None)
        create_function  = request.REQUEST.get('create_function', None)
        pane_id  = request.REQUEST.get('pane_id', None)
        return render_to_response('flooding/infowindow_approval_total.html',
                                  {"approval_object": approvaltable(request,used_scenario.approvalobject.id, True),
                                   'with_approval_object':True,
                                   'form': form,
                                   'ordered_approved_tasks': ordered_approved_tasks,
                                   'callbackfunction': callbackfunction,
                                   'form_id': form_id,
                                   'url_args': url_args,
                                   'destroy_function':destroy_function,
                                   'create_function':create_function,
                                   'pane_id':pane_id
                                   })


    else:
        return render_to_response( 'flooding/infowindow_approval.html',
                                  {'form': form,
                                   'ordered_approved_tasks': ordered_approved_tasks,
                                   'callbackfunction': callbackfunction,
                                   'form_id': form_id})

def infowindow_edit(request, scenario_id):
    used_scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(used_scenario.project, UserPermission.PERMISSION_SCENARIO_EDIT)):
        return HttpResponse(_("No permission to import scenario or login"))

    return render_to_response('flooding/infowindow_edit.html', {'scenario_id': scenario_id})

def showattachments(request, scenario_id):
    """Calls the page to give approval to scenarios"""
    succeeded = False
    sobekmodel_choices = []
    object_name_and_path_map = {'inundationmodel': (_('Inundation model'), Template('inundationmodels/$id/')),
                                'breachmodel': (_('Sobek models'), Template('sobekmodels/$id/')),
                                'scenario': (_('Scenario'), Template('scenarios/$id/')),
                                'project': (_('Project'), Template('projects/$id/'))}

    used_scenario = get_object_or_404(Scenario, pk=scenario_id)
    request_related_to = request.REQUEST.get('relatedto')

    if request_related_to == 'inundationmodel':
        attachments = used_scenario.sobekmodel_inundation.attachments.order_by('uploaded_date').reverse()
        related_to_object = used_scenario.sobekmodel_inundation
    elif request_related_to == 'breachmodel':
        #Get contenttype of the sobekmodel.
        #Needed for generic relation search for multiple breaches
        c =  ContentType.objects.get(model='sobekmodel')

        #Get the the sobekmodels
        for breach in used_scenario.breaches.all():
            for sobekmodel in breach.sobekmodels.all():
                sobekmodel_choices+=[[sobekmodel.id, sobekmodel.get_sobekmodeltype_display() + ' : ' + str(sobekmodel.sobekversion)]]

                #Get the attachments of all sobekmodels related to this scenario
        attachments = Attachment.objects.filter(content_type=c, object_id__in=[sm[0] for sm in sobekmodel_choices]).order_by('uploaded_date')
    elif request_related_to == 'scenario':
        attachments = used_scenario.attachments.order_by('uploaded_date').reverse()
        related_to_object = used_scenario
    elif request_related_to == 'project':
        attachments = used_scenario.project.attachments.order_by('uploaded_date').reverse()
        related_to_object = used_scenario.project

    if request.method == 'POST':

        form = AttachmentForm(sobekmodel_choices, request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.has_key('Sobekmodel'):
                related_to_object = SobekModel.objects.get(pk = int(form.cleaned_data['Sobekmodel']))
            #path = object_name_and_path_map[request_related_to][1].substitute(id= str(related_to_object.id))
            newAttachment = Attachment(uploaded_by = request.user.username,
                                   uploaded_date = datetime.datetime.now(),
                                   content_object = related_to_object,
                                   content_type = ContentType.objects.get_for_model(related_to_object),
                                   object_id = related_to_object.id,
                                   file = None,
                                   name = form.cleaned_data['name'],
                                   remarks = form.cleaned_data['remarks'])

            # got it only working with creating explicitly the contentfile and saving it
            # as the 'file' of the 'newAttachment'
            file_content = ContentFile(request.FILES['file'].read())
            newAttachment.file.save(request.FILES['file'].name, file_content)
            newAttachment.save()
            succeeded = True
    else:
        form = AttachmentForm(sobekmodel_choices)

    related_to =  object_name_and_path_map[request_related_to][0]
    action_url = '/flooding/infowindow/?scenarioid=' + scenario_id + '&action=showattachments&relatedto=' + request_related_to
    return render_to_response('flooding/showattachments.html', {'form': form,
                                                                'succeeded': succeeded,
                                                                'related_to': related_to,
                                                                'attachments': attachments,
                                                                'scenario_id': scenario_id,
                                                                'action_url': action_url})

def editproperties(request, scenario_id):
    """ Renders the page for editing properties of the scenario

    For this method the right permissions are required

    """
    used_scenario = get_object_or_404(Scenario, pk=scenario_id)
    pm = PermissionManager(request.user)
    if not(pm.check_project_permission(used_scenario.project, UserPermission.PERMISSION_SCENARIO_EDIT)):
        return HttpResponse(_("No permission to import scenario or login"))

    succeeded = False
    if request.method == "POST":
        form = EditScenarioPropertiesForm(request.POST)
        if form.is_valid():
            cleaned_animation_start = form.cleaned_data['animation_start']
            scenario_breaches = ScenarioBreach.objects.filter(scenario=used_scenario)
            for sb in scenario_breaches:
                sb.tstartbreach = float(cleaned_animation_start)/24 #tstartbreach is in days, but input in hours
                sb.save()
            for pl in used_scenario.presentationlayer.all():
                animation = Animation.objects.filter(presentationlayer = pl)
                if animation.count() >0:
                    # the model guarantees that there is only one animation
                    anim = animation[0] #needed for correct saving (weird thing in Django... (JMV))
                    anim.startnr = cleaned_animation_start
                    anim.save()
            succeeded = True
    else:
        scenario_breaches = ScenarioBreach.objects.filter(scenario=used_scenario)
        min_value = min([int(round(sb.tstartbreach*24)) for sb in scenario_breaches]) #tstartbreach is in days, but input in hours
        form = EditScenarioPropertiesForm({'animation_start': min_value})

    return render_to_response('flooding/edit_scenario_properties.html',
                              {'scenario': used_scenario,
                               'form': form,
                               'succeeded': succeeded})

