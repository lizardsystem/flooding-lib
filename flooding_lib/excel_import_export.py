"""
The Excel file format is modelled after the existing format that is
used by the importtool, and its example Excel files.

There is a header (the first four rows of the file) and after that,
one row per scenario in the file.

In the header, the leftmost column is empty. Then, there is a column
for each inputfield of the importtool. These are group by header, as
in the importtool.

Row 1 holds the name of the header (this will be repeated through
several columns)

Row 2 holds the name of the field

Row 3 holds the type of the field

Row 4 holds the 'Excel hint' of the field.

Required fields will have all their text in bold. A field is required
if it has a "hint_text" containing *, ** or ***. This includes fields
that don't have "required == True". The reason is that this Excel
output/input functionality is right now only for updating old data,
and old data only contains "type 1" scenarios.

For each row after the header, column 1 will contain the scenario's
primary key ID field, and the other columns will have the scenario's
existing data for the field in that column, if any.

There will be one Excel file per project, and it will contain all the
scenarios for which that project is the main project. If there are no
such scenarios, there won't be an Excel file.
"""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import ast
import logging
import xlrd
import xlwt

from itertools import izip

from django.db import transaction
from django.utils.html import strip_tags

from flooding_lib.util.decorators import memoized
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.models import Scenario
from flooding_lib.tools.approvaltool import models as approvalmodels

SCENARIO_DATA_WORKSHEET = "Scenario data"
SCENARIO_APPROVAL_WORKSHEET = "Goedkeuring"

HEADER_ROWS = 4

logger = logging.getLogger(__name__)

DEFAULT_NUM_FORMAT = '#.##'


@memoized
def make_style(pattern, num_format_str=DEFAULT_NUM_FORMAT):
    """We need to make this a memoized function because each call to
    easyxf creates a new XF object, and Excel files have a limit of
    4094 of them. If we create one per cell, we can go over that, but
    by memoizing them we only get one per pattern (and we use fewer
    than 10 different patterns)."""
    return xlwt.easyxf(pattern, num_format_str=num_format_str)


class Cell(object):
    """Helper class to represent an Excel cell. Has a value and a
    style."""
    def __init__(self, value, pattern='', inputfield=None):
        """If an inputfield is given, it may be used to add
        information to the pattern (e.g., formatting for dates)."""

        self.value = value

        num_format_str = DEFAULT_NUM_FORMAT
        if inputfield and inputfield.type == InputField.TYPE_DATE:
            num_format_str = 'dd/mm/yyyy'

        self.style = make_style(pattern, num_format_str)


class ScenarioRow(object):
    """A row of cells for some scenario."""
    def __init__(self, scenario, headers):
        self.scenario = scenario
        self.headers = iter(headers)  # Explicitly turn into iter
                                      # because it may be one already

    def columns(self):
        """The first column is the scenario id, there is no input
        field for that Skip the first column in headers."""
        default_pattern = 'font: bold off; align: wrap on, vertical top;'

        self.headers.next()
        yield Cell(self.scenario.id, default_pattern)  # Yield the value

        for header in self.headers:
            inputfield = header['inputfield']
            value = self.scenario.value_for_inputfield(inputfield)

            value_excel = inputfield.to_excel(value)
            yield Cell(value_excel, default_pattern, inputfield)


class FieldInfo(object):
    """This class can say what to put in each Excel cell, be it a
    header or a scenario row."""
    def __init__(self, scenariolist):
        self.scenariolist = list(scenariolist)

    def scenarios(self):
        """Return an iterator over the scenariolist."""
        return iter(self.scenariolist)

    def add_extra_header_fields(self, header):
        """Helper function that adds some elements to the header
        dictionary that don't come from
        InputField.grouped_input_fields()."""

        inputfield = header['inputfield']

        header['fieldname'] = strip_tags(inputfield.name)
        header['fieldhint'] = strip_tags(inputfield.excel_hint)
        header['required'] = '*' in inputfield.hint_text
        header['ignore'] = inputfield.ignore_in_scenario_excel_files

        if header['ignore']:
            header['fieldtype'] = u'(veld kan niet aangepast worden)'
        elif inputfield.type == InputField.TYPE_DATE:
            header['fieldtype'] = u"Datum (DD/MM/JJJJ)"
        else:
            for typeid, description in InputField.TYPE_CHOICES:
                if typeid == inputfield.type:
                    header['fieldtype'] = unicode(description)
                    break

        return header

    def headers_from_inputfields(self):
        """Get the output of InputField.grouped_input_fields and turn
        it into one iterable of header dictionaries."""

        for group in InputField.grouped_input_fields():
            for inputfield in group['fields']:
                yield {
                    'headername': group['title'],
                    'inputfield': inputfield
                    }

    def headers(self):
        """Generate a dictionary for each header column, used in the
        template and to generate the scenario rows."""

        # First column is empty
        yield {
            'headername': '',
            'fieldname': '',
            'fieldtype': '',
            'fieldhint': '(intern scenarionummer, niet veranderen)'
            }

        for header in self.headers_from_inputfields():
            yield self.add_extra_header_fields(header)

    def rows(self):
        """The actual rows of data are constructed using the
        scenariolist and the headers."""
        for scenario in self.scenariolist:
            yield ScenarioRow(scenario, self.headers())

    def __nonzero__(self):
        """Returns true if there are scenarios in the list."""
        return bool(self.scenariolist)


