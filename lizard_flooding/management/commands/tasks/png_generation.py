#!c:/python25/python.exe
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
#* Library    : png_generation
#* Purpose    : convert a set of asc files into png
#* Function   : png_generation.sobek/his_ssm
#*               
#* Project    : J0005
#*  
#* $Id$
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20080909
#**********************************************************************

__revision__ = "$Rev$"[6:-2]

import sys
if sys.version_info < (2, 4):
    print "I think I need version python2.4 and I was called from %d.%d" % sys.version_info[:2]

import logging

log = logging.getLogger('nens.lizard.kadebreuk.uitvoerder') 

SOBEK_PROGRAM_ID = 1
HISSSM_PROGRAM_ID = 2
IMPORT_PROGRAM_ID = 3

if __name__ == '__main__':
    sys.path.append('..')
    
    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)
    
from django.db import transaction
import os, stat
from zipfile import ZipFile, ZIP_DEFLATED
from lizard.flooding.models import Scenario, Result, ResultType
from lizard.base.models import Setting


def common_generation(connection, scenario_id, tmp_dir, source_programs):
    """invokes compute_png_files for all grids

    loop on all results computed for the given scenario_id, unpack
    them into a temporary directory, get the corresponding color
    mapping, convert to png, set in the results record the
    resultpngloc field.  
    """
    import zipfile, nens.asc

    scenario = Scenario.objects.get(pk=scenario_id)
    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value
    source_dir = Setting.objects.get(key='SOURCE_DIR').value
    
    log.debug("select results relative to scenario %i" % scenario_id)
    results = scenario.result_set.filter(resulttype__program__in=source_programs, resulttype__color_mapping_name__isnull=False)

    log.debug("selected results for scenario: %s" % str(results))


    if tmp_dir[-1:] not in ['/', '\\']:
        tmp_dir += '/'

    rel_output_dir_name = os.path.join(scenario.get_rel_destdir())
    abs_output_dir_name = os.path.join(destination_dir, rel_output_dir_name)

    log.debug("0g: retrieve dm1maxd0 from gridmaxwaterdepth as to have a default shape.")
    def_grid = None
    def_container = 'gridmaxwaterdepth.zip'
    def_name = 'dm1maxd0.asc'
    log.debug("use %s as default grid (default shape) from %s" % (def_name, def_container))
    
    try:
        ref_result = scenario.result_set.filter(resulttype__id=1)[0].resultloc
        if os.stat(os.path.join(destination_dir, ref_result))[stat.ST_SIZE] == 0:
            log.warning("input file '%s' is empty" % ref_result)
        else:
            input_file = zipfile.ZipFile(os.path.join(destination_dir, ref_result))
            def_grid = nens.asc.AscGrid(data=input_file, name=def_name)        
    except Scenario.DoesNotExist:
        log.warning("Reference grid does not exist")

    log.debug("starting the loop on all previously computed results")
    for result in results:
        log.debug("examining results record: '%s'" % str(result))
        
        if os.stat(os.path.join(destination_dir, result.resultloc))[stat.ST_SIZE] == 0:
            log.warning("input file '%s' is empty" % result.resultloc)
            continue

        log.debug("make sure destination directory exists")
        if not os.path.isdir(os.path.join(abs_output_dir_name, result.resulttype.name)):
            os.makedirs(os.path.join(abs_output_dir_name, result.resulttype.name))

        cm_location = os.path.join(source_dir, "colormappings")

        if result.resulttype.id == 0 and scenario.project.color_mapping_name is not None:
            color_mapping_name = scenario.project.color_mapping_name
        else:
            color_mapping_name = result.resulttype.color_mapping_name
        
        log.info("copy colormappings from source '%s' into destination '%s' directory" % 
                  (cm_location, os.path.join(abs_output_dir_name, result.resulttype.name)))


       
        cm_content = file(os.path.join(cm_location, color_mapping_name)).read()

        colormapping_abs = os.path.join(abs_output_dir_name, result.resulttype.name, 'colormapping.csv')
        output = file(colormapping_abs, 'w')
        output.write(cm_content)
        output.close()

        log.debug("create new empty temporary directory")
        if not os.path.isdir(os.path.join(tmp_dir, result.resulttype.name)):
            os.makedirs(os.path.join(tmp_dir, result.resulttype.name))
        else:
            [os.unlink(os.path.join(tmp_dir, result.resulttype.name, name)) 
             for name in os.listdir(os.path.join(tmp_dir, result.resulttype.name)) 
             if os.path.isfile(os.path.join(tmp_dir, result.resulttype.name, name))]

        log.debug("unpack all files into the temporary directory from file %s."%result.resultloc)
        if result.resultloc[-3:] == 'zip':
            log.debug("open zipfile %s"%(os.path.join(destination_dir, result.resultloc)))
            input_file = zipfile.ZipFile(os.path.join(destination_dir, result.resultloc))
            for name in input_file.namelist():
                content = input_file.read(name)
                temp = file(os.path.join(tmp_dir, result.resulttype.name, name), "wb")
                temp.write(content)
                temp.close()
        else:
            log.warning("source file is not a zipfile.")
            input_file = file(os.path.join(destination_dir, result.resultloc))
            temp = file(os.path.join(tmp_dir, result.resulttype.name, 'test.asc'), "wb")
            temp.write(input_file.read())
            temp.close()
            input_file.close()
            

        # invoke part that will generate the png(s) based on the asc/inc files.
        infile_asc = compute_png_files(result, abs_output_dir_name, os.path.join(tmp_dir, result.resulttype.name + '/'),
                                       def_grid, colormapping_abs)

        log.debug("empty temporary directory")
        [os.unlink(os.path.join(tmp_dir, result.resulttype.name,  name)) 
         for name in os.listdir(os.path.join(tmp_dir,result.resulttype.name)) 
         if os.path.isfile(os.path.join(tmp_dir, result.resulttype.name, name))]
        log.debug("remove temporary directory")
        os.rmdir(os.path.join(tmp_dir, result.resulttype.name))

        result.resultpngloc =  os.path.join(rel_output_dir_name, result.resulttype.name, infile_asc + ".png")
        
        result.save()


    return True

