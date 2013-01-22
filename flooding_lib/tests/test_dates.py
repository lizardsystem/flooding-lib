from django.test import TestCase

from flooding_lib import dates


class TestGetDayfloat(TestCase):
    def testCorrectInput(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('5 d 10:30'),
            5.4375)

    def testCorrectLargeInput(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('1115 d 10:30'),
            1115.4375)

    def testMissingSpace1(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('5d 10:30'),
            5.4375)

    def testMissingSpace2(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('5 d10:30'),
            5.4375)

    def testNoLeadingZero(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('5 d 10:6'),
            5.420833333333333)

    def testExtraSpace(self):
        self.assertRaises(
            ValueError,
            lambda:
            dates.get_dayfloat_from_intervalstring('5 d 10: 6'))

    def testZero(self):
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('0d0:0'),
            0)

    def testNegative(self):
        # Oddly enough, the days are negative, but the hours etc aren't.
        self.assertEquals(
            dates.get_dayfloat_from_intervalstring('-1 d 12:00'),
            -0.5)


class TestGetIntervalString(TestCase):
    def testTrivialCorrect(self):
        self.assertEquals(
            dates.get_intervalstring_from_dayfloat(5.4375),
            '5 d 10:30')

    def testNegative(self):
        self.assertEquals(
            dates.get_intervalstring_from_dayfloat(-0.5),
            '-1 d 12:00')
