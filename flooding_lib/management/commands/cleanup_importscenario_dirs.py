"""New animations are .tiff files, in the directories pointed at by
the .basedir property of pyramids.Animation records. In the same
directories, there may be .png and .pgw files of old animations."""

import os
import shutil
import logging

from django.core.management.base import BaseCommand

from flooding_lib.tools.importtool.models import ImportScenario
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # Filter through importsceanrios to delete unused
        # dirs. This way we clean
        # wrong/mistaken importscenarios. 
        count = 0
        importscenario_dir = os.path.join(settings.MEDIA_ROOT, 'import', 'importscenario')
        if not os.path.exists(importscenario_dir):
            logger.error("%s : the path does not exist.", importscenario_dir)
            return

        importscenario_ids = [str(id) for id in ImportScenario.objects.all().values_list('id', flat=True)]
        for dirname in os.listdir(importscenario_dir):
            if dirname in importscenario_ids:
                continue
            try:
                shutil.rmtree(os.path.join(importscenario_dir, dirname))
                count+=1
            except Exception as ex:
                logger.error(ex.message)
        logger.warn("%d importscenario dir(s) removed", count) 
