
from lizard_flooding.tools.importtool.forms import GroupImportForm
from lizard_flooding.tools.importtool.models import ImportScenario, InputField, ImportScenarioInputField, IntegerValue, FloatValue, StringValue, TextValue, GroupImport
from lizard_base.models import Setting
from lizard_flooding.tools.approvaltool.models import ApprovalObject, ApprovalObjectType
from lizard_flooding.models import Breach, Project, Scenario, SobekModel, SobekVersion, Region, Task, TaskType, WaterlevelSet, ScenarioBreach, ExtraInfoField, \
                        ExtraScenarioInfo, Result, ResultType
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import Context, loader
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404

from lizard_flooding.permission_manager import PermissionManager
from lizard_flooding.models import UserPermission
from lizard_flooding.tools.importtool.models import FileValue
from lizard_flooding.tools.importtool.forms import ImportScenarioFileUploadForm
from lizard_flooding.tools.approvaltool.views import approvaltable
from zipfile import ZipFile, ZIP_DEFLATED, BadZipfile
import os
import re
import operator
import datetime
from shutil import copyfile
from cStringIO import StringIO
#from StringIO import StringIO

import logging
logger = logging.getLogger(__name__)

def overview(request):
    """
    Renders Lizard-flooding import page, contains among others
    an overview of the imported scenarios.
    """
    has_approve_rights = False
    if not (request.user.is_authenticated() and (request.user.has_perm('importtool.can_upload') or request.user.has_perm('importtool.can_approve'))):
        return HttpResponse(_("No permission to upload data or login"))
    elif request.user.has_perm('importtool.can_approve'):
        #show all uploaded scenarios
        importscenarios = ImportScenario.objects.filter()
        has_approve_rights = True
    else:
        #show only own uploaded scenarios
        importscenarios = ImportScenario.objects.filter(owner = request.user)


    import_scenarios_list = []
    for import_scenario in importscenarios.order_by('state', 'creation_date', 'id'):
        try:
            group_name = import_scenario.groupimport.name
        except AttributeError, e:
            group_name = '-'

        import_scenarios_list += [(import_scenario.creation_date,
                                   import_scenario.id,
                                   import_scenario.name,
                                   import_scenario.owner.username,
                                   group_name,
                                   import_scenario.validation_remarks,
                                   import_scenario.get_state_display(),
                                   import_scenario.state,
                                   )]
    breadcrumbs = [
        {'name': _('Import tool') }]

    return render_to_response('import/imports_overview.html',
                              {'import_scenarios_list': import_scenarios_list,
                               'breadcrumbs': breadcrumbs,
                               'has_approve_rights': has_approve_rights
                               })

def approve_import(request, import_scenario_id):
    """
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """
    user = request.user
    if not (request.user.is_authenticated() and request.user.has_perm('importtool.can_approve')):
        return HttpResponse(_("No permission to approve scenario or login"))

    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if request.method == 'POST':
        if request.POST.get('action') == 'save_admin' or request.POST.get('action') =='save_and_import':
            importscenario.state = request.POST.get('state')
            breach= request.POST.get('breach', None)
            project = request.POST.get('project', None)
            region = request.POST.get('region', None)
            importscenario.validation_remarks = request.POST.get('remarks', None)
            if breach != None and breach != 'null':
                try:
                    importscenario.breach = Breach.objects.get(pk=int(breach))
                except Breach.DoesNotExist, e:
                    pass
                except ValueError, e:
                    pass
                except TypeError, e:
                    pass

            if project != None and project != 'null':
                try:
                    importscenario.project = Project.objects.get(pk=int(project))
                except Project.DoesNotExist, e:
                    pass
                except ValueError, e:
                    pass
                except TypeError, e:
                    pass

            if region != None and region != 'null':
                try:
                    importscenario.region = Region.objects.get(pk=int(region))
                except Region.DoesNotExist, e:
                    pass
                except ValueError, e:
                    pass
                except TypeError, e:
                    pass
            importscenario.save()

            if request.POST.get('action') =='save_and_import':
                return import_scenario_into_flooding(request, importscenario)
        else:
            for field in request.POST:
                #to do: first cehck if not edremark. or edstatus.
                field_ref = InputField.objects.filter(name = field)
                if field_ref.count() ==1:
                    field_ref = field_ref[0]
                    importscenariovalues, new = ImportScenarioInputField.objects.get_or_create(importscenario = importscenario, inputfield = field_ref)
                    importscenariovalues.setValue(request.POST[field])
                    importscenariovalues.validation_remarks = request.POST.get('edremark.'+field)
                    importscenariovalues.state = request.POST.get('edstate.'+field)
                    importscenariovalues.save()
        importscenario.update_scenario_name()
        answer = {'successful':'true', 'post_remarks':'opgeslagen', 'id': importscenario.id}
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")

    else:
        f = []
        k = {} # index
        i = 0
        for header in InputField.HEADER_CHOICES:
            k[header[0]] = len(f)
            f.append({'id': header[0], 'title':header[1],'fields':[]})

        fields = InputField.objects.all().order_by('-position')

        for field in fields:
            value = field.importscenarioinputfield_set.filter(importscenario = importscenario)

            if value.count() > 0:
                f[k[field.header]]['fields'].append(value[0])
            else:
                f[k[field.header]]['fields'].append(field)

    table = ""
    if importscenario.approvalobject:
        table = approvaltable(request,importscenario.approvalobject.id)

    state = importscenario.state

    state_valuemap = {}
    for option in ImportScenario.IMPORT_STATE_CHOICES:
        state_valuemap[option[0]] = option[1]

    state_valuemap = simplejson.dumps(state_valuemap, sort_keys=True)

    post_url = reverse('flooding_tools_import_approve', kwargs={'import_scenario_id': import_scenario_id})

    breadcrumbs = [
        {'name': _('Import tool'), 'url': reverse('flooding_tools_import_overview')},
        {'name': _('Approve import') }]

