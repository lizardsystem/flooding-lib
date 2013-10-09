from cStringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED, BadZipfile
import datetime
import functools
import logging
import operator
import os
import re
import xlrd

from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.conf import settings
from django.utils.translation import ugettext as _

from flooding_base.models import Text
from flooding_lib.models import Breach
from flooding_lib.models import Project
from flooding_lib.models import Region
from flooding_lib.tools.approvaltool.models import ApprovalObject
from flooding_lib.tools.approvaltool.models import ApprovalObjectType
from flooding_lib.tools.approvaltool.views import approvaltable
from flooding_lib.tools.importtool.forms import GroupImportForm
from flooding_lib.tools.importtool.forms import ImportScenarioFileUploadForm
from flooding_lib.tools.importtool.models import FileValue
from flooding_lib.tools.importtool.models import GroupImport
from flooding_lib.tools.importtool.models import ImportScenario
from flooding_lib.tools.importtool.models import ImportScenarioInputField
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.importtool.models import RORKering
from flooding_lib.util.files import remove_comments_from_asc_files

logger = logging.getLogger(__name__)


def checks_permission(permission, message):
    """Decorator that can be used on a view. If it is, the view checks
    whether the user is logged in and has permission 'permission'. If
    user doesn't, the message 'message' is returned.

    If permission is a tuple, check if user has one of the permissions
    in it."""

    def permission_checking_decorator(f):
        @functools.wraps(f)
        def wrapper(request, *args, **kwargs):
            if isinstance(permission, tuple):
                permissions = permission
            else:
                permissions = (permission,)

            if not (request.user.is_authenticated() and
                    any(request.user.has_perm(perm)
                        for perm in permissions)):
                return HttpResponse(message)
            return f(request, *args, **kwargs)
        return wrapper
    return permission_checking_decorator


@checks_permission(
    ('importtool.can_upload', 'importtool.can_approve'),
    _("No permission to upload data or login"))
def overview(request):
    """
    Renders Lizard-flooding import page, contains among others
    an overview of the imported scenarios.
    """
    has_approve_rights = False

    if request.user.has_perm('importtool.can_approve'):
        #show all uploaded scenarios
        importscenarios = ImportScenario.objects.filter()
        has_approve_rights = True
    else:
        #show only own uploaded scenarios
        importscenarios = ImportScenario.objects.filter(owner=request.user)

    import_scenarios_list = []
    for import_scenario in importscenarios.order_by(
        'state', 'creation_date', 'id'):
        try:
            group_name = import_scenario.groupimport.name
        except AttributeError:
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
        {'name': _('Import tool')}
        ]

    return render_to_response('import/imports_overview.html',
                              {'import_scenarios_list': import_scenarios_list,
                               'breadcrumbs': breadcrumbs,
                               'has_approve_rights': has_approve_rights
                               })


@checks_permission(
    'importtool.can_approve', _("No permission to approve scenario or login"))
