#!/usr/bin/env python2.4
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
#* Purpose    : Calculating max waterlevel for risicokaart.nl
#* Function   : main
#* Usage      : Run from Lizard-flooding toolbox (ArcGIS): Export maximale waterstand
#*               
#* Project    : Lizard-flooding
#*  
#* $Id: max_waterstand.py 8223 2009-10-05 15:38:38Z Coen $ <Id Name Rev must be added to svn:keywords>
#*
#* initial programmer :  Coen Nengerman
#* initial date       :  20060906
#**********************************************************************
__revision__ = "$Rev: 8223 $"[6:-2]
version = "Lizard-flooding v2.0 build%s" % __revision__ 

import logging
log = logging.getLogger('nens.lizard.flooding.max_waterstand')

# Import system modules
import nens.tools as tools, nens.tools_gp as tools_gp
import sys 
import time
import os
import csv
import zipfile
import shutil
import string
import glob

import arcgisscripting
import traceback


# Create the Geoprocessor object
gp = arcgisscripting.create()

def cleanDirectory(top):
    # Delete everything reachable from the directory named in "top",
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

def checkDeleteFile(filename):
    if gp.exists(filename):
        log.debug(" - delete %s" % filename)
        if os.path.isfile(filename):
            if filename[-3:] != "log":
                os.remove(filename)
        elif os.path.isdir(filename):
            cleanDirectory(filename)    
        else:
            pass
        return 1
    else:
        return 0
        
def cleanupTempFiles(workspace):
    log.info("Deleting temp files...")
    delete_count = 0
    log.debug("workspace: %s" % workspace)
        
    list_tempfiles = os.listdir(workspace)
    for tempfile in list_tempfiles:
        log.debug("trying to delete %s" % tempfile)
        delete_count = delete_count + checkDeleteFile(workspace + "\\" + tempfile)

    log.info(str(delete_count)+" file(s) and/or folders were deleted.")
    return delete_count

def check_spatial_analyst(gp, log):
    """
    Checks if the spatial analyst extension is available. If the extension if available, it will
    be checked on. When it is not available an errormessage will be shown and the program will shut down.
    Input: the arcgis geoprocessing object and the nens.gp log object. 
    """
    if gp.CheckExtension("Spatial") == 'Available':
        log.info("Spatial Analyst is available and will be checked out")
        gp.CheckOutExtension("Spatial")
    else:
        log.error("Spatial Analyst is not available")
        sys.exit(3)

def add_to_csv(output_csv, csv_data, write_or_append):
    """
    Will create a csv file when write_or_append = 'wb'. Choose binairy! Adds a line to an existing csv file when
    write_or_append = 'ab'. 
    output_csv = "c:\\test\\output.csv" (output location of the csv file)
    csv_data = [("CODE","NAAM_GEBIED", "LOCATIE_ZIP")] (list with tuples, will be added to csv)
    """

    csv_file = open(output_csv, write_or_append)
    log.debug(" - add tuple %s to csv" % csv_data)
    writer = csv.writer(csv_file)
    writer.writerows(csv_data)
    csv_file.close()

def addFolderToZip(myZipFile, folder, input_folder):
    """
    Creates a zipfile from a folder and everything in it. 
    myZipFile is created in add_to_zip function (zipfile.ZipFile(output_zipfile, "w"))
    folder and input_folder are the same, but this function is also used recursively so it is used twice
    """
    folder = folder.encode('ascii') #convert path to ascii for ZipFile Method
    for filename in glob.glob(folder+"/*"):
            if os.path.isfile(filename):
                log.debug(" - add %s to zip" %filename)
                myZipFile.write(filename, filename.replace(input_folder+'\\', ''), zipfile.ZIP_DEFLATED)
            elif os.path.isdir(filename):
                addFolderToZip(myZipFile, filename, input_folder)

