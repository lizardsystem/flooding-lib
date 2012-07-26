import mock
import os
import xlrd

from django.test import TestCase
from django.utils.translation import activate, deactivate

from flooding_lib import excel_import_export as eie

from flooding_lib.test_models import ProjectF
from flooding_lib.test_models import ScenarioF
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.importtool.test_models import InputFieldF


class FakeObject(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCreateExcelFile(TestCase):
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

    def test_creates_field_info_object(TestCase):
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
        the_cells = (FakeObject(value='2'), FakeObject(value='3'))

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


class TestFilenameForProject(TestCase):
    def test_correct_filename(self):
        """The generated file's name should contain the project id and
        the project's name."""

        pname = "Test project name for testing"
        project = ProjectF.create(name=pname)
        pid = str(project.id)

        path = eie.filename_for_project(project)

        filename = os.path.basename(path)

        self.assertTrue(pid in filename)
        self.assertTrue(pname in filename)


class TestFieldInfo(TestCase):
    def test_headers_from_inputfields(self):
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
        """header['fieldtype'] should be equal to the translated
        string version of the field's type."""

        activate('nl')

        inputfield = InputFieldF(type=InputField.TYPE_DATE)
        fieldinfo = eie.FieldInfo([])

        header = fieldinfo.add_extra_header_fields({
                'inputfield': inputfield})

        self.assertEquals(header['fieldtype'], u'Datum')

        deactivate()

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
            self.assertEquals(fields[0]['fieldhint'], '')

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
        field_value = object()
        inputfield = InputFieldF.build()

        with mock.patch(
            'flooding_lib.models.Scenario.value_for_inputfield',
            return_value=field_value) as patched:
            headers = ({}, {'inputfield': inputfield})
            scenariorow = eie.ScenarioRow(ScenarioF.build(), headers)

            columns = scenariorow.columns()
            columns.next()  # Skip scenario id
            self.assertEquals(columns.next().value, unicode(field_value))
            patched.assert_called_with(inputfield)


class TestGetHeaderStyleFor(TestCase):
    def test_wraps(self):
        """All header text should wrap"""
        with mock.patch('xlwt.easyxf') as easyxf:
            eie.get_header_style_for(0, 0, {})
            self.assertTrue("wrap on" in easyxf.call_args[0][0])

    def test_row_1_bold(self):
        with mock.patch('xlwt.easyxf') as easyxf:
            eie.get_header_style_for(1, 1, {})
            self.assertTrue("bold on" in easyxf.call_args[0][0])

    def test_row_2_not_bold(self):
        with mock.patch('xlwt.easyxf') as easyxf:
            eie.get_header_style_for(2, 1, {})
            self.assertTrue("bold on" not in easyxf.call_args[0][0])

    def test_required_is_orange(self):
        with mock.patch('xlwt.easyxf') as easyxf:
            eie.get_header_style_for(1, 1, {'required': True})
            self.assertTrue("fore_color orange" in easyxf.call_args[0][0])

    def test_not_required_is_light_yellow(self):
        with mock.patch('xlwt.easyxf') as easyxf:
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