def approve_import(request, import_scenario_id):
    """
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """
    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if request.method == 'POST':
        if (request.POST.get('action') == 'save_admin' or
            request.POST.get('action') == 'save_and_import'):
            importscenario.state = request.POST.get('state')
            breach = request.POST.get('breach', None)
            project = request.POST.get('project', None)
            region = request.POST.get('region', None)
            importscenario.validation_remarks = request.POST.get(
                'remarks', None)
            if breach != None and breach != 'null':
                try:
                    importscenario.breach = Breach.objects.get(pk=int(breach))
                except Breach.DoesNotExist:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass

            if project != None and project != 'null':
                try:
                    importscenario.project = Project.objects.get(
                        pk=int(project))
                except Project.DoesNotExist:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass

            if region != None and region != 'null':
                try:
                    importscenario.region = Region.objects.get(pk=int(region))
                except Region.DoesNotExist:
                    pass
                except ValueError:
                    pass
                except TypeError:
                    pass
            importscenario.save()

            if request.POST.get('action') == 'save_and_import':
                return import_scenario_into_flooding(request, importscenario)
        else:
            for field in request.POST:
                logger.debug("FIELD: {0}".format(field))
                #to do: first cehck if not edremark. or edstatus.
                field_ref = InputField.objects.filter(name=field)
                if field_ref.count() == 1:
                    field_ref = field_ref[0]
                    importscenariovalues, new = (
                        ImportScenarioInputField.objects.get_or_create(
                            importscenario=importscenario,
                            inputfield=field_ref))
                    importscenariovalues.setValue(request.POST[field])
                    importscenariovalues.validation_remarks = request.POST.get(
                        'edremark.' + field, '')
                    importscenariovalues.state = request.POST.get(
                        'edstate.' + field, True)
                    importscenariovalues.save()
        importscenario.update_scenario_name()
        importscenario.save()
        answer = {
            'successful': 'true',
            'post_remarks': 'opgeslagen',
            'id': importscenario.id
            }
        return HttpResponse(
            simplejson.dumps(answer),
            mimetype="application/json")

    else:
        f = []
        k = {}  # index

        for header in InputField.HEADER_CHOICES:
            k[header[0]] = len(f)
            f.append({
                    'id': header[0],
                    'title': unicode(header[1]),
                    'fields': []})

        fields = InputField.objects.all().order_by('-position')

        for field in fields:
            value = field.importscenarioinputfield_set.filter(
                importscenario=importscenario)

            if value.count() > 0:
                f[k[field.header]]['fields'].append(value[0])
            else:
                f[k[field.header]]['fields'].append(field)

    table = ""
    if importscenario.approvalobject:
        table = approvaltable(request, importscenario.approvalobject.id)

    state = importscenario.state

    state_valuemap = {}
    for option in ImportScenario.IMPORT_STATE_CHOICES:
        state_valuemap[option[0]] = unicode(option[1])

    state_valuemap = simplejson.dumps(state_valuemap, sort_keys=True)

    post_url = reverse(
        'flooding_tools_import_approve',
        kwargs={'import_scenario_id': import_scenario_id})

    breadcrumbs = [
        {'name': _('Import tool'),
         'url': reverse('flooding_tools_import_overview')},
        {'name': _('Approve import')}]

#    '''
#    'region':
#    'breach;
#    'project'
#    '''

    return render_to_response(
        'import/import_scenario.html',
        {'fields': f,
         'action': 'approve',
         'post_url': post_url,
         'approvaltable': table,
         'static_editor': False,
         'import_admin': True,
         'state': state,
         'state_valuemap': state_valuemap,
         'importscenario': importscenario,
         'breadcrumbs': breadcrumbs
         })


def verify_import(request, import_scenario_id):
    """
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """
    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if (not (request.user.is_authenticated() and
            (request.user.has_perm('importtool.can_upload') and
             importscenario.owner == request.user) or
             request.user.has_perm('importtool.can_approve'))):
        return HttpResponse(_("No permission to approve scenario or login"))

    if request.method == 'POST':

        for field in request.POST:
            field_ref = InputField.objects.filter(name=field)
            if field_ref.count() == 1:
                field_ref = field_ref[0]
                importscenario_inputfield, new = (
                    ImportScenarioInputField.objects.get_or_create(
                        importscenario=importscenario, inputfield=field_ref))
                importscenario_inputfield.setValue(request.POST[field])

        importscenario.update_scenario_name()
        importscenario.save()

        answer = {
            'successful': 'true',
            'remarks': 'opgeslagen',
            'id': importscenario.id}
        return HttpResponse(
            simplejson.dumps(answer), mimetype="application/json")

    else:
        f = []
        k = {}  # index

        for header in InputField.HEADER_CHOICES:
            k[header[0]] = len(f)
            f.append({
                    'id': header[0],
                    'title': unicode(header[1]),
                    'fields': []})

        fields = InputField.objects.all().order_by('-position')

        for field in fields:
            value = field.importscenarioinputfield_set.filter(
                importscenario=importscenario)

            if value.count() > 0:
                f[k[field.header]]['fields'].append(value[0])
            else:
                f[k[field.header]]['fields'].append(field)

    if importscenario.state in [
        ImportScenario.IMPORT_STATE_NONE,
        ImportScenario.IMPORT_STATE_WAITING,
        ImportScenario.IMPORT_STATE_ACTION_REQUIRED,
        ImportScenario.IMPORT_STATE_DISAPPROVED]:
        static_editor = False
    else:
        static_editor = True

    breadcrumbs = [
        {'name': _('Import tool'), 'url':
         reverse('flooding_tools_import_overview')},
        {'name': _('Verify import')}]

    post_url = reverse(
        'flooding_tools_import_verify',
        kwargs={'import_scenario_id': import_scenario_id})

    return render_to_response(
        'import/import_scenario.html',
        {'fields': f,
         'action': 'verify',
         'post_url': post_url,
         'static_editor': static_editor,
         'breadcrumbs': breadcrumbs
         })


