# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import datetime
import factory
import mock

from django.test import TestCase
from django.contrib.auth.models import User

from flooding_lib.tools.importtool import models


class UserF(factory.Factory):
    FACTORY_FOR = User

    username = 'remco'


class ImportScenarioF(factory.Factory):
    FACTORY_FOR = models.ImportScenario

    name = 'test'
    owner = UserF.create()


class ImportScenarioInputFieldF(factory.Factory):
    FACTORY_FOR = models.ImportScenarioInputField

    importscenario = factory.LazyAttribute(lambda a: ImportScenarioF.build())
    validation_remarks = ''


class InputFieldF(factory.Factory):
    FACTORY_FOR = models.InputField

    name = 'dummy'
    header = models.InputField.HEADER_SCENARIO
    import_table_field = ''
    destination_table = ''
    destination_field = ''
    type = models.InputField.TYPE_INTEGER
    options = ''
    visibility_dependency_value = ''
    excel_hint = ''
    hover_text = ''
    hint_text = ''
    required = False


class RORKeringF(factory.Factory):
    FACTORY_FOR = models.RORKering
    
    title = 'dummy'
    uploaded_at = datetime.datetime.today()
    owner = UserF.create(username='alex')
    file_name = 'wateren.zip'
    status = models.RORKering.NOT_APPLIEND
    type_kering= models.RORKering.PRIMARE
    description = ''


class TestStringValue(TestCase):
    """StringValues are trivial and only need a single test."""
    def test_trivial(self):
        string_value = models.StringValue()
        string_value.set('teststring')

        self.assertEquals(unicode(string_value), u'teststring')
        self.assertEquals(string_value.to_excel(), u'teststring')


class TestDateValue(TestCase):
    def setUp(self):
        self.dateobject = models.DateValue()

    def test_accepts_date_object(self):
        self.dateobject.set(datetime.date(2012, 8, 15))
        self.assertEquals(self.dateobject.value, "2012-08-15")

    def test_accepts_datetime_object(self):
        self.dateobject.set(datetime.datetime(2012, 8, 15))
        self.assertEquals(self.dateobject.value, "2012-08-15")

    def test_accepts_excel_float(self):
        self.dateobject.set(40725.0)
        self.assertEquals(self.dateobject.value, "2011-07-01")

    def test_accepts_excel_date_as_string(self):
        self.dateobject.set("40725.0")
        self.assertEquals(self.dateobject.value, "2011-07-01")

    def test_accepts_normal_value(self):
        self.dateobject.set("2012-08-15")
        self.assertEquals(self.dateobject.value, "2012-08-15")

    def test_otherwise_value_error(self):
        self.assertRaises(ValueError, lambda: self.dateobject.set("whee"))

    def test_strange_value_value_error(self):
        self.assertRaises(ValueError, lambda: self.dateobject.set(object()))

    def test_to_excel(self):
        self.dateobject.set("2012-08-21")
        d = self.dateobject.to_excel()

        self.assertTrue(isinstance(d, datetime.date))
        self.assertEquals(unicode(d), "2012-08-21")

    def test_to_excel_legacy(self):
        self.dateobject.value = "40725.0"
        d = self.dateobject.to_excel()

        self.assertTrue(isinstance(d, datetime.date))
        self.assertEquals(unicode(d), "2011-07-01")

    def test_unicode(self):
        self.dateobject.value = "2012-08-21"
        self.assertEquals(unicode(self.dateobject), "2012-08-21")


class TestIntegerValue(TestCase):
    def test_trivial(self):
        integervalue = models.IntegerValue()

        integervalue.set(3)
        self.assertEquals(integervalue.to_excel(), 3)
        self.assertEquals(unicode(integervalue), "3")

    def test_from_string(self):
        integervalue = models.IntegerValue()
        integervalue.set("3.0")
        self.assertEquals(integervalue.value, 3)


