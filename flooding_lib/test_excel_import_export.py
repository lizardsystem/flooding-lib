"""Tests for excel_import_export.py."""

# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import mock
import os
import xlrd

from django.test import TestCase
from django.utils.translation import activate, deactivate

from flooding_lib import excel_import_export as eie

from flooding_lib.test_models import ProjectF
from flooding_lib.test_models import ScenarioF
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.importtool.models import IntegerValue
from flooding_lib.tools.importtool.test_models import InputFieldF


class TestMakeStyle(TestCase):
    """Test the make style function"""
    def test_memoizes(self):
        """Call it twice, should return the exact same object."""

        self.assertTrue(eie.make_style('') is eie.make_style(''))


class TestCell(TestCase):
    """Tests for Cell."""
    @mock.patch('flooding_lib.excel_import_export.make_style')
    def test_date_inputfield_has_number_format(self, mocked_make_style):
        inputfield = InputFieldF(type=InputField.TYPE_DATE)
        eie.Cell(40725.0, inputfield=inputfield)

        num_format = mocked_make_style.call_args[0][1]
        self.assertEquals(num_format, 'dd/mm/yyyy')


class TestCreateExcelFile(TestCase):
    """Test the ceate_excel_file function"""
    def test_creates_file(self):
        """If called with a project, TestCreateExcelFile creates an
        Excel file and returns the path of that file."""
        project = ProjectF.create()
        # Add a scenario
        ScenarioF.create().set_project(project)
        filename = "/tmp/create_excel_file.xls"

        eie.create_excel_file(project, filename)
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_creates_field_info_object(self):
        """Check that it calls project.original_scenarios and passes
        the result to FieldInfo."""
        scenariolistmock = mock.MagicMock()

        with mock.patch(
            'flooding_lib.models.Project.original_scenarios',
            new=mock.MagicMock(return_value=scenariolistmock)):
            project = ProjectF()
            with mock.patch(
                'flooding_lib.excel_import_export.FieldInfo'):
                eie.create_excel_file(project)
                eie.FieldInfo.assert_called_with(scenariolistmock)

    def test_no_scenarios(self):
        """If there are no scenarios, function should return None and
        there should be no file."""
        project = ProjectF.create()
        filename = "/tmp/create_excel_file.xls"
        workbook = eie.create_excel_file(project, filename)
        self.assertEquals(workbook, None)
        self.assertFalse(os.path.exists(filename))

    @mock.patch(
        'flooding_lib.excel_import_export.FieldInfo.rows',
        return_value=())
    def test_writes_headers_to_sheet(self, rowmock):
        """Function should use the result of fieldinfo.headers() to
        write the header."""
        headers = [
            {'headername': 'test1', 'fieldname': 'testfield1',
             'fieldtype': 'int', 'fieldhint': 'het is groen'},
            {'headername': 'test1', 'fieldname': 'testfield2',
             'fieldtype': 'string', 'fieldhint': 'het is groen'},
            ]

        with mock.patch(
            'flooding_lib.excel_import_export.FieldInfo.headers',
            return_value=headers):
            with mock.patch(
                'flooding_lib.excel_import_export.write_domeinlijst',
                return_value=True):
                project = ProjectF.create()
                ScenarioF.create().set_project(project)
                filename = '/tmp/testfile.xls'

                eie.create_excel_file(project, filename)

                workbook = xlrd.open_workbook(filename)
                self.assertEquals(workbook.nsheets, 2)
                sheet = workbook.sheet_by_index(0)

                self.assertEquals(sheet.cell_value(0, 0), 'test1')
                self.assertEquals(sheet.cell_value(1, 0), 'testfield1')
                self.assertEquals(sheet.cell_value(2, 0), 'int')
                self.assertEquals(sheet.cell_value(3, 0), 'het is groen')
                self.assertEquals(sheet.cell_value(0, 1), 'test1')
                self.assertEquals(sheet.cell_value(1, 1), 'testfield2')
                self.assertEquals(sheet.cell_value(2, 1), 'string')
                self.assertEquals(sheet.cell_value(3, 1), 'het is groen')
                os.remove(filename)

    def test_writes_data_to_sheet(self):
        the_cells = (eie.Cell(value='2', pattern=''),
                     eie.Cell(value='3', pattern=''))

        class Row(object):
            def columns(self):
                return the_cells

        with mock.patch('flooding_lib.excel_import_export.FieldInfo.headers',
                        return_value=()):
            with mock.patch('flooding_lib.excel_import_export.FieldInfo.rows',
                            return_value=[Row()]):
                project = ProjectF.create()
                ScenarioF.create().set_project(project)
                filename = '/tmp/testfile.xls'

                eie.create_excel_file(project, filename)

                workbook = xlrd.open_workbook(filename)
                self.assertEquals(workbook.nsheets, 2)
                sheet = workbook.sheet_by_index(0)

                self.assertEquals(sheet.cell_value(4, 0), '2')
                self.assertEquals(sheet.cell_value(4, 1), '3')
                os.remove(filename)


