# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from django.test import TestCase
import os
import zipfile

from flooding_lib.util import files

TMPFILE = '/tmp/test.txt'
ZIPFILE = '/tmp/test.zip'


class TestTemporarilyUnzipped(TestCase):
    def test_trivial(self):
        for f in (TMPFILE, ZIPFILE):
            if os.path.exists(f):
                os.remove(f)

        f = open(TMPFILE, 'w')
        f.write("whee\n")
        f.close()

        os.system("/usr/bin/zip -q {zipfile} {tmpfile}"
                  .format(zipfile=ZIPFILE, tmpfile=TMPFILE))

        with files.temporarily_unzipped(ZIPFILE) as names:
            self.assertEquals(
                [os.path.basename(name) for name in names],
                ['test.txt'])

            name = names[0]
            f = open(name, 'w')
            f.write("ook whee\n")
            f.close()

        self.assertFalse(os.path.exists(name))

        zipf = zipfile.ZipFile(ZIPFILE)
        self.assertEquals(
            "ook whee\n",
            zipf.read('tmp/test.txt'))
        zipf.close()