def get_header_style_for(rownr, colnr, header):
    """Return a style object for the header field in given rownr and
    colnr."""
    if colnr > 0 and rownr > 0:
        if header.get('ignore', False):
            color = 'gray25'
        elif header.get('required', False):
            color = 'orange'
        else:
            color = 'light_yellow'
        pattern = """
            borders: top thin, bottom thin, left thin, right thin;
            pattern: fore_color {0}, pattern solid;""".format(color)
    else:
        pattern = ""

    if rownr == 1:
        return make_style(
            pattern + 'font: bold on; align: wrap on, vertical top;')
    return make_style(pattern + 'align: wrap on, vertical top;')


def write_domeinlijst(worksheet, column, header):
    if not header['fieldtype'] == 'Select':
        return False

    try:
        codes = ast.literal_eval(header['inputfield'].options)
    except SyntaxError:
        # If the options field doesn't contain a valid dictionary,
        # we're going to skip this input field.
        return False

    if not isinstance(codes, dict):
        return False

    worksheet.write(0, column, "Code")
    worksheet.write(0, column + 1, header['fieldname'])

    for rownr, code in enumerate(sorted(codes)):
        worksheet.write(rownr + 1, column, code)
        worksheet.write(rownr + 1, column + 1, codes[code])

    column_width = 30 * 256  # ~ 30 characters
    worksheet.col(column + 1).width = column_width

    return True


def create_metadata_worksheet(worksheet, fieldinfo):
    header_fields = ('headername', 'fieldname', 'fieldtype', 'fieldhint')

    worksheet.row(1).height = int(0.84 * 72 * 20)  # 0.84"
    worksheet.row(2).height = int(0.36 * 72 * 20)  # 0.36"
    worksheet.row(3).height = int(1.43 * 72 * 20)  # 1.43"

    # Write the header
    for column, header in enumerate(fieldinfo.headers()):
        for rownr, headerfield in enumerate(header_fields):
            style = get_header_style_for(rownr, column, header)
            worksheet.write(rownr, column, header[headerfield], style)

        if column > 0:
            column_width = 20 * 256  # ~ 20 characters
            worksheet.col(column).width = column_width

    # Write data
    for rownr, row in enumerate(fieldinfo.rows()):
        for colnr, cell in enumerate(row.columns()):
            if cell.value:
                worksheet.write(
                    len(header_fields) + rownr, colnr, cell.value, cell.style)


def create_domeinlijst_worksheet(worksheet, fieldinfo):
    column = 0
    for header in fieldinfo.headers():
        column_written = write_domeinlijst(worksheet, column, header)
        if column_written:
            column += 2


def create_approval_worksheet(project, worksheet, scenarios):
    # In theory it is possible that one scenario has completely
    # different approval rules than another scenario. Therefore we
    # keep a dict that keeps track of which rule goes in which column,
    # write all the data first, and only then write all the column
    # headers.
    rule_columns = dict()
    next_rule_column = 3

    # We want to show the value for this inputfield. Doing it using
    # scenario.value_for_inputfield() isn't the quickest way, but it
    # is the cleanest.
    scenario_id_inputfield = InputField.objects.get(
        name='Scenario Identificatie')

    for i, scenario in enumerate(scenarios):
        row = i + 4
        worksheet.write(row, 0, scenario.id)
        worksheet.write(
            row, 1, scenario.value_for_inputfield(
                scenario_id_inputfield))
        worksheet.write(row, 2, scenario.name)

        approval_object = scenario.approval_object(project)
        for statenr, state in enumerate(approval_object.states()):
            if state.approvalrule_id not in rule_columns:
                rule_columns[state.approvalrule_id] = next_rule_column
                next_rule_column += 2
            col = rule_columns[state.approvalrule_id]

            if state.successful is not None:
                worksheet.write(row, col, int(state.successful))

            if state.remarks:
                worksheet.write(row, col + 1, state.remarks)

    # Write the headers for each rule
    for ruleid, col in rule_columns.items():
        rule = approvalmodels.ApprovalRule.objects.get(pk=ruleid)

        # Two columns: one for the value of the approvalstate
        # (successful or not), one for any remarks that may have been
        # recorded. Rule name has bold: on.
        worksheet.write(1, col, rule.name, make_style(
                'font: bold on; align: wrap on, vertical top;'))
        worksheet.write(2, col, rule.description)
        worksheet.write(3, col, '(1 = goedgekeurd, 0 = afgekeurd)')

        worksheet.write(1, col + 1, rule.name, make_style(
                'font: bold on; align: wrap on, vertical top;'))
        worksheet.write(2, col + 1, 'Opmerkingen')

    # Set the column widths
    for colnr in range(next_rule_column):
        width = 30 if colnr >= 2 else 10
        worksheet.col(colnr).width = width * 256  # chars