class TestFieldInfo(TestCase):
    """Tests for the FieldInfo class."""

    def test_headers_from_inputfields(self):
        """Test that it uses the headers from
        grouped_input_fields()."""
        inputfield = InputFieldF.build(name="testfield")
        grouped_input_fields = [{
                'id': 1, 'title': 'testheader', 'fields': [
                    inputfield]}]

        with mock.patch(
        'flooding_lib.tools.importtool.models.InputField.grouped_input_fields',
            return_value=grouped_input_fields):
            fieldinfo = eie.FieldInfo([])
            headers = list(fieldinfo.headers_from_inputfields())

            self.assertEquals(len(headers), 1)
            self.assertEquals(headers[0]['headername'], 'testheader')
            self.assertEquals(headers[0]['inputfield'], inputfield)

    def test_add_extra_header_fields_name(self):
        """header['fieldname'] should be equal to the field's name."""

        inputfield = InputFieldF(name='test 123')
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        self.assertEquals(header['fieldname'], 'test 123')

    def test_add_extra_header_fields_type(self):
        """header['fieldtype'] should be equal to the translated version
        of the choice's description."""

        activate('nl')

        inputfield = InputFieldF(
            type=InputField.TYPE_STRING,
            destination_table='Scenario')
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        self.assertEquals(header['fieldtype'], u'Tekst')

        deactivate()

    def test_add_extra_header_fields_type_date(self):
        """header['fieldtype'] should be equal to a specific string in
        case the inputfield's type is TYPE_DATE."""

        inputfield = InputFieldF(
            type=InputField.TYPE_DATE,
            destination_table='Scenario')
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        self.assertEquals(header['fieldtype'], u'Datum (DD/MM/JJJJ)')

    def test_add_extra_header_fields_type_ignored(self):
        """If an inputfield is ignored, we place a notice in the type field"""

        inputfield = InputFieldF(
            type=InputField.TYPE_DATE,
            destination_table='Project')
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        # Field type contains a text within ( )
        self.assertTrue(header['fieldtype'].startswith('(') and
                        header['fieldtype'].endswith(')'))

    def test_add_extra_header_fields_hint(self):
        """header['fieldhint'] should be equal to the field's excel hint."""

        inputfield = InputFieldF(excel_hint='test 123')
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        self.assertEquals(header['fieldhint'], 'test 123')

    def test_headers_from_inputfields_first_empty(self):
        with mock.patch(
         'flooding_lib.excel_import_export.FieldInfo.headers_from_inputfields',
            return_value=()):
            fields = list(eie.FieldInfo([]).headers())

            self.assertEquals(fields[0]['headername'], '')
            self.assertEquals(fields[0]['fieldname'], '')
            self.assertEquals(fields[0]['fieldtype'], '')

            # fieldhint isn't empty, we've placed a hint about the
            # scenario ids there.
            #self.assertEquals(fields[0]['fieldhint'], '')

    def test_headers_calls_methods(self):
        header = object()

        mock_add_extra_header_fields = mock.MagicMock(return_value="whee")

        with mock.patch(
         'flooding_lib.excel_import_export.FieldInfo.headers_from_inputfields',
            return_value=iter((header,))):
            with mock.patch(
         'flooding_lib.excel_import_export.FieldInfo.add_extra_header_fields',
                new=mock_add_extra_header_fields):
                fields = list(eie.FieldInfo([]).headers())

                # Check fields[1], because fields[0] is the empty header
                self.assertEquals(fields[1], "whee")
                mock_add_extra_header_fields.assert_called_with(header)

    def test_rows(self):
        mockscenariorow = mock.MagicMock(return_value="whee")

        with mock.patch(
            'flooding_lib.excel_import_export.FieldInfo.headers',
            return_value=()):
            with mock.patch(
                'flooding_lib.excel_import_export.ScenarioRow',
                new=mockscenariorow):
                fieldinfo = eie.FieldInfo([])
                fieldinfo.scenariolist = ["scenario"]

                rows = list(fieldinfo.rows())

                # Rows[0] is equal to a ScenarioRow (turned into the
                # string "whee" by us)
                self.assertEquals(rows[0], "whee")

                # The ScenarioRow was constructed with the first
                # scenario in scenariolist, again set to use a string
                # by us, and the value of headers, an empty tuple:
                mockscenariorow.assert_called_with("scenario", ())


