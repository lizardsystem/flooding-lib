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
#* Purpose    : runs the max-waterdepth tool for creating shape-files for
#*              all csv files in the given folder.
#*
#*
#* Usage      : run_waterdepth_tool_for_all_csv_in_folder.py --help
#*
#* initial programmer :  Jan-Maarten Verbree
#* initial date       :  200908269
#**********************************************************************

import os
import glob
import logging
import sys

log = logging.getLogger('lizard.run_waterdepth_tool')
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
        success = 0
        gridsize = -1
        exportid = -1
        try:
            log.info('Processing file: ' + str(csvfile))
            textfile = os.path.splitext(csvfile)[0] + '.txt'
            text = open(textfile)
            for line in text:
                if line.find("Gridsize:") > -1:
                    gridsize = int(line[9:])
                    log.info('Gridsize = ' + str(gridsize))
                if line.find("ExportId:") > -1:
                    exportid = int(line[9:])
            if gridsize > -1 and exportid > -1:
                success = os.system(
                    options.pythonpath + ' ' + options.mwdtool + ' ' +
                    csvfile + ' ' + options.dikes + ' ' +
                    options.provinces + ' ' + str(gridsize) + ' ' +
                    str(exportid))
        except Exception, e:
            log.error('Error: ' + str(e))
            sys.exit(1)
        else:
            text.close()
        if success == 0:
            os.remove(csvfile)
            os.remove(textfile)
        else:
            log.error('An error occurred in the tool that has been processed.')

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
        '--pythonpath', help='pythonpath for the export max waterdepth tool')
    parser.add_option(
        '--mwdtool', help='path for the export max waterdepth tool')
    parser.add_option(
        '--csvpath',
        help='the path to the folder where the csv files are stored')
    parser.add_option(
        '--dikes',
        help='the shapefile describing the dikes of the Netherlands')
    parser.add_option(
        '--provinces',
        help='the shapefile describing the borders of the ' +
        'provinces of the Netherlands')

    (options, args) = parser.parse_args()
    if not (options.pythonpath and options.mwdtool and
            options.csvpath and options.dikes and
            options.provinces):
        parser.print_help()
    else:
        main(options, args)
        log.info("Everything done. Thanks for running this script.")