#    '''
#    'region':
#    'breach;
#    'project'
#    '''

    return render_to_response('import/import_scenario.html',
                              {'fields': f,
                               'action':'approve',
                               'post_url':post_url,
                               'approvaltable' : table,
                               'static_editor': False,
                               'import_admin':True,
                               'state': state,
                               'state_valuemap':state_valuemap,
                               'importscenario':importscenario,
                               'breadcrumbs': breadcrumbs
                               })

def verify_import(request, import_scenario_id):
    """
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """
    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if not (request.user.is_authenticated() and (request.user.has_perm('importtool.can_upload') and importscenario.owner == request.user) or request.user.has_perm('importtool.can_approve')):
        return HttpResponse(_("No permission to approve scenario or login"))

    if request.method == 'POST':

        for field in request.POST:
            field_ref = InputField.objects.filter(name = field)
            if field_ref.count() ==1:
                field_ref = field_ref[0]
                importscenario_inputfield, new = ImportScenarioInputField.objects.get_or_create(importscenario = importscenario, inputfield = field_ref)
                importscenario_inputfield.setValue(request.POST[field])

        importscenario.update_scenario_name()
        answer = {'successful':'true', 'remarks':'opgeslagen', 'id': importscenario.id}
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")

    else:
        f = []
        k = {} # index
        i = 0
        for header in InputField.HEADER_CHOICES:
            k[header[0]] = len(f)
            f.append({'id': header[0], 'title':header[1],'fields':[]})

        fields = InputField.objects.all().order_by('-position')

        for field in fields:
            value = field.importscenarioinputfield_set.filter(importscenario = importscenario)

            if value.count() > 0:
                f[k[field.header]]['fields'].append(value[0])
            else:
                f[k[field.header]]['fields'].append(field)


    if importscenario.state in [ImportScenario.IMPORT_STATE_NONE, ImportScenario.IMPORT_STATE_WAITING, ImportScenario.IMPORT_STATE_ACTION_REQUIRED, ImportScenario.IMPORT_STATE_DISAPPROVED]:
        static_editor = False
    else:
        static_editor = True

    breadcrumbs = [
        {'name': _('Import tool'), 'url': reverse('flooding_tools_import_overview')},
        {'name': _('Verify import') }]

    post_url = reverse('flooding_tools_import_verify', kwargs={'import_scenario_id': import_scenario_id})
    return render_to_response('import/import_scenario.html',
                              {'fields': f,
                               'action':'verify',
                               'post_url':post_url,
                               'static_editor': static_editor,
                               'breadcrumbs': breadcrumbs
                               })