class TestScenarioRow(TestCase):
    def test_first_is_scenario_id(self):
        scenario = ScenarioF.create()

        scenariorow = eie.ScenarioRow(scenario, ())

        for column in scenariorow.columns():
            self.assertEquals(column.value, scenario.id)
            break

    def test_rest_calls_value_for_inputfield(self):
        field_value = 3
        inputfield = InputFieldF.build(type=InputField.TYPE_INTEGER)

        with mock.patch(
            'flooding_lib.models.Scenario.value_for_inputfield',
            return_value=field_value) as patched:
            headers = ({}, {'inputfield': inputfield})
            scenariorow = eie.ScenarioRow(ScenarioF.build(), headers)

            columns = scenariorow.columns()
            columns.next()  # Skip scenario id
            self.assertEquals(columns.next().value, field_value)
            patched.assert_called_with(inputfield)


class TestGetHeaderStyleFor(TestCase):
    def test_wraps(self):
        """All header text should wrap"""
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(0, 0, {})
            self.assertTrue("wrap on" in easyxf.call_args[0][0])

    def test_row_1_bold(self):
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(1, 1, {})
            self.assertTrue("bold on" in easyxf.call_args[0][0])

    def test_row_2_not_bold(self):
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(2, 1, {})
            self.assertTrue("bold on" not in easyxf.call_args[0][0])

    def test_ignored_is_gray(self):
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(1, 1, {'ignore': True})
            self.assertTrue("fore_color gray" in easyxf.call_args[0][0])

    def test_required_is_orange(self):
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(1, 1, {'required': True})
            self.assertTrue("fore_color orange" in easyxf.call_args[0][0])

    def test_not_required_is_light_yellow(self):
        with mock.patch(
            'flooding_lib.excel_import_export.make_style') as easyxf:
            eie.get_header_style_for(1, 1, {'required': False})
            self.assertTrue(
                "fore_color light_yellow" in easyxf.call_args[0][0])