class TestSelectValue(TestCase):
    def setUp(self):
        self.selectvalue = models.SelectValue()
        self.selectvalueoptions = models.SelectValue()

    def test_set_integer_trivial(self):
        self.selectvalue = models.SelectValue()
        self.selectvalue.set(10)

        self.assertEquals(self.selectvalue.value, 10)
        self.assertEquals(self.selectvalue.to_excel(), 10)
        self.assertEquals(unicode(self.selectvalue), "10")

    def test_string_without_options_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            lambda: self.selectvalue.set("some string"))

    def test_unknown_option_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            lambda: self.selectvalueoptions.set(
                1,
                parsed_options={2: "some string"}))

    def test_string_unknown_option_raises_valueerror(self):
        self.assertRaises(
            ValueError,
            lambda: self.selectvalueoptions.set(
                "some string",
                parsed_options={1: "some other string"}))

    def test_string_known_option_works(self):
        self.selectvalueoptions.set(
            "some known string",
            parsed_options={1: "some known string"})

        self.assertEquals(self.selectvalueoptions.value, 1)

    def test_unicode_is_the_string_representation_from_options(self):
        self.selectvalueoptions.set(
            1,
            parsed_options={1: "some string"})
        self.assertEquals(unicode(self.selectvalueoptions), "some string")

    def test_unicode_is_unicode_of_integer_otherwise(self):
        self.selectvalue.set(3)
        self.assertEquals(unicode(self.selectvalue), "3")


class TestBooleanValue(TestCase):
    def setUp(self):
        self.booleanvalue = models.BooleanValue()

    def true(self):
        self.assertEquals(self.booleanvalue.value, 1)

    def false(self):
        self.assertEquals(self.booleanvalue.value, 0)

    def test_int_input(self):
        self.booleanvalue.set(5)
        self.true()
        self.booleanvalue.set(0)
        self.false()

    def test_string_input(self):
        self.booleanvalue.set("True")
        self.true()
        self.booleanvalue.set("false")
        self.false()
        self.booleanvalue.set("ja")
        self.true()
        self.booleanvalue.set("nee")
        self.false()

    def test_unknown_raises_value_error(self):
        self.assertRaises(ValueError, lambda: self.booleanvalue.set("whee"))

    def test_to_excel(self):
        self.booleanvalue.set(True)
        self.assertEquals(self.booleanvalue.to_excel(), "true")

    def test_unicode(self):
        self.booleanvalue.set(True)
        self.assertEquals(unicode(self.booleanvalue), "1")


class TestFloatValue(TestCase):
    """Nothing special about floats."""
    def test_trivial(self):
        floatvalue = models.FloatValue()
        floatvalue.set("3.66")
        self.assertEquals(floatvalue.value, 3.66)
        self.assertEquals(floatvalue.to_excel(), 3.66)
        self.assertEquals(unicode(floatvalue), "3.66")


class TestIntervalValue(TestCase):
    def test_trivial(self):
        intervalvalue = models.IntervalValue()
        intervalvalue.set(3.5)

        self.assertEquals(intervalvalue.value, 3.5)
        self.assertEquals(unicode(intervalvalue), "3.5")
        self.assertEquals(intervalvalue.to_excel(), "3 d 12:00")

    def test_string_input(self):
        intervalvalue = models.IntervalValue()
        intervalvalue.set("3 d 12:00")
        self.assertEquals(intervalvalue.value, 3.5)


class TestTextValue(TestCase):
    """TextValues seem trivial."""
    def test_trivial(self):
        textvalue = models.TextValue()
        textvalue.set("whee")
        self.assertEquals(textvalue.value, "whee")
        self.assertEquals(textvalue.to_excel(), "whee")
        self.assertEquals(unicode(textvalue), "whee")


class TestImportScenarioInputField(TestCase):
    def get_resulting_isif(self, inputfield_type, inputfield_name, value_in):
        """Create a new scenario and an inputfield of type inputfield_type and
        name inputfield_name. Set its value in this scenario to value_in.
        Then get the input field back from the database, get the filled in
        ImportScenarioInputField back from the database, and return it."""

        import_scenario = ImportScenarioF.create()

        input_field = InputFieldF.create(
            type=inputfield_type, name=inputfield_name)

        isif = ImportScenarioInputFieldF.create(
            importscenario=import_scenario, inputfield=input_field)
        isif.setValue(value_in)

        input_field_from_db = (
            models.InputField.objects.get(name=inputfield_name))

        isif_from_db = models.ImportScenarioInputField.objects.get(
            importscenario=import_scenario,
            inputfield=input_field_from_db)

        return isif_from_db

    def testSetGetInteger(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_INTEGER, 'test_integer', 10)
        self.assertEquals(isif.getValue(), 10)

    def testSetGetFloat(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_FLOAT, 'test_float', 10.5)
        self.assertEquals(isif.getValue(), 10.5)

    def testSetGetString(self):
        isif = self.get_resulting_isif(
            models.InputField.TYPE_STRING, 'test_string', 'test_string')
        self.assertEquals(isif.getValue(), 'test_string')

    def testSetIntervalRaisesOnWrongFormat(self):
        self.assertRaises(ValueError, lambda: self.get_resulting_isif(
            models.InputField.TYPE_INTERVAL, 'test_interval',
            "this is not the right format for an interval"))

    def testSetGetInterval(self):
        with mock.patch(
      'flooding_lib.tools.importtool.models.get_dayfloat_from_intervalstring',
            new=mock.MagicMock(return_value=5.5)) as mocked_function:
            isif = self.get_resulting_isif(
                models.InputField.TYPE_INTERVAL, 'test_interval', '5 d 10:30')
            self.assertEquals(isif.getValue(), 5.5)
            mocked_function.assertCalledWith('5 d 10:30')


