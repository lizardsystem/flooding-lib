import logging
import os
import os.path
from shutil import copyfile

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import simplejson
from django.utils.translation import ugettext as _

from flooding_base.models import Setting
from flooding_lib.dates import get_dayfloat_from_intervalstring
from flooding_lib.dates import get_intervalstring_from_dayfloat
from flooding_lib.models import Breach
from flooding_lib.models import ExtraInfoField
from flooding_lib.models import ExtraScenarioInfo
from flooding_lib.models import Project
from flooding_lib.models import Region
from flooding_lib.models import Result
from flooding_lib.models import ResultType
from flooding_lib.models import Scenario
from flooding_lib.models import ScenarioBreach
from flooding_lib.models import SobekModel
from flooding_lib.models import WaterlevelSet
from flooding_lib.tools.approvaltool.models import ApprovalObject


logger = logging.getLogger(__name__)


def get_groupimport_table_path(instance, filename):
    """
    Method that functions as a callback method to set dynamically the path
    for the table-file for the groupimport.

    """

    return os.path.join(
        'import', 'groupimport', str(instance.id), 'tablefile', filename)


def get_groupimport_result_path(instance, filename):
    """
    Method that functions as a callback method to set dynamically the path
    for the result zip-file for the groupimport

    """

    return os.path.join(
        'import', 'groupimport', str(instance.id), 'resultfile', filename)


class GroupImport(models.Model):
    """The import object of a group of scenarios

    table: The csv-files in which the scenarios are defined that are
    uploaded.  results: A zip-file containing all the needed result
    files form importing a scenario.
    """

    name = models.CharField(_("Name"), max_length=200)
    table = models.FileField(
        _("Excel table (.xls)"), upload_to=get_groupimport_table_path,
        blank=True, null=True)
    results = models.FileField(
        _("Results (zipfile)"), upload_to=get_groupimport_result_path,
        blank=True, null=True)
    upload_successful = models.NullBooleanField()

    def __unicode__(self):
        return self.name