class TestWriteDomeinlijst(TestCase):
    def test_false_if_wrong_fieldtype(self):
        self.assertFalse(eie.write_domeinlijst(
                None, 0, {'fieldtype': 'String'}))

    def test_one_inputfield_one_code(self):
        worksheet = mock.MagicMock()

        inputfield = InputFieldF.build(
            type=InputField.TYPE_SELECT,
            options=repr({1: "first line"}))

        header = {
            'fieldtype': 'Select',
            'inputfield': inputfield,
            'fieldname': 'Test'
            }

        self.assertTrue(eie.write_domeinlijst(worksheet, 0, header))

        expected = [
            mock.call(0, 0, "Code"),
            mock.call(0, 1, "Test"),
            mock.call(1, 0, 1),
            mock.call(1, 1, "first line")]

        self.assertEquals(worksheet.write.call_args_list, expected)

    def test_false_at_incorrect_options(self):
        inputfield = InputFieldF.build(
            type=InputField.TYPE_SELECT,
            options="not a dictionary at all!")

        header = {
            'fieldtype': 'Select',
            'inputfield': inputfield
            }

        self.assertFalse(eie.write_domeinlijst(None, 0, header))

    def test_a_string_isnt_a_dict(self):
        inputfield = InputFieldF.build(
            type=InputField.TYPE_SELECT,
            options=repr("not a dictionary at all!"))

        header = {
            'fieldtype': 'Select',
            'inputfield': inputfield
            }

        self.assertFalse(eie.write_domeinlijst(None, 0, header))


class TestGetScenarioWorksheet(TestCase):
    def test_trivial(self):
        worksheet = object()
        workbook_attrs = {
            'sheet_by_name.return_value': worksheet
            }
        with mock.patch(
            'xlrd.open_workbook',
            return_value=mock.MagicMock(**workbook_attrs)) as patched:
            sheet = eie.get_scenario_worksheet('path')

            patched.assertCalledWith(('path',))
            self.assertEquals(sheet, worksheet)


class TestImportUploadedExcelFile(TestCase):
    @mock.patch('flooding_lib.excel_import_export.import_header',
                return_value=(None, []))
    def test_calls_import_header(self, patched_import_header):
        cell = mock.MagicMock(value=15)
        cells = [cell]
        sheetattrs = {'row.return_value': cells}
        worksheet = mock.MagicMock(**sheetattrs)

        with mock.patch(
            'flooding_lib.excel_import_export.get_scenario_worksheet',
            return_value=worksheet):
            self.assertEquals([], eie.import_uploaded_excel_file('', set()))

        patched_import_header.assertCalledWith(cells)

    @mock.patch('flooding_lib.excel_import_export.import_header',
                return_value=(None, ["error!"]))
    def test_import_headers_returns_errors(self, patched_import_header):
        cell = mock.MagicMock(value=15)
        cells = [cell]
        sheetattrs = {'row.return_value': cells}
        worksheet = mock.MagicMock(**sheetattrs)

        with mock.patch(
            'flooding_lib.excel_import_export.get_scenario_worksheet',
            return_value=worksheet):
            self.assertEquals(
                ["error!"],
                eie.import_uploaded_excel_file('', set()))

    @mock.patch('flooding_lib.excel_import_export.import_header',
                return_value=(eie.ImportedHeader(), []))
    @mock.patch('flooding_lib.excel_import_export.import_scenario_row',
                return_value=[])
    def test_rows_calls_get_scenario_row(
        self, patched_import_header, patched_import_scenario_row):
        cell = object()
        onecellrow = [cell]

        def row(i):
            if i < 4:
                return []
            return onecellrow

        worksheet = mock.MagicMock(row=row, nrows=5)

        allowed_ids = set()

        with mock.patch(
            'flooding_lib.excel_import_export.get_scenario_worksheet',
            return_value=worksheet):
            eie.import_uploaded_excel_file('', allowed_ids)

            patched_import_scenario_row.assertCalledWith(
                (patched_import_header.return_value,
                 4,
                 onecellrow,
                 allowed_ids))

    @mock.patch('flooding_lib.excel_import_export.import_header',
                return_value=(eie.ImportedHeader(), []))
    @mock.patch('flooding_lib.excel_import_export.import_scenario_row',
                return_value=["error!"])
    def test_get_scenario_row_returns_errors(
        self, patched_import_header, patched_import_scenario_row):
        worksheet = mock.MagicMock(row=lambda i: [], nrows=5)

        with mock.patch(
            'flooding_lib.excel_import_export.get_scenario_worksheet',
            return_value=worksheet):
            errors = eie.import_uploaded_excel_file('', set())
            self.assertEquals(errors, ["error!"])