def add_to_zip(input_folder, output_location, code, name, csv_output):
    """
    adds all the files in the input_folder to a zipfile and writes it at the output_location
    """
    print "add %s to zipfile" % input_folder
    zipfilename = os.path.basename(input_folder) + ".zip"
    output_zipfile = os.path.join(output_location, zipfilename)
    myZipFile = zipfile.ZipFile(output_zipfile, "w")
    addFolderToZip(myZipFile, input_folder, input_folder)
    #close the zipfile
    myZipFile.close()
    #add output location to csv-file
    add_to_csv(csv_output, [(code, name, output_zipfile)], "ab")

def checkArcgisAllowedFilename(workspace, filename):
        """Deze functie bekijkt of een bepaalde feature al bestaat en indien ja, dan wordt de filenaam + _n (n is teller) toegevoegd.
        De input is de filenaam met extensie. 
        """
        # deze functie is gemaakt omdat arcgis soms een lock op een bestand zet waardoor de file niet gedelete kan worden of overschreven.
        # indien arcgis 9.3 gebruikt wordt is deze functie waarschijnlijk overbodig omdat je dan gebruik kan maken van testschemalock. 
        log.debug("looking for a filename allowed by arcgis")
        list_of_files = os.listdir(workspace)
        
        n = 1
        while filename + "_" + str(n) in list_of_files:
            n = int(n)+1
        filename =  filename + "_" + str(n)
        print filename
        allowed_filename = workspace + "\\" + filename
        print allowed_filename
        return allowed_filename
    
def main(options, args):
    """
    Deze tool maakt per dijkring en per provincie rasters met de maximale waterstand (gebaseerd op de output van scenario's uit Lizard-flooding.)
    Schrijf de resultaten weg als zip-files. 
    Input: 
    - CSV-file met REGIO_ID en de locatie van de zipfile met een ascii bestand van de maximale waterstand per scenario. 
    - Provinciegrenzen (Shapefile, polygons) 
    - Dijkringen (Shapefile, polygon) 
    Output: 
    - Folder met 73 zipfiles (1 van het totaal (CODE 30) 60 van de dijkringen (CODE 10) en 12 van de provincies (CODE 20)) 
    - CSV-file met CODE, NAAM GEBIED, LOCATIE ZIP-file)
    Werkwijze: 
    1. Lees csv-file als list/dictionary 
    2. Open ascii 
    3. Bereken per dijkring de maximale waterstand en schrijf deze weg als raster, ascii en stop deze in een zipfile. Schrijf de naam en locatie weg in een dictionary (wordt later een csv) 
    4. Merge alle rasters en schrijf deze weg als raster en ascii, opgeslagen in een zip. (heel nederland) 
    5. Clip op provinciegrens en schrijf 12 rasters, ascii weg en stop ze in een zip. 
    6. Schrijf een csv weg met overzicht van alle bestanden
    """
    
    # Create the Geoprocessor object
    gp = arcgisscripting.create()
    gp.RefreshCatalog
    gp.OverwriteOutput = 1

    #----------------------------------------------------------------------------------------
    #create header for logfile
    log.info("")
    log.info("*********************************************************")
    log.info("Export maximale waterstand")
    log.info("This python script is developed by "
             + "Nelen & Schuurmans B.V. and is a part of 'Lizard'")
    log.info(version)
    log.debug('loading module (%s)' % __revision__)
    log.info("*********************************************************")
    log.info("arguments: "+str(sys.argv))
    log.info("")

    #----------------------------------------------------------------------------------------
    # Check the settings for this script
    checkIni = tools.checkKeys(ini, ['test'])
    if len(checkIni) > 0:
        log.error("missing keys in lizard-settings.ini file (header max_waterstand)")
        log.error(checkIni)
        sys.exit(1)

    #----------------------------------------------------------------------------------------
    #check inputfields
    log.info("Getting commandline parameters")
    try:
        input_csv = sys.argv[1]        
        print input_csv
        input_dijkringen = sys.argv[2]
        print input_dijkringen
        input_provinciegrenzen = sys.argv[3]
        print input_provinciegrenzen
        input_cell_size = sys.argv[4]
        print input_cell_size
        input_export_number = sys.argv[5]
        print input_export_number
        time_str = time.strftime('%H%M%S')
        output_tempfiles = lizard_ini['location_temp'] + "//" + time_str
        
        os.makedirs(output_tempfiles)
    except:
        log.warning("Usage: python max_waterstand.py <input_csv> <input_dijkringen> <input provinciegrenzen>")
        input_csv = 'C:\\test\\Lizard-flooding\\testdata2.csv'
        input_dijkringen = 'C:\\test\\Lizard-flooding\\test2.shp'
        input_provinciegrenzen = 'C:\\test\\Lizard-flooding\\prov_test.shp'
        input_cell_size = "50"
        output_tempfiles = lizard_ini['location_temp']

        #sys.exit(1)    

    export_date = time.strftime('%Y%m%d%H%M%S')
    output_files = lizard_ini['location_output'] + "\\output_%s" % export_date
    
    log.info("Scenario csv-file: " + input_csv)
    log.info("Dijkringen shapefile: " + input_dijkringen)
    log.info("Provinciegrenzen shapefile: " + input_provinciegrenzen)
    #----------------------------------------------------------------------------------------
    #check input parameters
    log.info('Checking presence of input files')
