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
import xlwt

from flooding_lib.tools.importtool.models import InputField


class Cell(object):
    def __init__(self, value):
        self.value = value


class ScenarioRow(object):
    def __init__(self, scenario, headers):
        self.scenario = scenario
        self.headers = iter(headers)  # Explicitly turn into iter
                                      # because it may be one already

    def columns(self):
        # The first column is the scenario id, there is no input field for that
        # Skip the first column in headers
        self.headers.next()
        yield Cell(self.scenario.id)  # Yield the value

        for header in self.headers:
            inputfield = header['inputfield']
            value = self.scenario.value_for_inputfield(inputfield)
            value_unicode = inputfield.display_unicode(value)
            yield Cell(value_unicode)


class FieldInfo(object):
    def __init__(self, scenariolist):
        self.scenariolist = list(scenariolist)

    def add_extra_header_fields(self, header):
        header['fieldname'] = header['inputfield'].name
        header['fieldhint'] = header['inputfield'].excel_hint
        header['required'] = '*' in header['inputfield'].hint_text

        for typeid, description in InputField.TYPE_CHOICES:
            if typeid == header['inputfield'].type:
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
        if header.get('required', False):
            color = 'orange'
        else:
            color = 'light_yellow'
        pattern = """
            borders: top thin, bottom thin, left thin, right thin;
            pattern: fore_color {0}, pattern solid;""".format(color)
    else:
        pattern = ""

    if rownr == 1:
        return xlwt.easyxf(
            pattern + 'font: bold on; align: wrap on, vertical top;')
    return xlwt.easyxf(pattern + 'align: wrap on, vertical top;')


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

    scenarios = project.original_scenarios()
    if not scenarios.count():
        return None

    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet("Scenario data")

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
            worksheet.write(len(header_fields) + rownr, colnr, cell.value)

    # Domeinlijst definities
    worksheet = workbook.add_sheet("Domeinlijst definities")
    column = 0
    for header in headers:
        column_written = write_domeinlijst(worksheet, column, header)
        if column_written:
            column += 2

    if filename is not None:
        workbook.save(filename)

    return workbook
