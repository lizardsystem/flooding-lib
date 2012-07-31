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

import ast
import logging
import xlrd
import xlwt

from itertools import izip

from django.db import transaction

from flooding_lib.util.decorators import memoized
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.models import Scenario

SCENARIO_DATA_WORKSHEET = "Scenario data"

HEADER_ROWS = 4

logger = logging.getLogger(__name__)


@memoized
def make_style(pattern):
    """We need to make this a memoized function because each call to
    easyxf creates a new XF object, and Excel files have a limit of
    4094 of them. If we create one per cell, we can go over that, but
    by memoizing them we only get one per pattern (and we use less
    than 10 different patterns)."""
    return xlwt.easyxf(pattern)


class Cell(object):
    def __init__(self, value, pattern=''):
        self.value = value
        self.style = make_style(pattern)

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"Cell({0}) with style '{1}'".format(self.value, self.style)


class ScenarioRow(object):
    def __init__(self, scenario, headers):
        self.scenario = scenario
        self.headers = iter(headers)  # Explicitly turn into iter
                                      # because it may be one already

    def columns(self):
        # The first column is the scenario id, there is no input field for that
        # Skip the first column in headers
        default_pattern = 'font: bold off; align: wrap on, vertical top;'

        self.headers.next()
        yield Cell(self.scenario.id, default_pattern)  # Yield the value

        for header in self.headers:
            inputfield = header['inputfield']
            value = self.scenario.value_for_inputfield(inputfield)

            value_excel = inputfield.to_excel(value)
            yield Cell(value_excel, default_pattern)


class FieldInfo(object):
    def __init__(self, scenariolist):
        self.scenariolist = list(scenariolist)

    def add_extra_header_fields(self, header):
        inputfield = header['inputfield']

        header['fieldname'] = inputfield.name
        header['fieldhint'] = inputfield.excel_hint
        header['required'] = '*' in inputfield.hint_text
        header['ignore'] = inputfield.ignore_in_scenario_excel_files

        if header['ignore']:
            header['fieldtype'] = u'(veld kan niet aangepast worden)'
        else:
            if inputfield.type == InputField.TYPE_DATE:
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
        # First column is empty
        yield {
            'headername': '',
            'fieldname': '',
            'fieldtype': '',
            'fieldhint': ''
            }

        for header in self.headers_from_inputfields():
            yield self.add_extra_header_fields(header)

    def rows(self):
        for scenario in self.scenariolist:
            yield ScenarioRow(scenario, self.headers())


def filename_for_project(project):
    return (u"/tmp/{0} {1}.xls".format(project.id, project.name)
            .encode("utf-8"))


def get_header_style_for(rownr, colnr, header):
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


def create_excel_file(project, filename=None):
    """Create an Excel file containing the data of this project."""

    logger.debug(("Starting create_excel_file. Project id is {0}, "
                 "filename is '{1}'.").format(project.id, filename))

    scenarios = project.original_scenarios()
    if not scenarios.count():
        logger.debug("There are no scenarios in this project.")
        return None

    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet(SCENARIO_DATA_WORKSHEET)

    fieldinfo = FieldInfo(scenarios)

    header_fields = ('headername', 'fieldname', 'fieldtype', 'fieldhint')

    worksheet.row(1).height = int(0.84 * 72 * 20)  # 0.84"
    worksheet.row(2).height = int(0.36 * 72 * 20)  # 0.36"
    worksheet.row(3).height = int(1.43 * 72 * 20)  # 1.43"

    headers = list(fieldinfo.headers())

    # Write the header
    for column, header in enumerate(headers):
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

    # Domeinlijst definities
    worksheet = workbook.add_sheet("Domeinlijst definities")
    column = 0
    for header in headers:
        column_written = write_domeinlijst(worksheet, column, header)
        if column_written:
            column += 2

    if filename is not None:
        logger.debug("Saving workbook...")
        workbook.save(filename)

    return workbook


def get_scenario_worksheet(path):
    worksheet = xlrd.open_workbook(path).sheet_by_name(SCENARIO_DATA_WORKSHEET)
    return worksheet


def import_uploaded_excel_file(path):
    """Check and import the Excel file. The whole operation is wrapped
    in a database transaction, so that any problems won't change the
    database. Returns a list of error messages; an empty list
    indicates success."""

    worksheet = get_scenario_worksheet(path)
    header_titles = tuple(cell.value for cell in worksheet.row(1))

    errors = []

    class DummyException(Exception):
        pass

    try:
        with transaction.commit_on_success():
            header, header_errors = import_header(header_titles)

            if header_errors:
                errors += header_errors
                raise DummyException()

            for rownr in range(HEADER_ROWS, worksheet.nrows):
                row_errors = import_scenario_row(
                    header, rownr, worksheet.row(rownr))

                if row_errors:
                    errors += row_errors

            if errors:
                raise DummyException()
    except DummyException:
        pass

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


def import_scenario_row(header, rownr, row):
    if not row:
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

        value_object = inputfield.build_value_object()

        try:
            value_object.set(cell.value)
        except ValueError as ve:
            errors.append("Regel {0}: {1}.".format(rownr, ve))
        scenario
#        scenario.set_value_for_inputfield(inputfield, value_object)

    return errors