@checks_permission('importtool.can_upload',
                   _("No permission to import scenario or login"))
def new_import(request):
    """
    import_scenario_id = None
    Renders Lizard-flooding page for verifying the data of a proposed
    scenario import. The administrator has to verify the results.
    """

    if request.method == 'POST':
        return post_new_import(request.POST, request.user)

    post_url = reverse('flooding_tools_import_new')

    legend_html_json = simplejson.dumps(
        Text.get('importnewscenario', request=request))

    breadcrumbs = [
        {'name': _('Import tool'),
         'url': reverse('flooding_tools_import_overview')},
        {'name': _('New import')}]

    return render_to_response(
        'import/import_scenario.html',
        {'fields': InputField.grouped_input_fields(),
         'post_url': post_url,
         'breadcrumbs': breadcrumbs,
         'legend_html_json': legend_html_json,
         })


def post_new_import(posted_values, owner):
    """Handles POSTing of the form. Does no validation, we rely on
    Javascript for that (!)."""

    approvalobject = ApprovalObject.objects.create(
        name="vanuit importtool")
    approvalobject.approvalobjecttype.add(
        ApprovalObjectType.default_approval_type())
    importscenario = ImportScenario.objects.create(
        owner=owner, name='-',
        approvalobject=approvalobject)

    importscenario.receive_input_fields(posted_values)
    importscenario.update_scenario_name()
    importscenario.save()

    answer = {
        'successful': 'true',
        'remarks': 'opgeslagen',
        'id': importscenario.id}

    return HttpResponse(
        simplejson.dumps(answer),
        mimetype="application/json")


def get_new_filename(filename, dest_filename):
    new_filename = filename
    if dest_filename != None:
        if filename[-3:].lower() == dest_filename[-3:].lower():
            # change filename in case extension is the same. other file
            # names stay untouched
            if dest_filename.find('#') >= 0:
                # in case there is place for a number in the
                # dest_filename, copy the number from the source
                b = re.compile(r'(#+)')
                replace = b.findall(dest_filename)[-1]
                b = re.compile(r'([0-9]+)')
                number = '0000000000000' + b.findall(filename)[-1]
                new_filename = dest_filename.replace(
                    replace, number[-len(replace):])
            else:
                new_filename = dest_filename

    return str(new_filename)


def save_uploadfile_in_zipfile_groupimport(
    upload_zipfile, re_filenames_in_upload_file,
    dest_zipfile_name, dest_filename_in_zip=None):

    nzf = ZipFile(dest_zipfile_name, mode='w', compression=ZIP_DEFLATED)

    zf = upload_zipfile

    reg_ex = '([0-9]*)'.join(
        [b for b in re_filenames_in_upload_file.split('#') if b != ''])
    reg_ex = (reg_ex.replace('\\', '/').replace('+', '\+').
              replace('(', '\(').replace(')', '\)'))

    reg_ex = re.compile(reg_ex, re.I)
    found = False
    for filename in zf.namelist():
        filename = filename.replace('\\', '/')
        # write file to new

        if reg_ex.match(filename):
            # remove path
            new_filename = filename.replace('\\', '/').split('/')[-1]
            a = get_new_filename(new_filename, dest_filename_in_zip)
            nzf.writestr(a.lower(), zf.read(filename))
            found = True

    nzf.close()

    # Remove comment line from .asc and .inc files after uploading
    remove_comments_from_asc_files(os.path.dirname(dest_zipfile_name))

    if not found:
        raise KeyError('File not found')


