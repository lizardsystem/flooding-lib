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

    name = 'test'
    header = models.InputField.HEADER_REMAINING
    position = 0


DAYFLOAT_FROM_INTERVALSTRING =\
    'flooding_lib.tools.importtool.models.get_dayfloat_from_intervalstring'


class TestGetDayfloat(TestCase):
    def testCorrectInput(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('5 d 10:30'),
            5.4375)

    def testCorrectLargeInput(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('1115 d 10:30'),
            1115.4375)

    def testMissingSpace1(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('5d 10:30'),
            5.4375)

    def testMissingSpace2(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('5 d10:30'),
            5.4375)

    def testNoLeadingZero(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('5 d 10:6'),
            5.420833333333333)

    def testExtraSpace(self):
        self.assertRaises(
            ValueError,
            lambda:
            models.get_dayfloat_from_intervalstring('5 d 10: 6'))

    def testZero(self):
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('0d0:0'),
            0)

    def testNegative(self):
        # Oddly enough, the days are negative, but the hours etc aren't.
        self.assertEquals(
            models.get_dayfloat_from_intervalstring('-1 d 12:00'),
            -0.5)


class TestGetIntervalString(TestCase):
    def testTrivialCorrect(self):
        self.assertEquals(
            models.get_intervalstring_from_dayfloat(5.4375),
            '5 d 10:30')

    def testNegative(self):
        self.assertEquals(
            models.get_intervalstring_from_dayfloat(-0.5),
            '-1 d 12:00')


class TestImportScenarioInputField(TestCase):
    def get_resulting_isif(self, inputfield_type, inputfield_name, value_in):
        """Create a new scenario and an inputfield of type inputfield_type and
        name inputfield_name. Set its value in this scenario to value_in.
        Then get the input field back from the database, get the filled in
        ImportScenarioInputField back from the database, and return it."""

        import_scenario = ImportScenarioF()
        import_scenario.save()

        input_field = InputFieldF(
            type=inputfield_type, name=inputfield_name)
        input_field.save()

        isif = ImportScenarioInputFieldF(
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
            models.InputField.TYPE_INTERVAL, 'test_interval', 0.0))

    def testSetGetInterval(self):
        with mock.patch(
            DAYFLOAT_FROM_INTERVALSTRING,
            new=mock.MagicMock(return_value=5.5)) as mocked_function:
            isif = self.get_resulting_isif(
                models.InputField.TYPE_INTERVAL, 'test_interval', '5 d 10:30')
            self.assertEquals(isif.getValue(), 5.5)
            mocked_function.assertCalledWith('5 d 10:30')