def new_import(request):
    """
    import_scenario_id = None
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """

    if not (request.user.is_authenticated() and request.user.has_perm('importtool.can_upload')):
        return HttpResponse(_("No permission to import scenario or login"))

    if request.method == 'POST':
        approvalobject = ApprovalObject.objects.create(name = "vanuit importtool")
        approvalobject.approvalobjecttype.add(ApprovalObjectType.objects.get(pk = 1)  )
        importscenario = ImportScenario.objects.create(owner=request.user, name = 'nog invullen', approvalobject = approvalobject )

        # loop through all posted fields, search the corresponding
        # input field object. Get or create the importscenario_inputfield
        # and set the value, given in the POST.
        for field in request.POST:
            field_ref = InputField.objects.filter(name = field)
            if field_ref.count() ==1:
                field_ref = field_ref[0]
                importscenario_inputfield, new = ImportScenarioInputField.objects.get_or_create(importscenario = importscenario, inputfield = field_ref)
                importscenario_inputfield.setValue(request.POST[field])

        importscenario.state = ImportScenario.IMPORT_STATE_WAITING
        importscenario.save()
        importscenario.update_scenario_name()
        answer = {'successful':'true', 'remarks':'opgeslagen', 'id': importscenario.id}
        return HttpResponse(simplejson.dumps(answer), mimetype="application/json")

    else:
        form_fields = []
        header_listposition_map = {} # save the position in the form_fields list for each header

        # create the form_fields list (only headers, no fields added)
        # and save for each header the position in the list
        for header in InputField.HEADER_CHOICES:
            header_listposition_map[header[0]] = len(form_fields)
            form_fields.append({'id': header[0], 'title':header[1],'fields':[]})

        fields = InputField.objects.all().order_by('-position')

        # Loop though all the fields an place them and append
        # them at the fields of the correct tuple (so, you need the header)
        for field in fields:
            form_fields[header_listposition_map[field.header]]['fields'].append(field)

    post_url = reverse('flooding_tools_import_new')

    breadcrumbs = [
        {'name': _('Import tool'), 'url': reverse('flooding_tools_import_overview')},
        {'name': _('New import') }]
    return render_to_response('import/import_scenario.html',
                              {'fields': form_fields,
                               'post_url':post_url,
                               'breadcrumbs': breadcrumbs,
                               })



def get_new_filename(filename, dest_filename):
    new_filename = filename
    if dest_filename != None:
        if filename[-3:].lower() == dest_filename[-3:].lower():
            #change filename in case extension is the same. other file names stay untouched
            if dest_filename.find('#')>=0:
                #in case there is place for a number in the dest_filename, copy the number from the source
                b = re.compile(r'(#+)')
                replace = b.findall(dest_filename)[-1]
                b = re.compile(r'([0-9]+)')
                number = '0000000000000' + b.findall(filename)[-1]
                new_filename = dest_filename.replace(replace, number[-len(replace):])
            else:
                new_filename = dest_filename

    return str(new_filename)



def save_uploadfile_in_zipfile_groupimport(upload_zipfile, re_filenames_in_upload_file, dest_zipfile_name, dest_filename_in_zip = None):

    nzf = ZipFile(dest_zipfile_name,mode='w', compression=ZIP_DEFLATED)

    zf = upload_zipfile

    reg_ex = '([0-9]*)'.join([b for b in re_filenames_in_upload_file.split('#') if b != '']).replace('\\','/').replace('+','\+').replace('(','\(').replace(')','\)')

    reg_ex = re.compile(reg_ex , re.I)
    found = False
    for filename in zf.namelist():
        filename = filename.replace('\\','/')
        #write file to new

        if reg_ex.match(filename):
            #remove path
            new_filename = filename.replace('\\','/').split('/')[-1]
            a = get_new_filename(new_filename, dest_filename_in_zip)
            nzf.writestr(a.lower(), zf.read(filename))
            found = True

    nzf.close()
    if not found:
        raise KeyError('File not found')


def save_uploadfile_in_zipfile(upload_file, upload_filename, dest_zipfile_name, dest_filename_in_zip = None):

    nzf = ZipFile(dest_zipfile_name,mode='w', compression=ZIP_DEFLATED)

    if upload_filename[-3:].lower() == u'zip':
        # 'zipfile, check and rename content'
        zf = ZipFile(StringIO(upload_file.read()),'r')
        file_names = zf.namelist()
        for filename in file_names:
            #write file to new
            a = get_new_filename(filename, dest_filename_in_zip)

            nzf.writestr(a, zf.read(filename))
        zf.close()
    else:
        # 'normal file'
        nzf.writestr(get_new_filename(upload_filename, dest_filename_in_zip), upload_file.read())

    nzf.close()