def compute_png_files(result, abs_output_dir_name, tmp_dir, def_grid, colormapping_abs):
    """subroutine isolating the png computing logic.

    it assumes all data is in place.
    it does not remove (temporary) input data.
    it saves the files into the abs_output_dir_name

    the 'result' dictionary holds all relevant data, in particular the
    fields 're', 'basename', 'min_nr', 'max_nr'.

    returns the common part of the name of the images produced.
    """

    import re, os, nens.asc
    log.info("will produce png files out of %s, using '%s' color mapping." % (result.resulttype.content_names_re, colormapping_abs))
    log.debug("temporary directory: %s" % tmp_dir)
    candidates = os.listdir(tmp_dir)
    log.debug("content of temporary directory: %s" % candidates)

    log.debug('look for files which match "%s"'%result.resulttype.content_names_re)
    accepted_files_re = re.compile(result.resulttype.content_names_re)
        
    log.debug('files (candidates for match) are: %s'%str(candidates))
    input_files = [i for i in candidates if accepted_files_re.match(i)]
    log.debug("choose input for image production from %s." % input_files)
    
    inc_files = [i for i in input_files if i.endswith('.inc')]
    if inc_files:
        log.debug("first candidate is a .inc file.")
        input_files = inc_files[:1]
        basename = input_files[0].replace('_','')[:4]
    else:
        log.debug("no .inc files, use all .asc files.")
        input_files = [i for i in input_files if i.endswith('.asc')]
        log.debug('input files are: %s'%str(input_files))
        if len(input_files) == 1:
            basename = input_files[0][:8]
        elif len(input_files) > 1:
            basename = input_files[0][:4]
        else:
            log.warning('no files found to generate pngs')
            return None

    log.debug("sort input files alfabetically.")
    input_files.sort()
    log.info("produce images from %s." % input_files)

    log.debug("there are %s input files, basename for output files is '%s'" % (len(input_files), basename))

    log.debug("create the list of AscGrid objects.")
    only_one_grid = len(input_files) == 1 and input_files[0].endswith('.asc')
    import itertools
    grids = itertools.chain()

    for item in input_files:
        grids = itertools.chain(grids, (grid for hour, grid in nens.asc.AscGrid.xlistFromStream(tmp_dir + item, oneperhour=True, default_grid=def_grid)))

    log.debug("open the ColorMapping %s." % (colormapping_abs))
    colors = nens.asc.ColorMapping(file(colormapping_abs))

    log.debug("get the geometry properties from the first grid to build the pgw file")
    pgw_data = {}
    pgw_content_format = """\
%(cellsize_x)s
0
0
%(cellsize_y)s
%(upper_left_corner_x)s
%(upper_left_corner_y)s
"""

    if 0:
        log.debug("transform each grid to a 8 bit gif image")
        item.save("name.gif", transparency = 0)
    else:
        log.debug("saving who knows how many files as pngs")

        def save_png_and_pgw(item, full_name_no_extension):
            image = item.asImage(colors, bits=24)
            image.save(full_name_no_extension + '.png')
            pgw_data['cellsize_x'] = item.cellsize
            pgw_data['cellsize_y'] = item.cellsize
            pgw_data['upper_left_corner_x'] = item.xllcorner
            pgw_data['upper_left_corner_y'] = item.yllcorner + item.nrows * item.cellsize
            log.debug("pgw_data: %s" % pgw_data)
            pgw_file = file(full_name_no_extension + '.pgw', 'w')
            pgw_file.write(pgw_content_format % pgw_data)
            pgw_file.close()

        if only_one_grid:
            save_png_and_pgw(grids.next(), os.path.join(abs_output_dir_name, result.resulttype.name, basename))
            log.debug("saved just one file.")
        else:
            for i, item in enumerate(grids):
                save_png_and_pgw(item, os.path.join(abs_output_dir_name, result.resulttype.name, basename + '%04d' % i ))
            result.firstnr = 0
            result.lastnr = i
            log.debug("saved %d files." %  (i+1))

    return (basename + "####")[:8]

def sobek(connection, scenario_id, tmp_dir):
    return common_generation(connection, scenario_id, tmp_dir, [SOBEK_PROGRAM_ID, IMPORT_PROGRAM_ID])

def his_ssm(connection, scenario_id, tmp_dir):
    return common_generation(connection, scenario_id, tmp_dir, [HISSSM_PROGRAM_ID])

if __name__ == '__main__':
    pass
