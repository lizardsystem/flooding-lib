#!/usr/bin/python
# -*- coding: utf-8 -*-
#***********************************************************************
#*
#***********************************************************************
#*                      All rights reserved                           **
#*
#*
#*                                                                    **
#*
#*
#*
#***********************************************************************
#* Purpose    : load the export results files (waterdepth map) such that the
#*              database is updated. The result files have to be transformed
#*              to Result object that are related to an ExportRun.
#*
#*
#* Usage      : update_export_runs.py --help
#*
#* initial programmer :  Jan-Maarten Verbree
#* initial date       :  200908269
#**********************************************************************


import os
import logging
import glob
import sys
import csv
import datetime

# Load settings first, to be able to import the exporttool models
#setup_environ(settings)
from flooding_lib.tools.exporttool.models import ExportRun, Result


log = logging.getLogger('lizard.update_export')
log.setLevel(logging.DEBUG)


def main(options, args):
    #define console log handler
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    console.setLevel(options.console_level)

    #add handler to root logger
    logging.getLogger('').addHandler(console)

    #set loglevel for this module
    log.setLevel(options.loglevel)

    if not os.path.exists(options.csvpath):
        log.error('The folder does not exists.')
        sys.exit(1)

    log.info('Processing list of .csv files')
    for csvfile in glob.glob(os.path.join(options.csvpath, '*.csv')):
        if os.path.splitext(csvfile)[1] != '.csv':
            log.error('No .csv file provided.')
            sys.exit(1)
        log.info('Reading rows and creating Result objects')
        file = open(csvfile, "rb")
        reader = csv.reader(file)

        # Find exportid; count backwards to avoid underscores in foldernames
        exportid = csvfile.split('_')[-2]
        log.debug('exportid = ' + str(exportid))
        try:
            e_run = ExportRun.objects.get(pk=exportid)
        except:
            log.error('No Export Run object found with id: ' + str(exportid))
            sys.exit(1)

        # Skip header
        reader.next()

        for row in reader:
            log.debug(row)

            #Check if object already exists
            existing_objects = Result.objects.filter(
                area=row[0], name=row[1],
                file_location=row[2], export_run=e_run)
            log.debug('existing_result_objects =' + str(existing_objects))
            if not existing_objects:
                r = Result(area=row[0],
                           name=row[1],
                           file_location=row[2],
                           export_run=e_run)
                r.save()
        file.close()
        e_run.state = ExportRun.EXPORT_STATE_DONE
        e_run.run_date = datetime.datetime.fromtimestamp(
            os.path.getctime(csvfile))
        e_run.save()
        os.remove(csvfile)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "usage: %prog [options] [csv_file]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        '--console-level', help='sets the handling level of the console.',
        default=logging.WARNING, type='int')

    parser.add_option(
        '--info', help='be sanely informative - the default',
        action='store_const', dest='loglevel',
        const=logging.INFO, default=logging.INFO)
    parser.add_option(
        '--debug', help='be verbose', action='store_const',
        dest='loglevel', const=logging.DEBUG)
    parser.add_option(
        '--quiet', help='log warnings and errors', action='store_const',
        dest='loglevel', const=logging.WARNING)
    parser.add_option(
        '--extreme-debugging', help='be extremely verbose',
        action='store_const', dest='loglevel', const=0)
    parser.add_option(
        '--silent', help='log only errors', action='store_const',
        dest='loglevel', const=logging.ERROR)

    parser.add_option(
        '--csvpath',
        help='the folder where the csv-files are ' +
        'located that have to be processed')

    (options, args) = parser.parse_args()
    if not (options.csvpath):
        parser.print_help()
    else:
        main(options, args)
        log.info("Everything done. Thanks for running this script.")