def upload_import_scenario_files(request, import_scenario_id):
    """ Returns the HTML-page for uploading files for an import scenario.

    """
    user = request.user

    if not (request.user.is_authenticated() and request.user.has_perm('importtool.can_upload')):
        return HttpResponse(_("No permission to import scenarios or login"))

    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if request.method == 'POST':
        form = ImportScenarioFileUploadForm(request.POST, request.FILES)
        if form.is_valid():

            # got it only working with creating explicitly the contentfile and saving it
            # as 'file'
            dest_filename = 'testtt.asc'

            for f in request.FILES:
                field_ref = InputField.objects.filter(name = f)[0] #Assumption: filename is unique
                file_content = ContentFile(request.FILES[f].read())
                upload_filename = request.FILES[f].name
                importscenario_filefield, new = ImportScenarioInputField.objects.get_or_create(importscenario = importscenario, inputfield = field_ref)
                #create empty file. replace it later with
                filevalue, new = FileValue.objects.get_or_create(importscenario_inputfield = importscenario_filefield)
                filevalue.value.save(request.FILES[f].name + '.zip', ContentFile(""))
                filevalue.save()
                filevalue.value.close()

                destination =  filevalue.value.file.name
                save_uploadfile_in_zipfile(file_content, upload_filename, destination, field_ref.destination_filename)

            return HttpResponseRedirect(reverse('flooding_tools_import_overview'))


    file_inputfields =  InputField.objects.filter(type=InputField.TYPE_FILE)
    file_inputfields = file_inputfields.order_by('name').reverse()
    file_urls=[]

    for inputfield in file_inputfields:
        importscenario_filefields = ImportScenarioInputField.objects.filter(importscenario = importscenario, inputfield = inputfield)
        for importscenario_filefield in importscenario_filefields:
            # one to one relation
            file_values = FileValue.objects.filter(importscenario_inputfield = importscenario_filefield)
            file_inputfields = file_inputfields.order_by('name')
            for file_value in file_values:
                file_urls += [(file_value.value.name, file_value.importscenario_inputfield.inputfield.name)]
    file_urls = sorted(file_urls, key=operator.itemgetter(1))

    if request.method == 'GET':
        form = ImportScenarioFileUploadForm(file_inputfields)

    return render_to_response('import/import_file_upload.html',
                              {'form': form,
                               'import_scenario_id': import_scenario_id,
                               'file_urls': file_urls})