class ImportScenario(models.Model):
    """ A scenario that is offered as an import for the database.

    """
    class Meta:
        permissions = (
            ("can_upload", "Can upload new scenarios"),
            ("can_approve", "Can approve uploaded scenarios"),
        )

    class Meta:
        verbose_name = _('Import scenario')
        verbose_name_plural = _('Import scenarios')

    IMPORT_STATE_NONE = 0
    IMPORT_STATE_WAITING = 10
    IMPORT_STATE_ACTION_REQUIRED = 20
    IMPORT_STATE_APPROVED = 30
    IMPORT_STATE_DISAPPROVED = 40
    IMPORT_STATE_IMPORTED = 50

    IMPORT_STATE_CHOICES = (
         (IMPORT_STATE_NONE, _('None')),
         (IMPORT_STATE_WAITING, _('Waiting for validation')),
         (IMPORT_STATE_ACTION_REQUIRED, _('Action required')),
         (IMPORT_STATE_APPROVED, _('Approved for import')),
         (IMPORT_STATE_DISAPPROVED, _('Disapproved for import')),
         (IMPORT_STATE_IMPORTED, _('Imported')),
    )

    name = models.CharField(max_length=200)
    scenario = models.OneToOneField(Scenario, null=True, blank=True)
    region = models.ForeignKey(Region, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)
    breach = models.ForeignKey(Breach, null=True, blank=True)

    groupimport = models.ForeignKey(GroupImport, null=True, blank=True)
    approvalobject = models.OneToOneField(
        ApprovalObject, null=True, blank=True)

    owner = models.ForeignKey(User, help_text=_('The owner of the scenario.'))
    creation_date = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(
        choices=IMPORT_STATE_CHOICES, default=IMPORT_STATE_WAITING)
    action_taker = models.CharField(max_length=200, blank=True, null=True)

    validation_remarks = models.TextField(blank=True, null=True, default='-')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.get_state_display())

    def update_scenario_name(self):
        """The Scenario name isn't actually imported yet, but we can
        use it for the ImportScenario just as well."""

        try:
            field = self.importscenarioinputfield_set.get(
                inputfield__destination_table="Scenario",
                inputfield__destination_field="name")
            name = field.getValue()
            if name == '':
                name = '-'
            self.name = name
        except ImportScenarioInputField.DoesNotExist:
            self.name = '-'

    def receive_input_fields(self, fields):
        """Loop through all posted fields, search the corresponding
        input field object. Get or create the
        importscenario_inputfield and set the value, given in the
        fields dictionary."""
        for field, value in fields.iteritems():
            input_fields = InputField.objects.filter(name=field)
            if input_fields.count() == 1:
                input_field = input_fields[0]
                importscenario_inputfield, _ = (
                    ImportScenarioInputField.objects.get_or_create(
                        importscenario=self, inputfield=input_field))
                importscenario_inputfield.setValue(value)

    def get_import_values(self):
        """Get all import values in dict form.
        - Keys of the dictionary are destination tables
        - Values are destination field / value dictionaries"""

        import_values = {
            'Scenario': {},
            'ScenarioBreach': {},
            'ExtraScenarioInfo': {},
            'Breach': {},
            }

        for field in self.importscenarioinputfield_set.all():
            destination_table = field.inputfield.destination_table
            destination_field = field.inputfield.destination_field

            import_values.setdefault(destination_table, {})[
                destination_field] = field.getValue()

        return import_values

    def create_scenario(self, scenario_values):
        """If self.scenario doesn't exist yet, create it with the
        import values. TODO: should probably update the existing one
        too."""
        if self.scenario:
            scenario = self.scenario
        else:
            scenario = Scenario.objects.create(
                approvalobject=self.approvalobject,
                name=str(scenario_values.get("name", "-")),
                owner=self.owner,
                remarks=str(scenario_values.get("remarks", "")),
                sobekmodel_inundation=SobekModel.objects.get(
                    pk=1),  # only link to dummy is possible
                tsim=float(scenario_values.get("tsim", 0)),
                # calcpriority
                code="2impsc_" + str(self.id))
            scenario.set_project(self.project)
            self.scenario = scenario
            self.save()

    def create_scenariobreach(self, breach_values):
        """Create a ScenarioBreach if it's not there yet. Set values
        from import input fields."""

        scenariobreach, _ = ScenarioBreach.objects.get_or_create(
            scenario=self.scenario, breach=self.breach,
            defaults={
                "waterlevelset": WaterlevelSet.objects.get(
                    pk=1),  # only linking to dummy is possible
                #sobekmodel_externalwater
                "widthbrinit": breach_values.get("widthbrinit", -999),
                "methstartbreach": breach_values.get("methstartbreach", 2),
                "tstartbreach": breach_values.get("tstartbreach", 0),
                "hstartbreach": breach_values.get("hstartbreach", -999),
                "brdischcoef": breach_values.get("brdischcoef", -999),
                "brf1": breach_values.get("brf1", -999),
                "brf2": breach_values.get("brf2", -999),
                "bottomlevelbreach": breach_values.get(
                    "bottomlevelbreach", -999),
                "ucritical": breach_values.get("ucritical", -999),
                "pitdepth": breach_values.get("pitdepth", -999),
                "tmaxdepth": breach_values.get("tmaxdepth", 0),
                "extwmaxlevel": breach_values.get("extwmaxlevel", -999),
                "extwbaselevel": breach_values.get("extwbaselevel", None),
                "extwrepeattime": breach_values.get("extwrepeattime", None),
                "tstorm": breach_values.get("tstorm", None),
                "tpeak": breach_values.get("tpeak", None),
                "tdeltaphase": breach_values.get("tdeltaphase", None),
                "code": "2impsc_" + str(self.id)})

    def create_extra_scenario_info(self, extra_scenario_info):
        for extra_field_name in extra_scenario_info:
            extrainfofield, _ = ExtraInfoField.objects.get_or_create(
                name=extra_field_name)
            extrascenarioinfo, _ = ExtraScenarioInfo.objects.get_or_create(
                extrainfofield=extrainfofield,
                scenario=self.scenario,
                defaults={"value": " "})
            extrascenarioinfo.value = str(
                extra_scenario_info[extra_field_name])
            extrascenarioinfo.save()

    def copy_result_files(self, result_values):
        # results
        for resulttype_id, value in result_values.items():
            filepath = os.path.join(
                settings.MEDIA_ROOT, value.name)

            result, _ = Result.objects.get_or_create(
                scenario=self.scenario,
                resulttype=ResultType.objects.get(
                    pk=int(resulttype_id)),
                defaults={
                    "resultloc": "-",
                    "deltat": 1.0 / 24})

            dest_file_rel = os.path.join(
                self.scenario.get_rel_destdir(),
                os.path.basename(filepath))

            dest_file = os.path.join(
                Setting.objects.get(
                    key='destination_dir').value, dest_file_rel)
            dest_file = dest_file.replace('\\', '/')

            dest_path = os.path.dirname(dest_file)

            if not os.path.isdir(dest_path):
                os.makedirs(dest_path)

            result.resultloc = dest_file_rel
            result.save()

            # Replace \ by / so that it works on both Linux and Windows

            # The directory
            # /p-flod-fs-00-d1.external-nens.local/flod-share/ was
            # created on both flooding webservers to make a path like
            # that work on both sides.
            filepath = filepath.replace('\\', '/')
            dest_file = dest_file.replace('\\', '/')

            logger.debug("VALUE = " + filepath)
            logger.debug("DEST_FILE = " + dest_file)
            copyfile(filepath, dest_file)

    def import_into_flooding(self, username):
        """Import all fields into the correct fields in flooding.

        Returns two values: a success boolean, and a message string."""

        # Check whether attachments are present
        if not (self.region and self.breach and self.project):
            return (False,
                    'instellingen voor region, breach of project missen')

        import_values = self.get_import_values()

        self.create_scenario(import_values['Scenario'])
        self.create_scenariobreach(import_values['ScenarioBreach'])
        self.create_extra_scenario_info(import_values['ExtraScenarioInfo'])
        self.copy_result_files(import_values['Result'])
        self.scenario.create_calculated_status(username)

        self.state = ImportScenario.IMPORT_STATE_IMPORTED
        self.save()

        return (True, 'migratie compleet. scenario id is: {0}'.
                format(self.scenario.id))