def save_uploadfile_in_zipfile(
    upload_file, upload_filename,
    dest_zipfile_name, dest_filename_in_zip=None):

    nzf = ZipFile(dest_zipfile_name, mode='w', compression=ZIP_DEFLATED)

    if upload_filename[-3:].lower() == u'zip':
        # 'zipfile, check and rename content'
        zf = ZipFile(StringIO(upload_file.read()), 'r')
        file_names = zf.namelist()
        for filename in file_names:
            #write file to new
            a = get_new_filename(filename, dest_filename_in_zip)

            nzf.writestr(a, zf.read(filename))
        zf.close()
    else:
        # 'normal file'
        nzf.writestr(
            get_new_filename(upload_filename, dest_filename_in_zip),
            upload_file.read())

    nzf.close()

    # Remove comment line from .asc and .inc files after uploading
    remove_comments_from_asc_files(os.path.dirname(dest_zipfile_name))


@checks_permission('importtool.can_upload',
                   _("No permission to import scenario or login"))
def upload_import_scenario_files(request, import_scenario_id):
    """ Returns the HTML-page for uploading files for an import scenario.

    """
    importscenario = get_object_or_404(ImportScenario, pk=import_scenario_id)

    if request.method == 'POST':
        # Get form from request
        form = ImportScenarioFileUploadForm(request.POST, request.FILES)

        # If it's valid, process it
        if form.is_valid():
            return post_upload_import_scenario_files(
                form, request.FILES, importscenario)

    breadcrumbs = [
        {'name': _('Import tool'),
         'url': reverse('flooding_tools_import_overview')},
        {'name': _('Add files')}]

    file_inputfields = InputField.objects.filter(type=InputField.TYPE_FILE)
    file_inputfields = file_inputfields.order_by('name').reverse()
    file_urls = []

    for inputfield in file_inputfields:
        importscenario_filefields = ImportScenarioInputField.objects.filter(
            importscenario=importscenario, inputfield=inputfield)
        for importscenario_filefield in importscenario_filefields:
            # one to one relation
            file_values = FileValue.objects.filter(
                importscenario_inputfield=importscenario_filefield)
            file_inputfields = file_inputfields.order_by('name')
            for file_value in file_values:
                file_urls += [(
                        file_value.value.name,
                        file_value.importscenario_inputfield.inputfield.name)]

    file_urls = sorted(file_urls, key=operator.itemgetter(1))

    if request.method == 'GET':
        form = ImportScenarioFileUploadForm(file_inputfields)

    return render_to_response('import/import_file_upload.html',
                              {'form': form,
                               'breadcrumbs': breadcrumbs,
                               'import_scenario_id': import_scenario_id,
                               'file_urls': file_urls})


def post_upload_import_scenario_files(form, files, importscenario):
    # got it only working with creating explicitly the
    # contentfile and saving it as 'file'
    destination_dirs = set()

    for filename in files:
        field_ref = InputField.objects.filter(
            name=filename)[0]  # Assumption: filename is unique
        file_content = ContentFile(files[filename].read())
        upload_filename = files[filename].name
        importscenario_filefield, new = (
            ImportScenarioInputField.objects.get_or_create(
                importscenario=importscenario, inputfield=field_ref))
        # create empty file. replace it later with
        filevalue, new = (
            FileValue.objects.get_or_create(
                importscenario_inputfield=importscenario_filefield))
        filevalue.value.save(
            files[filename].name + '.zip', ContentFile(""))
        filevalue.save()
        filevalue.value.close()

        destination = filevalue.value.file.name
        save_uploadfile_in_zipfile(
            file_content, upload_filename,
            destination, field_ref.destination_filename)
        destination_dirs.add(os.path.dirname(destination))

    return render_to_response(
        'import/import_file_upload_success.html', {
            'import_scenario_id': importscenario.id,
            'url': reverse('flooding_tools_import_overview'),
            })


