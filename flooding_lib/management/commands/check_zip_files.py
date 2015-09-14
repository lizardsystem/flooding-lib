# Python 3 is coming to town
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os
import glob
import zipfile

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    args = '<path>'
    help = """Walks the directories starting at <path>, test zip-files,
    print info of corrupted zip-files."""

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No path given.")
        path = args[0]
        if not os.path.exists(path) or not os.path.isdir(path):
            raise CommandError("'{0}' is not an existing directory.".
                               format(path))
        self.walk_zips(path)

    def test_zips(self, zippathes):
        for zippath in zippathes:
            try:
                result = ''
                with zipfile.ZipFile(zippath) as zip:
                    result = zip.testzip()
                if result:
                    print('First corrupted file "%s" in zip "%s"' % (
                        result, zipzippzth))
            except:
                print("Corrupted zip: '%s'." % zippath)
                    
    def walk_zips(self, path):
        if os.path.isdir(path):
            walk = os.walk(path)

        for root, dirs, files in walk:
            for dir in dirs:
                zips = glob.glob(os.path.join(root, dir, '*.zip'))
                self.test_zips(zips)