class ImportScenarioInputField(models.Model):
    """ Relates an input field with a scenario

    This class can be used for 'constructing' a scenario import form.
    One can pick one or more InputField and link them to a scenario, such
    that finally a scenario has been connected to one or more input fields.

    These input fields together can be seen as a form. And like in a
    form one can set and get values for each form field.

    """
    class Meta:
        verbose_name = _('Import scenario input field')
        verbose_name_plural = _('Import scenarios input fields')

    FIELD_STATE_WAITING = 20
    FIELD_STATE_APPROVED = 30
    FIELD_STATE_DISAPPROVED = 40

    FIELD_STATE_CHOICES = (
         (FIELD_STATE_WAITING, _('Waiting')),
         (FIELD_STATE_APPROVED, _('Approved')),
         (FIELD_STATE_DISAPPROVED, _('Disapproved'))
    )

    importscenario = models.ForeignKey(ImportScenario, null=True)
    inputfield = models.ForeignKey('InputField', null=True)
    state = models.IntegerField(
        choices=FIELD_STATE_CHOICES, default=FIELD_STATE_WAITING)
    validation_remarks = models.TextField(blank=True)

    def __unicode__(self):
        return u'%s: %s (%s)' % (
            self.importscenario.name, self.inputfield.name,
            self.getValueString())

    def getValue(self):
        value_object = self.inputfield.get_or_create_value_object(self)
        return value_object.value

    def getValueString(self):
        return str(self.getValue())

    def setValue(self, value):
        value_object = self.inputfield.get_or_create_value_object(self)
        value_object.set(value)
        value_object.save()

    def get_editor_dict(self):
        item = self.inputfield.get_editor_dict()

        item["defaultValue"] = self.getValue()
        if self.inputfield.type == InputField.TYPE_BOOLEAN:
            if self.getValue() == 0:
                item["defaultValue"] = False
            else:
                item["defaultValue"] = True

        if self.inputfield.type == InputField.TYPE_INTERVAL:
            item["defaultValue"] = get_intervalstring_from_dayfloat(
                self.getValue())
        if self.inputfield.type == InputField.TYPE_DATE:
            a = self.getValue()
            try:
                item["defaultValue"] = (a[8:10] + '/' + a[5:7] +
                                        '/' + a[0:4] + ' 3:00')
            except:
                pass
        elif self.inputfield.type == InputField.TYPE_FILE:
            item["type"] = "StaticTextItem"
            item["required"] = False
        return item

    def get_editor_json(self):
        return simplejson.dumps(self.get_editor_dict())

    def get_static_editor_json(self):
        item = self.get_editor_dict()
        item["disabled"] = True
        return simplejson.dumps(item)

    def get_statestring_json(self):
        item = {
            "title": "status",
            "type":  "StaticTextItem",
            "defaultValue": (self.get_state_display() + ": " +
                             self.validation_remarks)
        }

        if self.state == self.FIELD_STATE_APPROVED:
            item["cellStyle"] = "approved"
        elif self.state == self.FIELD_STATE_DISAPPROVED:
            item["cellStyle"] = "disapproved"

        if self.inputfield.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.inputfield.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.inputfield.visibility_dependency_field.name + "'))")

        return simplejson.dumps(item)

    def get_approve_remarkeditor_dict(self):
        item = self.inputfield.get_approve_remarkeditor_dict()
        item["defaultValue"] = self.validation_remarks,
        if self.inputfield.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.inputfield.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.inputfield.visibility_dependency_field.name + "'))")
        return item

    def get_approve_remarkeditor_json(self):
        return simplejson.dumps(self.get_approve_remarkeditor_dict())

    def get_approve_statuseditor_dict(self):
        item = self.inputfield.get_approve_statuseditor_dict()
        item["defaultValue"] = self.state,
        if self.inputfield.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.inputfield.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.inputfield.visibility_dependency_field.name + "'))")
        return item

    def get_approve_statuseditor_json(self):
        return simplejson.dumps(self.get_approve_statuseditor_dict())