@checks_permission('importtool.can_upload',
                   _("No permission to import scenario or login"))
def group_import(request):
    """Renders a html with the form for creating a new groupimport
    """

    if request.method == 'POST':
        form = GroupImportForm(request.POST, request.FILES)
        if form.is_valid():
            return post_group_import(request, form)
    else:
        form = GroupImportForm()

    breadcrumbs = [
        {'name': _('Import tool'),
         'url': reverse('flooding_tools_import_overview')},
        {'name': _('Group import')}]

    return render_to_response('import/groupimport_new.html',
                              {'form': form,
                               'breadcrumbs': breadcrumbs})


def post_group_import(request, form):
    """create a GroupImport object and fill it"""
    groupimport = GroupImport(
        name=form.cleaned_data['name'],
        table=None,
        results=None)

    groupimport.save()
    # got it only working with creating explicitly the
    # contentfile and saving it as 'file'
    table_file_content = ContentFile(request.FILES['table'].read())
    groupimport.table.save(
        request.FILES['table'].name, table_file_content)
    result_file_content = ContentFile(request.FILES['results'].read())
    groupimport.results.save(
        request.FILES['results'].name, result_file_content)
    groupimport.save()

    # Handle the input from the uploaded files
    remarks = []
    remarks.append('inladen')
    method = 2

    try:
        if method == 1:
            pass
        else:
            wb = xlrd.open_workbook(groupimport.table.path)
            sheet = wb.sheet_by_name('import scenarios')

            nr_rows = sheet.nrows

            #combine fields with ImportField
            field_dict = {}
            colnr = 1
            for fieldname in sheet.row_slice(1, 1):
                try:
                    # Use name__iexact so case doesn't have to
                    # be exactly right
                    inputfield = InputField.objects.get(
                        name__iexact=fieldname.value)
                    field_dict[colnr] = inputfield

                except InputField.DoesNotExist, e:
                    remarks.append('veld ' + fieldname.value +
                                   ' komt niet voor in de database')

                colnr = colnr + 1

            nr_cols_field = colnr

            zip_file = ZipFile(groupimport.results.path, "r")
            for rownr in range(4, nr_rows):
                row = sheet.row_slice(rownr)

                if row[0].value == 'x':
                    scenario_name = "geen"

                    # eerst een import scenario maken
                    approvalobject = ApprovalObject.objects.create(
                        name=scenario_name)
                    approvalobject.approvalobjecttype.add(
                        ApprovalObjectType.default_approval_type())
                    importscenario = ImportScenario.objects.create(
                        owner=request.user, name=scenario_name,
                        approvalobject=approvalobject,
                        groupimport=groupimport)

                    # vervolgens de velden opslaan
                    for col_nr in range(1, min(len(row), nr_cols_field)):
                        field = row[col_nr]
                        if (col_nr in field_dict and
                            field.ctype != 'empty' and
                            field.value != ''):
                            importscenario_inputfield, new = (
                                ImportScenarioInputField.objects.
                                get_or_create(
                                    importscenario=importscenario,
                                    inputfield=field_dict[col_nr]))
                            try:
                                value = field.value

                                # Excel does bugged things with dates,
                                # always use xl_date_as_tuple to correct them
                                # Convert it to a string immediately
                                if field.ctype == 'date':
                                    datetime_tuple = xlrd.xldate_as_tuple(
                                        field.value, wb.datemode)
                                    # Throw away time fields, it's not
                                    # a datetime it's a date
                                    date_only = datetime_tuple[:3]
                                    value = (
                                        datetime.date(date_only).isoformat())
                                importscenario_inputfield.setValue(value)
                            except ValueError as e:
                                remarks.append(
                                    ("Value error. Rij %i, kolom "
                                     " '%s' van type %s. Waarde "
                                     "is: '%s'. error: %s") % (
                                        rownr,
                                        field_dict[col_nr].name,
                                        field_dict[col_nr].
                                        get_type_display(),
                                        str(field.value), e))
                            except TypeError as e:
                                remarks.append(
                                    ("Type error. Rij %i, kolom"
                                     "  '%s' van type %s. Waarde "
                                     "is: \'%s\'. error: %s") % (
                                        rownr,
                                        field_dict[col_nr].name,
                                        field_dict[col_nr].
                                        get_type_display(),
                                        str(field.value), e))

                            if (field_dict[col_nr].type ==
                                InputField.TYPE_FILE):
                                try:
                                    filevalue, new = (
                                        FileValue.objects.
                                        get_or_create(
                       importscenario_inputfield=importscenario_inputfield))
                                    #create empty
                                    #file. replace it later
                                    #with zipfile
                                    filevalue.value.save(
                                        field.value.replace('\\', '/').
                                        split('/')[-1] + '.zip',
                                        ContentFile(""))
                                    filevalue.save()
                                    filevalue.value.close()

                                    destination = (filevalue.value.
                                                   file.name)
                                    save_uploadfile_in_zipfile_groupimport(
                                        zip_file, field.value,
                                        destination,
                                        field_dict[col_nr].
                                        destination_filename)

                                except KeyError, e:
                                    remarks.append(
                                        ("File '%s' niet gevonden in "
                                         "zipfile. Rij %i, kolom '%s'. ") %
                                        (str(field.value),
                                         rownr, field_dict[col_nr].name))
                                    filevalue.delete()

                    importscenario.update_scenario_name()
                    importscenario.save()

        #to do. check of files aanwezig in zipfile
        remarks.append('klaar met inladen')
    except BadZipfile, e:
        remarks.append((
                "error bij inlezen. De zip-file kan niet gelezen "
                "worden. De gegevens zijn wel opgeslagen, maar kunnen "
                "niet verwerkt worden. Neem contact op met de "
                "applicatiebeheerder en vermeld het group-import "
                "nummer %i") % groupimport.id)
    except Exception, e:
        remarks.append(
            ("error bij inlezen: %s. De gegevens zijn wel "
             "opgeslagen, maar kunnen niet verwerkt worden."
             " Neem contact op met de applicatiebeheerder "
             "en vermeld het group-import nummer %i") %
            (str(e), groupimport.id))

    remarks.append('<a href="%s">ga terug naar importoverzicht</a>' %
                   reverse('flooding_tools_import_overview'))

    return HttpResponse('<br>'.join(remarks))


def group_import_example_csv(request):
    """ Returns an example csv file that can be used for creating a
    group import
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


def group_import_example(request):
    """ Returns an example lines and fields that can be used for
    creating a group import
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

    username = request.user.get_full_name()
    success, save_log = importscenario.import_into_flooding(username)

    return HttpResponse(simplejson.dumps({
                'successful': success,
                'save_log': save_log}))


def ror_keringen_page(request):
    """ Show ror-keringen. """
    if not (request.user.is_authenticated()):
        return HttpResponse(_("Not authenticated."))

    
    files = os.listdir(settings.ROR_KERINGEN_APPLIED_PATH)
    keringen_file_names = [
        {'id': files.index(f),
         'name': f,
         'path': reverse('flooding_ror_keringen_download', kwargs={'filename': f})} for f in files]

    breadcrumbs = [
        {'name': _('Importtool'),
         'url': reverse('flooding_tools_import_overview')},
        {'name': _('Down- upload ROR-keringen en wateren')}]
    return render_to_response('import/down_upload_ror_keringen.html',
                              {'breadcrumbs': breadcrumbs,
                               'keringen_file_names': keringen_file_names})