def group_import(request):
    """ Renders a html with the form for creating a new groupimport

    """

    user = request.user
    if not (request.user.is_authenticated() and request.user.has_perm('importtool.can_upload')):
        return HttpResponse(_("No permission to import scenarios or login"))


    if request.method == 'POST':
        form = GroupImportForm(request.POST, request.FILES)
        if form.is_valid():
            # create a GroupImport object and fill it
            groupimport = GroupImport(
                                       name = form.cleaned_data['name'],
                                       table = None,
                                       results = None,
                                      )

            groupimport.save()
            # got it only working with creating explicitly the contentfile and saving it
            # as 'file'
            table_file_content = ContentFile(request.FILES['table'].read())
            groupimport.table.save(request.FILES['table'].name, table_file_content)
            result_file_content = ContentFile(request.FILES['results'].read())
            groupimport.results.save(request.FILES['results'].name, result_file_content)
            groupimport.save()

            # Handle the input from the uploaded files
            remarks = []
            remarks.append('inladen')
            method = 2

            try:
                if method == 1:
                    pass
                else:

                    import xlrd

                    wb = xlrd.open_workbook(groupimport.table.path)
                    sheet = wb.sheet_by_name('import scenarios')

                    nr_rows = sheet.nrows
                    nr_cols = sheet.ncols

                    #combine fields with ImportField
                    field_dict = {}
                    colnr = 1
                    for fieldname in sheet.row_slice(1,1):
                        try:
                            inputfield = InputField.objects.get(name = fieldname.value)
                            field_dict[colnr] = inputfield

                        except InputField.DoesNotExist, e:
                            remarks.append('veld ' +fieldname.value+ ' komt niet voor in de database')

                        colnr = colnr + 1

                    nr_cols_field = colnr

                    zip_file = ZipFile(groupimport.results.path, "r")
                    for rownr in range(4, nr_rows):
                        row = sheet.row_slice(rownr)


                        if row[0].value == 'x':
                            scenario_name = "geen"

                            # eerst een import scenario maken
                            approvalobject = ApprovalObject.objects.create(name =  scenario_name)
                            approvalobject.approvalobjecttype.add(ApprovalObjectType.objects.get(pk = 1))
                            importscenario = ImportScenario.objects.create(owner=request.user, name =  scenario_name, approvalobject = approvalobject, groupimport = groupimport )

                            #vervolgens de velden opslaan
                            for col_nr in range(1, min(len(row), nr_cols_field)):
                                field = row[col_nr]
                                if field_dict.has_key(col_nr) and not field.ctype == 'empty' and not field.value == '':
                                    importscenario_inputfield, new = ImportScenarioInputField.objects.get_or_create(importscenario = importscenario, inputfield = field_dict[col_nr])
                                    try:
                                        importscenario_inputfield.setValue(field.value, field.ctype)
                                    except ValueError, e:
                                        remarks.append('Value error. Rij %i, kollom  \'%s\' van type %s. Waarde is: \'%s\'. error: %s'%(rownr, field_dict[col_nr].name, field_dict[col_nr].get_type_display(), str(field.value), e))
                                    except TypeError, e:
                                        remarks.append('Type error. Rij %i, kollom  \'%s\' van type %s. Waarde is: \'%s\'. error: %s'%(rownr, field_dict[col_nr].name, field_dict[col_nr].get_type_display(), str(field.value), e))


                                    if field_dict[col_nr].type == InputField.TYPE_FILE:
                                        try:
                                            filevalue, new = FileValue.objects.get_or_create(importscenario_inputfield = importscenario_inputfield)
                                            #create empty file. replace it later with zipfile
                                            filevalue.value.save(field.value.replace('\\','/').split('/')[-1] + '.zip', ContentFile(""))
                                            filevalue.save()
                                            filevalue.value.close()

                                            destination =  filevalue.value.file.name
                                            save_uploadfile_in_zipfile_groupimport(zip_file, field.value, destination, field_dict[col_nr].destination_filename)

                                        except KeyError, e:
                                            remarks.append('File \'%s\' niet gevonden in zipfile. Rij %i, kollom  \'%s\'. '%( str(field.value),rownr, field_dict[col_nr].name))
                                            filevalue.delete()


                            importscenario.update_scenario_name()


                #to do. check of files aanwezig in zipfile
                remarks.append('klaar met inladen')
                succeeded = True
            except BadZipfile, e:
                remarks.append("error bij inlezen. De zip-file kan niet gelezen worden. De gegevens zijn wel opgeslagen, maar kunnen niet verwerkt worden. Neem contact op met de applicatiebeheerder en vermeld het group-import nummer %i"%groupimport.id)
            except Exception, e:
                remarks.append("error bij inlezen: %s. De gegevens zijn wel opgeslagen, maar kunnen niet verwerkt worden. Neem contact op met de applicatiebeheerder en vermeld het group-import nummer %i"% (str(e), groupimport.id))

            remarks.append('<a href="%s">ga terug naar importoverzicht</a>'%reverse('flooding_tools_import_overview'))

            return HttpResponse('<br>'.join(remarks))
    else:
        form = GroupImportForm()

    breadcrumbs = [
        {'name': _('Import tool'), 'url': reverse('flooding_tools_import_overview')},
        {'name': _('Group import') }]

    return render_to_response('import/groupimport_new.html',
                              {'form': form,
                               'breadcrumbs': breadcrumbs})