def create_excel_file(
    project, scenarios, filename=None, include_approval=False):
    """Create an Excel file containing the data of this project."""

    logger.debug(("Starting create_excel_file. Project id is {0}, "
                 "filename is '{1}'.").format(project.id, filename))

    fieldinfo = FieldInfo(scenarios)
    if not fieldinfo:
        logger.debug("There are no scenarios in this project.")
        return None

    workbook = xlwt.Workbook(encoding='utf-8')

    worksheet = workbook.add_sheet(SCENARIO_DATA_WORKSHEET)
    create_metadata_worksheet(worksheet, fieldinfo)

    worksheet = workbook.add_sheet("Domeinlijst definities")
    create_domeinlijst_worksheet(worksheet, fieldinfo)

    if include_approval:
        worksheet = workbook.add_sheet(SCENARIO_APPROVAL_WORKSHEET)
        create_approval_worksheet(project, worksheet, scenarios)

    if filename is not None:
        logger.debug("Saving workbook...")
        workbook.save(filename)

    return workbook


def get_worksheet(path, name):
    worksheet = xlrd.open_workbook(path).sheet_by_name(name)
    return worksheet


@transaction.commit_manually
def import_uploaded_excel_file(path, allowed_scenario_ids):
    """Check and import the Excel file. The whole operation is wrapped
    in a database transaction, so that any problems won't change the
    database. Returns a list of error messages; an empty list
    indicates success."""

    worksheet = get_worksheet(path, SCENARIO_DATA_WORKSHEET)
    header_titles = tuple(cell.value for cell in worksheet.row(1))

    errors = []

    header, header_errors = import_header(header_titles)

    if header_errors:
        errors += header_errors

    for rownr in range(HEADER_ROWS, worksheet.nrows):
        row_errors = import_scenario_row(
            header, rownr, worksheet.row(rownr), allowed_scenario_ids)

        if row_errors:
            errors += row_errors

    if errors:
        transaction.rollback()
    else:
        transaction.commit()

    return errors


def find_approval_rules(worksheet):
    rule_dict = dict()
    errors = []

    rulenames = list(worksheet.row(1))[3:]

    colnr = 0
    while colnr < len(rulenames):
        rulename1 = rulenames[colnr].value
        if (colnr + 1 >= len(rulenames)):
            errors.append(
                "De naam van een goedkeuringsregel moet boven twee kolommen"
                "staan.")
            return errors, rule_dict
        rulename2 = rulenames[colnr + 1].value

        if rulename1:
            if rulename1 != rulename2:
                errors.append(("De naam van de goedkeuringsregel in kolom {0}"
                               "is niet dezelfde als die in kolom {1}.")
                              .format(colnr, colnr + 1))
                return errors, rule_dict

            try:
                rule = approvalmodels.ApprovalRule.objects.get(name=rulename1)
                rule_dict[colnr] = rule
            except approvalmodels.ApprovalRule.DoesNotExist:
                errors.append("Regel met naam '{0}' niet gevonden.".format(
                        rulename1))

        colnr += 2

    return errors, rule_dict