class StringValue(models.Model):
    """The class responsible for saving Strings"""
    importscenario_inputfield = models.OneToOneField(
        ImportScenarioInputField, primary_key=True)
    value = models.CharField(max_length=200, blank=True, null=True)

    def set(self, value):
        self.value = str(value)


class DateValue(StringValue):
    """The class responsible for saving Dates"""
    def set(self, value):
        self.value = str(value)

    class Meta:
        proxy = True


class IntegerValue(models.Model):
    """The class responsible for saving Integers"""
    importscenario_inputfield = models.OneToOneField(
        ImportScenarioInputField, primary_key=True)
    value = models.IntegerField(blank=True, null=True)

    def set(self, value):
        self.value = int(value)


class SelectValue(IntegerValue):
    """The class responsible for saving Selects"""
    class Meta:
        proxy = True


class BooleanValue(IntegerValue):
    """The class responsible for saving Booleans"""

    def set(self, value):
        if value.lower() in ['true', 'yes', 'ja']:
            self.value = 1
        elif value.lower() in ['false', 'no', 'nee']:
            self.value = 0
        else:
            raise ValueError('boolean value is not true or false')

    class Meta:
        proxy = True


class FloatValue(models.Model):
    """The class responsible for saving Floats"""
    importscenario_inputfield = models.OneToOneField(
        ImportScenarioInputField, primary_key=True)
    value = models.FloatField(blank=True, null=True)

    def set(self, value):
        self.value = float(value)


class IntervalValue(FloatValue):
    """The class responsible for saving Intervals"""
    def set(self, value):
        value = get_dayfloat_from_intervalstring(value)
        self.value = float(value)

    class Meta:
        proxy = True


class TextValue(models.Model):
    """The class responsible for saving Texts"""
    importscenario_inputfield = models.OneToOneField(
        ImportScenarioInputField, primary_key=True)
    value = models.TextField(blank=True, null=True)

    def set(self, value):
        self.value = str(value)


def get_import_upload_files_path(instance, filename):
    """
    Method that functions as a callback method to set dynamically
    the path for the result zip-file for the groupimport
    """
    return os.path.join(
        'import',
        'importscenario',
        str(instance.importscenario_inputfield.importscenario_id),
        'files', filename)