class TestImportScenario(TestCase):
    def testReceiveInputFields(self):
        testfields = {
            'test1': 'whee',
            'test2': 3
            }

        test1 = InputFieldF.create(
            name='test1',
            type=models.InputField.TYPE_STRING)
        test2 = InputFieldF.create(
            name='test2',
            type=models.InputField.TYPE_INTEGER)

        importscenario = ImportScenarioF.create()

        importscenario.receive_input_fields(testfields)

        try:
            isif = models.ImportScenarioInputField.objects.get(
                importscenario=importscenario, inputfield=test1)
        except models.ImportScenarioInputField.DoesNotExist:
            raise AssertionError(
                "importscenarioimportfield test1 does not exist")

        try:
            value = models.StringValue.objects.get(
                importscenario_inputfield=isif)
            self.assertEquals(value.value, 'whee')
        except models.StringValue.DoesNotExist:
            raise AssertionError("stringvalue does not exist")

        try:
            isif = models.ImportScenarioInputField.objects.get(
                importscenario=importscenario, inputfield=test2)
        except models.ImportScenarioInputField.DoesNotExist:
            raise AssertionError(
                "importscenarioimportfield test2 does not exist")

        try:
            value = models.IntegerValue.objects.get(
                importscenario_inputfield=isif)
            self.assertEquals(value.value, 3)
        except models.StringValue.DoesNotExist:
            raise AssertionError("integervalue does not exist")

    def test_update_scenario_name_doesnt_exist(self):
        """If there is no inputfield with a scenario name, set the
        name to '-'"""
        importscenario = ImportScenarioF()
        importscenario.update_scenario_name()
        self.assertEquals(importscenario.name, "-")

    def test_update_scenario_name_works(self):
        importscenario = ImportScenarioF()

        inputfield = InputFieldF.create(
            type=models.InputField.TYPE_STRING,
            destination_table="Scenario",
            destination_field="name")

        isif = ImportScenarioInputFieldF.create(
            importscenario=importscenario,
            inputfield=inputfield)

        isif.setValue("name!")

        importscenario.update_scenario_name()
        self.assertEquals(importscenario.name, "name!")

    def test_update_scenario_name_empty(self):
        importscenario = ImportScenarioF()

        inputfield = InputFieldF.create(
            type=models.InputField.TYPE_STRING,
            destination_table="Scenario",
            destination_field="name")

        isif = ImportScenarioInputFieldF.create(
            importscenario=importscenario,
            inputfield=inputfield)

        isif.setValue("")

        importscenario.update_scenario_name()
        self.assertEquals(importscenario.name, "-")


