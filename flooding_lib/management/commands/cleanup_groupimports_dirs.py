"""New animations are .tiff files, in the directories pointed at by
the .basedir property of pyramids.Animation records. In the same
directories, there may be .png and .pgw files of old animations."""

import os
import shutil
import logging

from django.core.management.base import BaseCommand

from flooding_lib.tools.importtool.models import GroupImport
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # Filter through groupimports to delete unused
        # groupimports files and dirs. This way we clean
        # wrong/mistaken groupimports 
        count = 0
        groupimport_dir = os.path.join(settings.MEDIA_ROOT, 'import', 'groupimport')
        if not os.path.exists(groupimport_dir):
            logger.error("%s : the path does not exist.", groupimport_dir)
            return

        groupimport_ids = [str(id) for id in GroupImport.objects.all().values_list('id', flat=True)]
        for dirname in os.listdir(groupimport_dir):
            if dirname in groupimport_ids:
                continue
            try:
                shutil.rmtree(os.path.join(groupimport_dir, dirname))
                count+=1
            except Exception as ex:
                logger.error(ex.message)
        logger.warn("%d importscenario dir(s) removed", count)