##    if not(gp.exists(input_peilgebieden)):
##        log.error("inputfile peilgebieden "+input_peilgebieden+" does not exist!")
##        sys.exit(5)

    #----------------------------------------------------------------------------------------
    #check format parameters
    ## check if dijkringen and provinciegrenzen for polygons
    ## check format csv file
    log.info('input parameters checked')
    #----------------------------------------------------------------------------------------
    #cleaning temp files in workdirectory
    log.info("Cleaning temp files... ")
    cleanupTempFiles(output_tempfiles)
    log.info('tempfiles deleted... ')
    
    output_zipfiles = "%s\\zipfiles" % output_files
    if not gp.exists(output_zipfiles):
        os.makedirs(output_zipfiles)

    csv_output1 = output_zipfiles + "\\output_" + input_export_number + ".csv"    
    add_to_csv(csv_output1, [("CODE","NAAM_GEBIED", "LOCATIE_ZIP")], "wb")    
    
    



    #----------------------------------------------------------------------------------------
    # A) Create tempfiles
    print "A) creating tempfiles... "  
    #area_id = "dijkringnr"
    area_id = ini['dijkring_nr'].lower()
    dijkringen_gegevens = nens.gp.get_table(gp,input_dijkringen, primary_key=area_id)
    dijkringnr_list = []
    
    for key, value in dijkringen_gegevens.items():
        # make output folder for dijkring
        os.makedirs("%s\\dijkring_%s" %(output_files, key))
        
        dijkringnr_list.append(key)
        where_clause = '"%s" = \'%s\'' % (area_id.upper(), key)
        output_dijkring = "%s\\dijkring_%s.shp" %(output_tempfiles, key.replace("-", "_"))
        print " - export dijkring %s" %key.lower()
        gp.Select_analysis(input_dijkringen, output_dijkring.lower(), where_clause)
        #raster_dijkring = "%s\\dr_%s" %(output_tempfiles, key.replace("-", "_"))
        raster_dijkring = "%s\\dr_%s" %(output_tempfiles, key.replace("-", "_"))
        print raster_dijkring

        gp.FeatureToRaster_conversion(output_dijkring.lower(), area_id, raster_dijkring , input_cell_size)

    #provincie_id = "provc_nm"
    provincie_id = ini['provincie_naam'].lower()
    provinciegrenzen_gegevens = nens.gp.get_table(gp,input_provinciegrenzen, primary_key=provincie_id)
    provinciegrenzen_list = []
    
    for key, value in provinciegrenzen_gegevens.items():
        # make output folder for provincie
        os.makedirs("%s\\provincie_%s" %(output_files, key))

        provinciegrenzen_list.append(key)
        where_clause = '"%s" = \'%s\'' % (provincie_id.upper(), key)
        output_provincie = "%s\\provincie_%s.shp" %(output_tempfiles, key.replace("-", "_"))
        print " - export provincie %s" %key.lower()
        gp.Select_analysis(input_provinciegrenzen, output_provincie.lower(), where_clause)
        raster_provincie = "%s\\pr_%s" %(output_tempfiles, key.replace("-", "_")[:8])
        gp.FeatureToRaster_conversion(output_provincie.lower(), provincie_id, raster_provincie , input_cell_size)
        
    #----------------------------------------------------------------------------------------
    counter = 1
    regio_list = []
    
    input =  [d for d in csv.DictReader(open(input_csv))]
    
    for row in input:
        regio_id = row['dijkring']
        if regio_id not in regio_list:
            regio_list.append(regio_id)

    max_raster_list = []
    max_dijkringen_list = []

    #check out spatial analyst (if available)
    check_spatial_analyst(gp, log)

    progress = 1
    for dijkring in regio_list:
        if dijkring in dijkringnr_list:
            print "... processing regio: %s (progress: nr. %s of %s)" %(dijkring, progress, len(regio_list))
            raster_list = []
            for row in input:
                if row['dijkring'] == dijkring:
                    bestandslocatie = row['bestandslocatie']
                    bestandslocatie_split = bestandslocatie.split('\\')
                    log.debug(" - copy file from %s" % bestandslocatie)
                    output_zipfile = '%s\\_%s_%s_%s_%s' %(output_tempfiles,
                                                        bestandslocatie_split[4],
                                                        bestandslocatie_split[5],
                                                        bestandslocatie_split[6],
                                                        bestandslocatie_split[7])
                    print bestandslocatie
                    log.debug(' - copy file to %s' %output_zipfile)
                    shutil.copyfile(bestandslocatie, output_zipfile)

                    output_ascii_name = '%s_%s_%s_%s.asc' %(bestandslocatie_split[4],
                                                            bestandslocatie_split[5],
                                                            bestandslocatie_split[6],
                                                            bestandslocatie_split[7][:-4])

                    # open zipfile and write ascii to tempdir        
                    zip_file = zipfile.ZipFile(output_zipfile)
                    obj = zip_file.filelist[0].filename
                    newfile= open(os.path.join(output_tempfiles, obj), 'wb')
                    log.debug(' - %s' %output_ascii_name)
                    newfile.write(zip_file.read(obj))
                    newfile.close()
                    os.rename(os.path.join(output_tempfiles, obj), os.path.join(output_tempfiles, output_ascii_name))

                    gp.ASCIIToRaster_conversion (os.path.join(output_tempfiles, output_ascii_name), '%s\\ras_%s_%s' % (output_tempfiles, dijkring, counter), "FLOAT")
                    raster_list.append('%s\\ras_%s_%s' % (output_tempfiles, dijkring, counter))
                    counter += 1
                    
            input_raster_str = string.join(raster_list, ' ; ' )
            out_raster = '%s\\max_dr_%s' % (output_tempfiles, dijkring)
            max_raster_list.append(out_raster)
            gp.CellStatistics_sa(input_raster_str, out_raster, ini['raster_statistics'].upper())
            output_max_dijkring = "%s\\dijkring_%s\\out_%s" %(output_files, dijkring, dijkring)
            gp.Con_sa("%s\\dr_%s" %(output_tempfiles, dijkring), out_raster, output_max_dijkring, "#", "VALUE = 1")
            max_dijkringen_list.append("%s\\dijkring_%s\\out_%s" %(output_files, dijkring, dijkring))

            # convert to ascii
            out_ascii_file = output_max_dijkring + ".asc"
            #max_ascii_list.append(out_ascii_file)
            gp.RasterToASCII_conversion(out_raster, out_ascii_file)

            dijkring_zipfile = "%s\\dijkring_%s" %(output_files, dijkring)
            add_to_zip(dijkring_zipfile, output_zipfiles, "10", "Dijkring %s" % dijkring, csv_output1)
            progress += 1
        else:
            print "regio %s is not available in dijkringen shapefile" % dijkring
            progress += 1
            
    # merge alle rasters uit max_raster_list
    output_total = output_files + "\\totaal"
    os.makedirs(output_total)
    
    input_max_dijkringen_str = string.join(max_dijkringen_list, ' ; ' )
    print input_max_dijkringen_str
    gp.MosaicToNewRaster_management(input_max_dijkringen_str, output_total, "out_nl", "#", "32_BIT_FLOAT", input_cell_size)
    gp.RasterToASCII_conversion("%s\\out_nl" % output_total, "%s\\out_nl.asc" % output_total)
    add_to_zip(output_total, output_zipfiles, "30", "Totaal", csv_output1)
    
    # clip het merge_raster op provinciegrens en sla voor iedere provincie het raster op
    for provincie in provinciegrenzen_list:
        print " - clip waterstanden for %s" % provincie
        try:
            input_raster_provincie = output_tempfiles + "\\pr_" + provincie.replace("-", "_")[:8]
            provincie_afkorting = provincie.replace("-", "_")[:8]
            output_provincie = "%s\\provincie_%s\\out_%s" %(output_files, provincie.lower(), provincie_afkorting.lower())
            extent_provincie = "%s\\pr_%s" % (output_tempfiles, provincie_afkorting.lower())
            gp.Con_sa(input_raster_provincie, extent_provincie, output_provincie, "#", "VALUE = 1")
            # converteer deze rasters naar ascii. 
            gp.RasterToASCII_conversion(output_provincie, output_provincie + ".asc")
            add_to_zip("%s\\provincie_%s" % (output_files, provincie), output_zipfiles, "20", "Provincie %s" % provincie, csv_output1)
        except:
            print "no raster available for this area"
            print traceback.format_exc()

    #Copy output file also to the new_outputs folder
    shutil.copyfile(csv_output1, lizard_ini['location_output'] + "\\new_outputs\\output_" + input_export_number + "_%s.csv" % export_date)
    #----------------------------------------------------------------------------------------
    log.info("Cleaning temp files...")
    try:
        cleanupTempFiles(output_tempfiles)
    except:
        log.info(traceback.format_exc())
        
    log.debug("Deleting geoprocessing object...")
    if gp:
        del gp

    log.info("Finished")
    pass

        