def import_scenario_approval(
    rule_dict, rownr, row, allowed_scenario_ids, project, username):
    if not row:
        # Empty row, skip.
        return []

    try:
        scenarioidcell = row[0]
        scenarioid = int(scenarioidcell.value)
    except (ValueError, TypeError):
        return ["Op regel {0} geen scenarionummer gevonden.".format(rownr)]

    try:
        scenario = Scenario.objects.get(pk=scenarioidcell.value)
    except Scenario.DoesNotExist:
        return ["Regel {0}: onbekend scenarionummer {1}.".
                format(rownr, scenarioid)]

    if scenarioid not in allowed_scenario_ids:
        return ["Regel {0}: Scenario {1} zit niet in dit project."
                .format(rownr, scenarioid)]

    approvalobject = scenario.approval_object(project)
    approval_values = row[3:]

    col = 0
    while col in rule_dict and col < len(row):
        rule = rule_dict[col]
        approval_value = approval_values[col].value
        approval_remark = approval_values[col + 1].value

        record_approval(
            approvalobject, username, rule, approval_value, approval_remark)
        col += 2

    scenario.update_status()
    return []


def record_approval(
    approvalobject, username, rule, approval_value, approval_remark):
    approval_value = unicode(approval_value).strip()

    if approval_value not in ("0", "1"):
        return

    successful = approval_value == "1"

    approvalobject.approve(rule, successful, username, approval_remark)


@transaction.commit_manually
def import_upload_excel_file_for_approval(
    project, username, path, allowed_scenario_ids):
    worksheet = get_worksheet(path, SCENARIO_APPROVAL_WORKSHEET)

    errors, rule_dict = find_approval_rules(worksheet)
    if not errors:
        for rownr in range(HEADER_ROWS, worksheet.nrows):
            row_errors = import_scenario_approval(
                rule_dict, rownr, worksheet.row(rownr),
                allowed_scenario_ids, project, username)

            if row_errors:
                errors += row_errors

    if errors:
        transaction.rollback()
    else:
        transaction.commit()
    return errors


class ImportedHeader(object):
    """After importing, we want to know which field is where. This
    class stores that information; call __getitem__ with a column
    number and it will return an InputField, if any. Also, the class
    can be iterated over and it will return InputFields in turn."""

    class HeaderException(Exception):
        def __init__(self, message):
            self.message = message

    def __init__(self, fields=None):
        if fields is None:
            fields = {}

        self._fields = fields

    def find_field_by_name(self, colnr, fieldname):
        """If colnr >= 1, tries to find an InputField that corresponds to
        the given name. Checks that fields do not occur twice. Keeps
        track of which field is where.

        Returns None if colnr is 0, because there won't be a field
        there.  Raises an exception with an appropriate error message
        in other cases."""
        if colnr == 0:
            return None

        try:
            field = InputField.objects.get(name=fieldname)
        except InputField.DoesNotExist:
            raise self.HeaderException(
                "Veld met naam {0} niet gevonden.".format(fieldname))

        if field in self._fields.values():
            raise self.HeaderException(
                "Veld met naam {0} komt twee keer voor.".format(fieldname))

        self._fields[colnr] = field
        return field

    def __getitem__(self, column):
        return self._fields[column]

    def __iter__(self):
        last_value = max(self._fields)
        i = 1
        while i <= last_value:
            yield self._fields.get(i, None)
            i += 1


def import_header(header_titles):
    errors = []
    header = ImportedHeader()

    for column, title in enumerate(header_titles):
        try:
            header.find_field_by_name(column, title)
        except ImportedHeader.HeaderException as e:
            errors.append(e.message)

    return header, errors


def import_scenario_row(header, rownr, row, allowed_scenario_ids):
    """Given a row from the excel sheet, and the header, import it
    into the database. Returns a list of error messages. Perhaps there
    will be data written to the database even in case of errors, which
    shouldn't be a problem because this function will be called within
    a transaction that won't be committed if there are errors."""

    if not row:
        # Empty row, skip.
        return []

    try:
        scenarioidcell = row[0]
        scenarioid = int(scenarioidcell.value)
    except ValueError:
        return ["Op regel {0} geen scenarionummer gevonden.".format(rownr)]

    try:
        scenario = Scenario.objects.get(pk=scenarioidcell.value)
    except Scenario.DoesNotExist:
        return ["Regel {0}: onbekend scenarionummer {1}.".
                format(rownr, scenarioid)]

    if scenarioid not in allowed_scenario_ids:
        return ["Regel {0}: Scenario {1} zit niet in dit project."
                .format(rownr, scenarioid)]

    fieldvalues = row[1:]

    errors = []
    for cell, inputfield in izip(fieldvalues, header):
        if inputfield.ignore_in_scenario_excel_files:
            # InputField is of a type that can't be changed with this
            # import (e.g., properties of the Project or Region)
            continue

        if not cell.value:
            # Nothing filled in. Skip.
            continue

        try:
            value_object = inputfield.build_value_object(cell.value)
            scenario.set_value_for_inputfield(inputfield, value_object)
        except ValueError as ve:
            errors.append("Regel {0}: {1}.".format(rownr, ve))

    return errors
