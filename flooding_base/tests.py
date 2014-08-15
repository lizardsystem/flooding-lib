# Smoke test: just import everything and see if smoke comes out:

from django.utils.unittest import TestCase


# Simple test, for testing
class TrivialTest(TestCase):
    def testAddition(self):
        self.assertEquals(1 + 1, 2)