if __name__ == '__main__':
    script_name = "max_waterstand" #settings header
    file_script = sys.argv[0] #get absolute path of running script
    location_script = os.path.abspath(os.path.dirname(file_script))+"\\"
    
    #settings for all turtle tools
    lizard_settings_all = tools.readIniHeaders(location_script+os.sep+"lizard-settings.ini")
    lizard_ini = lizard_settings_all["GENERAL"]
    ini = lizard_settings_all['max_waterstand']

    #checkIni = tools.missingKeys(lizard_ini, ['location_temp'])
    #if len(checkIni) > 0:
    #    print "missing keys in lizard-settings.ini file (header General)"
    #    print checkIni
    #    sys.exit(1)
    
    #check temporary folder (workspace)
    if not gp.exists(lizard_ini['location_temp']):
        os.makedirs(lizard_ini['location_temp']) #does nothing if it already exists
    
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename=os.path.join(lizard_ini['location_temp'], lizard_ini['filename_log']),
                        filemode='a')
        
    import nens.gp
    #hdlr = nens.gp.GpHandler(logging.INFO, gp, format='%(message)s')
    #logging.getLogger('nens.lizard').addHandler(hdlr)
  
    from optparse import OptionParser
    parser = OptionParser()

    (options, args) = parser.parse_args()
    main(options, args)
    