def group_import_example_csv(request):
    """ Returns an example csv file that can be used for creating a group import

    """
    import csv
    csv_file = open('groupimport.csv', 'wb')
    writer = csv.writer(csv_file)
    lines = group_import_example(request)
    for line in lines:
        writer.writerows(line)
    csv_file.close()

    csv_file = open('groupimport.csv', 'wb')
    writer = csv.writer(csv_file)
    # read created csv file for sending it over html
    csv_file = open('groupimport.csv', 'rb')
    response = HttpResponse(csv_file.read(), mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=groupimport.csv'
    csv_file.close()

    return  response



def group_import_example_excel(request):
    """ Returns an example excel file that can be used for creating a group import

    """
    if not (request.user.is_authenticated() and request.user.has_perm('importtool.can_upload')):
        return HttpResponse(_("No permission to import scenarios or login"))

    import xlwt as excel

    wb = excel.Workbook()
    ws = wb.add_sheet('import scenarios')

    font0 = excel.Formatting.Font()
    font0.name = 'Arial'
    font0.height = 200

    font1 = excel.Formatting.Font()
    font1.name = 'Arial'
    font1.height = 200
    font1.bold = True

    font2 = excel.Formatting.Font()
    font2.name = 'Arial'
    font2.height = 160

    font3 = excel.Formatting.Font()
    font3.name = 'Arial'
    font3.height = 160
    #font3.outline = True

    borders = excel.Borders()
    borders.bottom = 10

    st0 = excel.XFStyle()
    st1 = excel.XFStyle()
    st2 = excel.XFStyle()
    st3 = excel.XFStyle()

    st0.font = font0
    st1.font = font1
    st2.font = font2
    st3.font = font3
    st3.borders = borders

    wb.add_style(st0)
    wb.add_style(st1)
    wb.add_style(st2)
    wb.add_style(st3)

    lines = group_import_example(request)

    ws.write( 1, 0, "actief", st1)
    ws.write( 3, 0, "vul hier een 'x' in als regel meegenomen moet worden", st3)

    i = 1
    for field in lines[0][0]:
        ws.write( 0, i, field, st0)
        i = i + 1
    i = 1
    for field in lines[1][0]:
        ws.write( 1, i, field, st1)
        #ws.col(i).width = hex(len(field)*8)
        i = i + 1
    i = 1
    for field in lines[2][0]:
        ws.write( 2, i, field, st2)
        i = i + 1
    i = 1
    for field in lines[3][0]:
        if field.lower() != 'none':
            ws.write( 3, i, field, st3)
        else:
            ws.write( 3, i, "", st3)
        i = i + 1

    buffer = StringIO()
    wb.save(buffer)
    del wb
    buffer.seek(0)

    response = HttpResponse(buffer.read(), mimetype='xls')
    response['Content-Disposition'] = 'attachment; filename=groupimport.xls'

    return  response


def group_import_example(request):
    """ Returns an example lines and fields that can be used for creating a group import

    """
    inputfields = InputField.objects.order_by('header', 'position')
    lines = []
    lines.append([[str(f.get_header_display()) for f in inputfields]])
    lines.append([[str(f.name) for f in inputfields]])
    lines.append([[str(f.get_type_display()) for f in inputfields]])
    lines.append([[str(f.excel_hint) for f in inputfields]])
    return lines


def import_scenario_into_flooding(request, importscenario):
    """ import importscenario into flooding database

    """

    #attachments
    if importscenario.region == None or importscenario.breach == None or importscenario.project == None:
        answer = {'successful': False,
                  'save_log': 'instellingen voor region, breach of project missen' % importscenario.id }
        return HttpResponse(simplejson.dumps(answer))


    import_values = {}
    for field in importscenario.importscenarioinputfield_set.all():
        if not import_values.has_key(field.inputfield.destination_table):
            import_values[field.inputfield.destination_table]={}
        import_values[field.inputfield.destination_table][field.inputfield.destination_field]=field.getValue()

    scenario_values = import_values.get('Scenario',{})

    if importscenario.scenario is not None:
        scenario = importscenario.scenario
    else:
        scenario = Scenario.objects.create(  approvalobject=importscenario.approvalobject,
                                               name= str(scenario_values.get("name","-")),
                                               owner= importscenario.owner,
                                               remarks= str(scenario_values.get("remarks","")),
                                               project= importscenario.project,
                                               sobekmodel_inundation= SobekModel.objects.get(pk=1),#only link to dummy is possible
                                               tsim= float(scenario_values.get("tsim",0)),
                                               #calcpriority
                                               code="2impsc_" + str(importscenario.id) )
        importscenario.scenario = scenario
        importscenario.save()

    task_create = Task.objects.create( scenario = scenario, tasktype = TaskType.objects.get(pk = 60),
                                              remarks="import scenario",
                                              creatorlog='uploaded by %s'%importscenario.owner.get_full_name(),
                                              tstart=datetime.datetime.now() )


    scenario_values = import_values.get('ScenarioBreach',{})

    scenariobreach, new = ScenarioBreach.objects.get_or_create( scenario = scenario, breach = importscenario.breach,
                                               defaults={
                                               "waterlevelset": WaterlevelSet.objects.get(pk=1),#only linking to dummy is possible
                                               #sobekmodel_externalwater
                                               "widthbrinit": scenario_values.get("widthbrinit",-999),
                                               "methstartbreach": scenario_values.get("methstartbreach",2),
                                               "tstartbreach": scenario_values.get("tstartbreach",0),
                                               "hstartbreach": scenario_values.get("hstartbreach",-999),
                                               "brdischcoef": scenario_values.get("brdischcoef",-999),
                                               "brf1": scenario_values.get("brf1",-999),
                                               "brf2": scenario_values.get("brf2",-999),
                                               "bottomlevelbreach": scenario_values.get("bottomlevelbreach",-999),
                                               "ucritical": scenario_values.get("ucritical",-999),
                                               "pitdepth": scenario_values.get("pitdepth",-999),
                                               "tmaxdepth": scenario_values.get("tmaxdepth",0),
                                               "extwmaxlevel": scenario_values.get("extwmaxlevel",-999),
                                               "extwbaselevel": scenario_values.get("extwbaselevel",None),
                                               "extwrepeattime": scenario_values.get("extwrepeattime",None),
                                               #"tide": scenario_values.get("",""),
                                               "tstorm": scenario_values.get("tstorm",None),
                                               "tpeak": scenario_values.get("tpeak",None),
                                               "tdeltaphase": scenario_values.get("tdeltaphase",None),
                                               "code": "2impsc_" + str(importscenario.id) })

    #ExtraScenarioInfo
    scenario_values = import_values.get('ExtraScenarioInfo',{})
    for extra_field_name in scenario_values.keys():
        extrainfofield, new = ExtraInfoField.objects.get_or_create(name = extra_field_name)
        extrascenarioinfo, new = ExtraScenarioInfo.objects.get_or_create(extrainfofield = extrainfofield, scenario = scenario, defaults = {"value":" " })
        extrascenarioinfo.value = str(scenario_values.get(extra_field_name," "))
        extrascenarioinfo.save()

    #results
    scenario_values = import_values.get('Result',{})
    for resulttype_id, value in scenario_values.items():
        result, new = Result.objects.get_or_create( scenario = scenario, resulttype = ResultType.objects.get(pk=int(resulttype_id)),
                                               defaults={
                                               "resultloc": "-" ,
                                               "deltat":1/24})


        dest_file_rel = os.path.join(scenario.get_rel_destdir(), os.path.split(value)[1])

        dest_file = os.path.join(Setting.objects.get( key = 'destination_dir' ).value, dest_file_rel)
        dest_file = dest_file.replace('\\', '/')

        dest_path = os.path.dirname(dest_file)

        if not os.path.isdir( dest_path ):
            os.makedirs( dest_path )

        result.resultloc =  dest_file_rel
        result.save()

        # Replace \ by / so that it works on both Linux and Windows

        # The directory
        # /p-flod-fs-00-d1.external-nens.local/flod-share/ was created
        # on both flooding webservers to make a path like that work on
        # both sides.
        value = value.replace('\\', '/')
        dest_file = dest_file.replace('\\', '/')

        logger.debug("VALUE = "+value)
        logger.debug("DEST_FILE = "+dest_file)
        copyfile(value, dest_file)


    task_create.tfinished = datetime.datetime.now()
    task_create.successful = True
    task_create.save()

    Task.objects.create( scenario = scenario, tasktype = TaskType.objects.get(pk = 130),
                                              remarks="import scenario",
                                              creatorlog='imported by %s'%request.user.get_full_name(),
                                              tstart=datetime.datetime.now(),
                                              tfinished=datetime.datetime.now(),
                                              successful=True
                                              )
    scenario.update_status()

    importscenario.state = ImportScenario.IMPORT_STATE_IMPORTED
    importscenario.save()

    answer = {'successful':True, 'save_log':'migratie compleet. scenario id is: %i' % scenario.id }
    return HttpResponse(simplejson.dumps(answer))