class TestImportedHeader(TestCase):
    def test_trivial(self):
        eie.ImportedHeader()

    def test_returns_none_for_fieldnr_0(self):
        self.assertEquals(
            None,
            eie.ImportedHeader().find_field_by_name(0, ''))

    def test_finds_field(self):
        name = u"dit is een input field"
        field = InputFieldF.create(name=name)

        fields = {}
        header = eie.ImportedHeader(fields)

        foundfield = header.find_field_by_name(1, name)

        self.assertEquals(field, foundfield)
        self.assertTrue(fields[1] is foundfield)

    def test_exception_if_not_found(self):
        header = eie.ImportedHeader()
        self.assertRaises(
            eie.ImportedHeader.HeaderException,
            lambda: header.find_field_by_name(1, u"bestaat niet"))

    def test_exception_if_occurs_twice(self):
        name = u"dit is een input field"
        InputFieldF.create(name=name)
        header = eie.ImportedHeader()

        header.find_field_by_name(1, name)

        self.assertRaises(
            eie.ImportedHeader.HeaderException,
            lambda: header.find_field_by_name(2, name))

    def test_getitem(self):
        name = u"dit is een input field"
        InputFieldF.create(name=name)
        header = eie.ImportedHeader()

        foundfield = header.find_field_by_name(1, name)

        self.assertTrue(header[1] is foundfield)

    def test_can_iterate(self):
        name = u"dit is een input field"
        field = InputFieldF.create(name=name)
        header = eie.ImportedHeader()

        header.find_field_by_name(1, name)

        for i, iterfield in enumerate(header):
            self.assertEquals(i, 0)  # We should only come here once
            self.assertEquals(field, iterfield)


class TestImportHeader(TestCase):
    def test_trivial(self):
        header_titles = ["title"]
        find_field_by_name = mock.MagicMock()
        with mock.patch(
       'flooding_lib.excel_import_export.ImportedHeader',
            return_value=mock.MagicMock(
                find_field_by_name=find_field_by_name)):
            eie.import_header(header_titles)
            find_field_by_name.assert_called_with(0, "title")

    def test_find_field_throws_exception(self):
        header_titles = ["title"]

        # Safe it here because otherwise it'll be mocked...
        real_exception = eie.ImportedHeader.HeaderException

        def throwing(column, title):
            raise real_exception("message")

        find_field_by_name = mock.MagicMock(side_effect=throwing)
        with mock.patch(
       'flooding_lib.excel_import_export.ImportedHeader',
            return_value=mock.MagicMock(
                find_field_by_name=find_field_by_name),
            HeaderException=real_exception):
            _, errors = eie.import_header(header_titles)
            self.assertEquals(errors, ["message"])


class TestImportScenarioRow(TestCase):
    """Tests for the import_scenario_row function."""
    def test_empty_row(self):
        """Shouldn't really do anything, just return"""
        errors = eie.import_scenario_row(eie.ImportedHeader(), 5, [], set())
        self.assertEquals(errors, [])

    def test_empty_scenario_id(self):
        """Should give an error message mentioning the row nr"""
        errors = eie.import_scenario_row(
            eie.ImportedHeader(), 66, [mock.MagicMock(value="")], set())

        self.assertEquals(len(errors), 1)
        self.assertTrue("66" in errors[0])

    def test_bad_scenario_id(self):
        """Tests that a row with a badly formed scenario id returns an
        error, and that the error message includes the line number."""
        errors = eie.import_scenario_row(
            eie.ImportedHeader(), 66,
            [mock.MagicMock(value="scenarioid")], set())

        self.assertEquals(len(errors), 1)
        self.assertTrue("66" in errors[0])

    def test_unknown_scenario_id(self):
        """Tests that using a nonexisting scenario id results in an
        error, and that the error message includes the line number."""
        errors = eie.import_scenario_row(
            eie.ImportedHeader(), 66, [mock.MagicMock(value=42313)], set())

        self.assertEquals(len(errors), 1)
        self.assertTrue("66" in errors[0])

    def test_disallowed_scenario_id(self):
        """Tests that using a scenario id that exists but isn't in
        allowed scenario id fails."""
        scenario = ScenarioF.create()
        allowed_ids = set((scenario.id + 1,))
        errors = eie.import_scenario_row(
            eie.ImportedHeader(),
            66,
            [mock.MagicMock(value=scenario.id)],
            allowed_ids)

        self.assertEquals(len(errors), 1)
        self.assertTrue("66" in errors[0])