class TestInputField(TestCase):
    def test_grouped_input_fields(self):
        inputfield = InputFieldF.create(
            header=models.InputField.HEADER_REMAINING)

        gif = models.InputField.grouped_input_fields()

        # There is an element in gif that has 'id' equal to the header we set
        self.assertTrue(
            any(giffield['id'] == models.InputField.HEADER_REMAINING
                for giffield in gif))
        for g in gif:
            if g['id'] == models.InputField.HEADER_REMAINING:
                giffield = g
                break

        # There is a 'title' field
        self.assertTrue('title' in giffield)

        # giffield['fields'] is an iterable of inputfields and one of
        # them has the id ours has
        self.assertTrue(
            inputfield.id in (inpf.id for inpf in giffield['fields']))

    def test_ignore_in_scenario_excel_files_scenario(self):
        """In scenario import/export excel files, we only want to read
        fields that are related to the scenario (destination table is
        scenario, extrascenarioinfo or scenariobreach) and that make
        sense to import this way (files represented by just a string
        are useless)."""
        inputfield = InputFieldF.build(destination_table='Scenario')
        self.assertFalse(inputfield.ignore_in_scenario_excel_files)

    def test_ignore_in_scenario_excel_files_project(self):
        inputfield = InputFieldF.build(destination_table='Project')
        self.assertTrue(inputfield.ignore_in_scenario_excel_files)

    def test_ignore_in_scenario_excel_files_scenario_file(self):
        inputfield = InputFieldF.build(
            destination_table='Scenario',
            type=models.InputField.TYPE_FILE
            )
        self.assertTrue(inputfield.ignore_in_scenario_excel_files)

    def test_parsed_options_correct(self):
        inputfield = InputFieldF(options=str({"whee": 3}))
        options = inputfield.parsed_options
        self.assertEquals(options["whee"], 3)

    def test_parsed_options_empty(self):
        inputfield = InputFieldF(options='')
        self.assertEquals(inputfield.parsed_options, {})

    def test_parsed_options_syntax_error(self):
        inputfield = InputFieldF(options="whee")
        self.assertEquals(inputfield.parsed_options, {})

    def test_build_value_object(self):
        inputfield = InputFieldF(type=models.InputField.TYPE_INTEGER)
        value_object = inputfield.build_value_object()
        self.assertTrue(isinstance(value_object, models.IntegerValue))

    def test_build_value_object_with_value(self):
        inputfield = InputFieldF(type=models.InputField.TYPE_INTEGER)
        value_object = inputfield.build_value_object(3)
        self.assertEquals(value_object.value, 3)

    @mock.patch('flooding_lib.tools.importtool.models.SelectValue.set')
    def test_build_value_object_uses_options(self, mocked_set):
        inputfield = InputFieldF(
            type=models.InputField.TYPE_SELECT,
            options="{3: 'whee'}")
        inputfield.build_value_object(3)
        self.assertEquals(mocked_set.call_args[0][1], {3: 'whee'})


class TestDisplayValueUnicode(TestCase):
    def test_none(self):
        inputfield = InputFieldF()
        self.assertEquals(inputfield.display_unicode(None), '')

    def test_interval(self):
        inputfield = InputFieldF.build(
            type=models.InputField.TYPE_INTERVAL)
        value_str = inputfield.display_unicode(2.5)
        self.assertEquals(value_str, '2 d 12:00')

    def test_unicode(self):
        """Function used to be called display_string, then bugged on
        this..."""
        s = (u"De EDO scenario\u2019s zijn opgesteld voor de landelijke "
             u"voorbereiding op de gevolgen van overstromingen. Ze zijn "
             u"ook input om de bovenregionale afstemming in de water- en "
             u"openbare orde en veiligheid (OOV) sector vorm te geven.")

        inputfield = InputFieldF.build(
            type=models.InputField.TYPE_STRING)

        try:
            inputfield.display_unicode(s)
        except UnicodeEncodeError:
            self.fail("display_unicode() failed on a Unicode string.")

    def test_select_for_editing(self):
        """Should return the number."""
        inputfield = InputFieldF(
            type=models.InputField.TYPE_SELECT,
            options=repr({1: "whee"}))

        self.assertEquals(inputfield.display_unicode(1), "1")

    def test_select_for_viewing(self):
        """Should return the descriptions."""
        inputfield = InputFieldF(
            type=models.InputField.TYPE_SELECT,
            options=repr({1: "whee"}))

        self.assertEquals(
            inputfield.display_unicode(1, for_viewing_only=True),
            "whee")

    def test_select_unknown_value_just_returns_it(self):
        inputfield = InputFieldF(
            type=models.InputField.TYPE_SELECT,
            options=repr({1: "whee"}))

        self.assertEquals(
            inputfield.display_unicode("grr"),
            "grr")

class TestRORKering(TestCase):

    def setUp(self):
        self.kering = RORKeringF.build(
            type_kering=models.RORKering.PRIMARE,
            status=models.RORKering.APPLIED)

    def test_unicode(self):
        uni = self.kering.__unicode__()
        self.assertTrue(isinstance(uni, unicode))

    def test_kering_as_dict(self):
        kering_dict = self.kering.kering_as_dict
        self.assertEquals(kering_dict['title'], 'dummy')
        self.assertEquals(kering_dict['type_kering'], models.RORKering.TYPE_KERING[0][1])
        self.assertEquals(kering_dict['status'], models.RORKering.STATE[0][1])