class FileValue(models.Model):
    """The class responsible for saving Files"""
    importscenario_inputfield = models.OneToOneField(
        ImportScenarioInputField, primary_key=True)
    value = models.FileField(
        upload_to=get_import_upload_files_path, blank=True, null=True)

    def set(self, value):
        #TO DO: Nog niet geimplementeerd!!!!
        return 'Aanwezig'


class InputField(models.Model):
    """ A general field that is used for importing scenario properties

    By relating multiple instance of this class to a scenario, one can
    create a list of fields that can be used for entering data for the import
    scenario. The class ImportScenarioValue is responsible for linking
    a field with a scenario.

    The fields contain enough information for displaying the field in
    the webinterface.

    The fields also contain enough information for displaying and handling
    the approving of the field.

    """
    class Meta:
        verbose_name = _('Import scenario fields')
        verbose_name_plural = _('Import scenarios fields')
        ordering = ['header']

    TYPE_INTEGER = 10
    TYPE_FLOAT = 20
    TYPE_STRING = 30
    TYPE_TEXT = 40
    TYPE_DATE = 50
    TYPE_INTERVAL = 60
    TYPE_FILE = 70
    TYPE_SELECT = 80
    TYPE_BOOLEAN = 90

    TYPE_CHOICES = (
         (TYPE_INTEGER, _('Integer')),
         (TYPE_FLOAT, _('Float')),
         (TYPE_STRING, _('String')),
         (TYPE_TEXT, _('Text')),
         (TYPE_INTERVAL, _('Interval (D d HH:MM)')),
         (TYPE_DATE, _('Date')),
         (TYPE_FILE, _('File')),
         (TYPE_SELECT, _('Select')),
         (TYPE_BOOLEAN, _('Boolean (True or False)')),
    )

    TYPE_VALUE_CLASSES = {
        TYPE_INTEGER: IntegerValue,
        TYPE_FLOAT: FloatValue,
        TYPE_STRING: StringValue,
        TYPE_TEXT: TextValue,
        TYPE_DATE: DateValue,
        TYPE_INTERVAL: IntervalValue,
        TYPE_FILE: FileValue,
        TYPE_SELECT: SelectValue,
        TYPE_BOOLEAN: BooleanValue,
        }

    HEADER_SCENARIO = 10
    HEADER_META = 20
    HEADER_LOCATION = 30
    HEADER_BREACH = 40
    HEADER_EXTERNALWATER = 50
    HEADER_MODEL = 70
    HEADER_REMAINING = 80
    HEADER_FILES = 90

    HEADER_CHOICES = (
        (HEADER_SCENARIO, _('Scenario')),
        (HEADER_META, _('Meta')),
        (HEADER_LOCATION, _('Location')),
        (HEADER_BREACH, _('Breach')),
        (HEADER_EXTERNALWATER, _('External Water')),
        (HEADER_MODEL, _('Model')),
        (HEADER_REMAINING, _('Remaining')),
        (HEADER_FILES, _('Files')),
    )

    name = models.CharField(max_length=200, unique=True)
    header = models.IntegerField(
        choices=HEADER_CHOICES, default=HEADER_REMAINING)
    position = models.IntegerField(
        default=0, help_text=_('Hoe hoger hoe eerder in rij'))
    import_table_field = models.CharField(
        max_length=100, help_text=_('Name of col. in import csv-file'))
    destination_table = models.CharField(
        max_length=100, help_text=_('Name of table in flooding database'))
    destination_field = models.CharField(
        max_length=100,
        help_text=_('Name of field in flooding database table'))
    destination_filename = models.CharField(
        max_length=100, null=True, blank=True,
        help_text=_('Name of imported files (match with resulttypes). '
                    'Use #### for numbers'))

    type = models.IntegerField(choices=TYPE_CHOICES)
    options = models.TextField(blank=True)

    visibility_dependency_field = models.ForeignKey(
        'InputField', null=True, blank=True)
    visibility_dependency_value = models.TextField(blank=True)

    excel_hint = models.CharField(
        max_length=200, blank=True,
        help_text=_('help text shown in excel file'))
    hover_text = models.CharField(
        max_length=200, blank=True,
        help_text=_('help text shown when hovering over field'))
    hint_text = models.CharField(
        max_length=200, blank=True,
        help_text=_('help text shown behind field'))
    required = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.get_header_display(), self.name)

    @property
    def value_class(self):
        """Return the value class for this input field's type."""
        if self.type in self.TYPE_VALUE_CLASSES:
            return self.TYPE_VALUE_CLASSES[self.type]
        else:
            raise NotImplementedError(
                "self.type has an unknown value (%s)" % (str(self.type),))

    def get_or_create_value_object(self, importscenario_inputfield):
        value_object, _ = self.value_class.objects.get_or_create(
            importscenario_inputfield=importscenario_inputfield)
        return value_object

    def get_editor_dict(self):

        item = {
                "name": self.name,
                "title": self.name,
                "required": self.required,
                "colSpan": 2,
                "width": 300,
                #"height": 50,
                "startRow": True
        }
        if self.hint_text:
            item["hint"] = self.hint_text
        if self.hover_text:
            item["prompt"] = self.hover_text
        if self.type == self.TYPE_INTEGER:
            item["type"] = "integer"
        elif self.type == self.TYPE_FLOAT:
            item["type"] = "float"
        elif self.type == self.TYPE_STRING:
            item["type"] = "text"
        elif self.type == self.TYPE_TEXT:
            item["type"] = "textArea"
        elif self.type == self.TYPE_DATE:
            item["type"] = "date"
            # fix to get right dates back from Isomorphic
            item["blur"] = "this.setValue(this.getValue().setHours(4));"
        elif self.type == self.TYPE_INTERVAL:
            item["type"] = "text"
            item["dateFormatter"] = "intervalFormatter"
            item["blur"] = "this.setValue(intervalFormatter(this.getValue()));"
        elif self.type == self.TYPE_FILE:
            item["type"] = "binary"  # "link" if not editable and just view it
        elif self.type == self.TYPE_SELECT:
            item["type"] = "select"
            item["valueMap"] = eval(self.options)
        elif self.type == self.TYPE_BOOLEAN:
            item["type"] = "boolean"
        if self.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.visibility_dependency_field.name + "'))")

        if self.inputfield_set.count() > 0:
            item['redrawOnChange'] = True

        return item

    def get_editor_json(self):
        return simplejson.dumps(self.get_editor_dict())

    def get_static_editor_json(self):
        item = self.get_editor_dict()
        item["disabled"] = True
        return simplejson.dumps(item)

    def get_approve_remarkeditor_dict(self):
        item = {
                "name": "edremark." + self.name,
                "title": "status",
                "showTitle": False,
                "colSpan": 1,
                "width": 150,
                "type": "text"
        }
        if self.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.visibility_dependency_field.name + "'))")

        return item

    def get_approve_remarkeditor_json(self):
        return simplejson.dumps(self.get_approve_remarkeditor_dict())

    def get_approve_statuseditor_dict(self):
        valuemap = {}
        for obj in ImportScenarioInputField.FIELD_STATE_CHOICES:
            valuemap[obj[0]] = obj[1]

        item = {
            "name": "edstate." + self.name,
            "title": "status",
            "colSpan": 2,
            "width": 100,
            "type": "select",
            "valueMap": valuemap
        }

        if self.visibility_dependency_field:
            item["showIf"] = (
                "[" + self.visibility_dependency_value +
                "].contains(form.getValue('" +
                self.visibility_dependency_field.name + "'))")

        return item

    def get_approve_statuseditor_json(self):
        return simplejson.dumps(self.get_approve_statuseditor_dict())

    @classmethod
    def grouped_input_fields(cls):
        """Returns a list of dictionaries. One dictionary for each header
        in HEADER_CHOICES, with id the id of the header, title the title
        of the header, and fields all the InputField objects that belong to
        that header."""

        form_fields = []
        header_listposition_map = {}

        # create the form_fields list (only headers, no fields added) and
        # save for each header the position in the list

        for header_id, header_title in cls.HEADER_CHOICES:
            header_listposition_map[header_id] = len(form_fields)
            form_fields.append(
                {'id': header_id, 'title': header_title, 'fields': []})

        fields = cls.objects.all().order_by('-position')

        # Loop though all the fields an place them and append
        # them at the fields of the correct tuple (so, you need the header)
        for field in fields:
            (form_fields[header_listposition_map[field.header]]['fields'].
             append(field))

        return form_fields