class FakeCell(object):
    """Helper object to hold a value; fake Excel cell."""
    def __init__(self, value):
        self.value = value


class TestImportScenarioRow2(TestCase):
    """More tests for import_scenario_row. These tests assume that
    there is a scenario, and has helper functions to create a header
    and a number of cells."""

    def setUp(self):
        """Create a scenario, let the first field of the row contain a
        cell with that scenario's ID."""
        self.scenario = ScenarioF.create()
        self.rowstart = [FakeCell(unicode(self.scenario.id))]
        self.allowed_ids = set((self.scenario.id,))

    def build_header(self, *inputfields):
        """Build an eie.ImportedHeader object using named
        inputfields."""
        fields = {}
        i = 1
        for inputfield in inputfields:
            fields[i] = inputfield
            i += 1
        return eie.ImportedHeader(fields)

    @mock.patch('flooding_lib.models.Scenario.set_value_for_inputfield')
    def test_skips_ignored_inputfield(self, mocked_setvalue):
        """Some destination tables, e.g. Project, can't be modified
        from this import and should be skipped."""
        inputfield = InputFieldF.build(
            destination_table='Project',
            type=InputField.TYPE_INTEGER)
        cell = FakeCell(value=3)

        header = self.build_header(inputfield)

        eie.import_scenario_row(
            header, 66, self.rowstart + [cell], self.allowed_ids)

        self.assertFalse(mocked_setvalue.called)

    @mock.patch('flooding_lib.models.Scenario.set_value_for_inputfield')
    def test_skips_empty_cell(self, mocked_setvalue):
        """If a cell isn't filled in, skip it."""
        inputfield = InputFieldF.build(
            destination_table='Scenario',
            type=InputField.TYPE_INTEGER)
        cell = FakeCell(value=u'')

        header = self.build_header(inputfield)

        eie.import_scenario_row(
            header, 66, self.rowstart + [cell], self.allowed_ids)

        self.assertFalse(mocked_setvalue.called)

    @mock.patch('flooding_lib.models.Scenario.set_value_for_inputfield')
    def test_some_inputfield(self, mocked_setvalue):
        """Test with an integer inputfield and see what happens."""

        inputfield = InputFieldF.build(
            destination_table='scenario',
            type=InputField.TYPE_INTEGER)
        cell = FakeCell(value=3)

        header = self.build_header(inputfield)

        eie.import_scenario_row(
            header, 66, self.rowstart + [cell], self.allowed_ids)

        self.assertTrue(mocked_setvalue.called)
        c_inputfield, c_value = mocked_setvalue.call_args[0]

        self.assertTrue(c_inputfield is inputfield)
        self.assertTrue(isinstance(c_value, IntegerValue))

    def test_wrong_value_raises_error(self):
        """A nonsensical value in a cell returns an error message."""
        inputfield = InputFieldF.build(
            destination_table='scenario',
            type=InputField.TYPE_INTEGER)
        cell = FakeCell(value="whee")

        header = self.build_header(inputfield)

        errors = eie.import_scenario_row(
            header, 66, self.rowstart + [cell], self.allowed_ids)

        self.assertEquals(len(errors), 1)
        self.assertTrue("66" in errors[0])
