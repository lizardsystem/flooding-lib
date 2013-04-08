# Run under linux
# Task 200 (sorry that I didn't put that in the filename)

from __future__ import unicode_literals
from __future__ import print_function

import tempfile
import os
import simplejson as json
from StringIO import StringIO

from flooding_lib.models import ResultType
from flooding_lib.tools.exporttool.models import ExportRun
from flooding_lib.tools.exporttool.models import Setting
from flooding_lib.tools.exporttool.models import Result
from flooding_lib.util import files

import numpy as np
import zipfile
import shutil

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

import logging
log = logging.getLogger(__name__)


def mktemp():
    """Make a temp file

    You are responsible for deleting it.
    """
    f = tempfile.NamedTemporaryFile(delete=False, prefix='task_200_')
    pathname = f.name
    f.close()
    return pathname


def linuxify_pathname(pathname):
    """
    Based on Remco's experience on this problem, we'll just replace
    all '\\' with '/' and symlink the correct paths to the mounts.

    input: \\\\p-flod-fs-00-d1.external-nens.local\\flod-share\\Flooding\\resultaten-staging/Dijkring 44 - Kromme Rijn\\3649\\gridmaxwaterdepth.zip
    output: /mnt/p-flod-fs-00-d1/Flooding/resultaten-staging/Dijkring 44 - Kromme Rijn/3649/gridmaxwaterdepth.zip
    """
    #return '/mnt/p-flod-fs-00-d1/Flooding/resultaten-staging/Dijkring 31 - Zuid-Beveland - oost/13072/gridmaxwaterdepth.zip'
    #return '/mnt/p-flod-fs-00-d1/Flooding/resultaten-staging/Dijkring 31 - Zuid-Beveland - oost/13072/gridmaxwaterlevel.zip'
    return pathname.replace('\\', '/')


def is_valid_zipfile(linux_filename):
    """Check if the passed file is a valid zipfile."""
    if not os.path.isfile(linux_filename):
        return False
    try:
        zipf = zipfile.ZipFile(open(linux_filename, 'rb'))
        test = zipf.testzip()
        if test is not None:
            log.warn("Corrupted zipfile {0}".format(linux_filename))
            return False
    except:
        log.error("File is not valid: {0}".format(linux_filename))
        return False

    return True


def add_zero_before_number(number):
    """Add 0 before a number less then 10,
    format it to string."""
    if number < 10: number = "{0}{1}".format(0, number)
    return number


def generate_dst_filename(export_run):
    """Create filename like
    [export name]_ddmmyyyy_hhMM.zip.

    Replace all ' ' with '_' in export name
    Cat export name to 20 chars."""
    max_length = 20
    export_name = ""
    if export_run.name is not None:
        export_name = export_run.name[:max_length]
        export_name = export_name.strip()
        export_name = export_name.replace(' ', '_')

    c_date = export_run.creation_date

    day = add_zero_before_number(c_date.day)
    month = add_zero_before_number(c_date.month)
    hour = add_zero_before_number(c_date.hour)
    minute = add_zero_before_number(c_date.minute)
        
    dst_basename = "{0}_{1}{2}{3}_{4}{5}.zip".format(
        export_name, day, month, c_date.year, hour, minute)

    return dst_basename
    


def generate_export_meta(export_run, dst_filename):
    """Generate a dict with meta data for 
    passed export."""
    scenarios = export_run.scenarios.all()
    export_meta = {
        "name": export_run.name,
        "owner": export_run.owner.username,
        "creationdate": export_run.creation_date.isoformat(),
        "description": export_run.description,
        "selectedmaps": export_run.selected_maps,
        "scenarios": export_run.meta_scenarios,
        "filelocation": dst_filename}
    return export_meta
        

def create_json_meta_file(tmp_zip_filename, export_run, dst_filename):
    """Create meta file."""
    # export_meta = {
    #     "export_name": export_run.name,
    #     "owner": export_run.owner.username}
    export_meta = generate_export_meta(export_run, dst_filename)
    io = StringIO()
    json.dump(export_meta, io, indent=4)
    meta_filename = mktemp()
    meta_file = open(meta_filename, 'wb')
    meta_file.write(io.getvalue())
    meta_file.close()
    add_to_zip(tmp_zip_filename, 
               [{'filename': meta_filename, 'arcname': "meta.json", 'delete_after': True}])
    if not io.closed:
        io.close()
    
    
def np_max(list_of_arrays):
    """
    Max of a list of arrays
    """
    if len(list_of_arrays) == 1:
        return list_of_arrays[0]
    else:
        return np.maximum(list_of_arrays[0], np_max(list_of_arrays[1:]))


def write_masked_array_as_ascii(filename, masked_array, geo_transform):
    """
    Use gdal to write a masked_array to a ascii file.
    """
    NO_DATA_VALUE = -999
    masked_array.fill_value = NO_DATA_VALUE
    filled = masked_array.filled()
    size_y, size_x = filled.shape
    num_bands = 1
    ds = gdal.GetDriverByName(b'mem').Create(
        filename, size_x, size_y, num_bands, gdal.gdalconst.GDT_Float64)
    band = ds.GetRasterBand(1)
    band.WriteArray(filled)
    band.SetNoDataValue(NO_DATA_VALUE)
    #Xp = padfTransform[0] + P*padfTransform[1] + L*padfTransform[2];
    #Yp = padfTransform[3] + P*padfTransform[4] + L*padfTransform[5];
    #[1] is pixel width, [5] is pixel height, upper left is [0], [3]
    ds.SetGeoTransform(geo_transform)

    # Now it gets written to the disk
    gdal.GetDriverByName(b'aaigrid').CreateCopy(filename, ds)
    #print 'output file %s written' % filename


def add_to_zip(output_zipfile, zip_result):
    """
    Zip all files listed in zip_result

    zip_result is a list with keys:
    - filename: filename on disc
    - arcname: target filename in archive
    - delete_after: set this to remove file from file system after zipping
    """
    #print 'zipping result into %s' % output_zipfile
    with zipfile.ZipFile(output_zipfile, 'a', zipfile.ZIP_DEFLATED) as myzip:
        for file_in_zip in zip_result:
            #print 'zipping %s...' % file_in_zip['arcname']
            myzip.write(file_in_zip['filename'], file_in_zip['arcname'])
            if file_in_zip.get('delete_after', False):
                #print 'removing %r (%s in arc)' % (file_in_zip['filename'], file_in_zip['arcname'])
                os.remove(file_in_zip['filename'])


def get_dijkring_mask(dijkringnr, geo_projection, geo_transform, size_x, size_y):
        """
        Use a shapefile to create a dataset with the shape as
        mask. Borrowed from get_mask in lizard_damage.raster.
        """
        # geo_projection = ds.GetProjection()
        # geo_transform = ds.GetGeoTransform()

        # Get the driver
        driver = ogr.GetDriverByName(b'ESRI Shapefile')
        # Open a shapefile
        #DIJKRING_SHAPES_FOLDER = '/home/jack/git/sites/flooding/dijkringen_todo_move_somewhere'
        dijkring_shapes_folder = '/srv/test.flooding.lizard.net/dijkringen'  # Default
        try:
            dijkring_shapes_folder = Setting.objects.get(key='DIJKRING_SHAPES_FOLDER').value
        except:
            log.warn('Check Exporttool.Setting DIJKRING_SHAPES_FOLDER, taking %s' % dijkring_shapes_folder)

        shapefile_name = os.path.join(dijkring_shapes_folder, 'dr__%d.shp' % dijkringnr)
        log.debug('Reading shapefile %s...' % (shapefile_name))
        dataset = driver.Open(shapefile_name, 0)

        dijkring_layer = dataset.GetLayer()
        # # The dijkring shapefile always contains only 1 feature.
        # for index in xrange(layer.GetFeatureCount()):
        #     feature = layer.GetFeature(index)
        #     dijkring_wkb = feature.GetGeometryRef().ExportToWkb()
        #     break

        sr = osr.SpatialReference()
        sr.ImportFromWkt(geo_projection)

        # # Prepare in-memory ogr layer
        # ds_ogr = ogr.GetDriverByName(b'Memory').CreateDataSource('')
        # layer = ds_ogr.CreateLayer(b'', sr)
        # layerdefinition = layer.GetLayerDefn()
        # feature = ogr.Feature(layerdefinition)
        # feature.SetGeometry(ogr.CreateGeometryFromWkb(str(dijkring_wkb)))
        # layer.CreateFeature(feature)

        # Prepare in-memory copy of ds_gdal
        ds_result = gdal.GetDriverByName(b'mem').Create(
            '', size_x, size_y, 1, gdal.gdalconst.GDT_Byte,
        )
        ds_result.SetProjection(geo_projection)
        ds_result.SetGeoTransform(geo_transform)
        band = ds_result.GetRasterBand(1)
        band.WriteArray(np.ones((size_y, size_x)))  # Fill with ones

        # Rasterize and return
        gdal.RasterizeLayer(ds_result, (1,), dijkring_layer, burn_values=(0,))  # Burn with 0's
        return ds_result.GetRasterBand(1).ReadAsArray()


def dijkring_arrays_to_zip(input_files, tmp_zip_filename, gridtype='output', gridsize=50):
    """
    Return arrays in a dict with key 'dijkringnr'.
    Value is a list of 2-tuples (masked_array, geo_transform)

    Input_files is a list with dicts 'dijkringnr' and 'filename'

    gridtype is used to generate useful arcnames
    """
    dijkring_arrays = {}  # key is dijkringnr
    result = {}

    x_min = None
    x_max = None
    y_max = None
    y_min = None

    for input_file in input_files:
        log.debug('  - checking bbox of %s...' % input_file['scenario'])
        #print input_file
        linux_filename = linuxify_pathname(input_file['filename'])
        dijkringnr = input_file['dijkringnr']
        log.debug("Input_filename {0}".format(input_file['filename']))
        log.debug("Linux-filename {0}".format(linux_filename))
        
        if not is_valid_zipfile(linux_filename):
            continue

        with files.temporarily_unzipped(linux_filename) as files_in_zip:
            for filename_in_zip in files_in_zip:
                log.debug(filename_in_zip)
                dataset = gdal.Open(str(filename_in_zip))
                dataset.RasterXSize, dataset.RasterYSize
                geo_transform = dataset.GetGeoTransform()
                # something like (183050.0, 25.0, 0.0, 521505.0, 0.0, -25.0)
                this_x_min, this_y_max = geo_transform[0], geo_transform[3]
                this_x_max = this_x_min + dataset.RasterXSize * geo_transform[1]
                this_y_min = this_y_max + dataset.RasterYSize * geo_transform[5]

                if x_min is None or this_x_min < x_min:
                    x_min = this_x_min
                if x_max is None or this_x_max > x_max:
                    x_max = this_x_max
                if y_min is None or this_y_min < y_min:
                    y_min = this_y_min
                if y_max is None or this_y_max > y_max:
                    y_max = this_y_max
                del dataset
   
    size_x = int(abs((x_max - x_min) / gridsize))
    size_y = int(abs((y_max - y_min) / gridsize))
    log.debug('resulting image: %f %f %f %f size: %f %f' % (
        x_min, y_min, x_max, y_max, size_x, size_y))

    len_input_files = len(input_files)
    for index, input_file in enumerate(input_files):
        log.debug(
            '  - processing result (%d/%d) for scenario %s...' % (index+1, len_input_files, input_file['scenario']))
        #print input_file
        linux_filename = linuxify_pathname(input_file['filename'])
        if not is_valid_zipfile(linux_filename):
            continue
        log.debug("Linuxified filepath: {0}".format(linux_filename))
        dijkringnr = input_file['dijkringnr']
        with files.temporarily_unzipped(linux_filename) as files_in_zip:
            for filename_in_zip in files_in_zip:
                #print filename_in_zip
                #import pdb; pdb.set_trace()
                dataset = gdal.Open(str(filename_in_zip))
                #reprojected_dataset = dataset
                driver = gdal.GetDriverByName(b'mem')
                reprojected_dataset = driver.Create('dummyname', size_x, size_y, 1, gdal.gdalconst.GDT_Float64)
                #reprojected_dataset = gdal.GetDriverByName('mem').Create(
                #    'dummyname', size_x, size_y, 1, gdal.gdalconst.GDT_Float64)
                reprojected_dataset.SetGeoTransform((x_min, gridsize, 0, y_max, 0, -gridsize))

                band = reprojected_dataset.GetRasterBand(1)
                #print dir(band)
                NO_DATA_VALUE = -999
                band.SetNoDataValue(NO_DATA_VALUE)
                band.Fill(NO_DATA_VALUE)
                gdal.ReprojectImage(dataset, reprojected_dataset)

                # testing
                #gdal.GetDriverByName('aaigrid').CreateCopy('test.asc', reprojected_dataset)

                # (183050.0, 25.0, 0.0, 521505.0, 0.0, -25.0) 
                #print dataset.GetGeoTransform(), dataset.GetProjection()
                # Read the data into a masked array
                arr = reprojected_dataset.ReadAsArray()
                ndv = reprojected_dataset.GetRasterBand(1).GetNoDataValue()
                # Commented this out, because everything was masked away in the test case.
                #masked_array = np.ma.array(arr, mask=(arr == ndv))

                masked_array = np.ma.array(arr)
                #print masked_array.max()
                geo_transform = reprojected_dataset.GetGeoTransform()
                geo_projection = reprojected_dataset.GetProjection()  # why empty? does it matter?
                if dijkringnr not in dijkring_arrays:
                    dijkring_arrays[dijkringnr] = (masked_array, geo_transform, geo_projection)
                else:
                    old_max = dijkring_arrays[dijkringnr][0]
                    dijkring_arrays[dijkringnr] = (np.maximum(masked_array, old_max), geo_transform, geo_projection)
                    #.append((masked_array, geo_transform, geo_projection))
                #print masked_array.max()
                del dataset  # This closes the file, so that the
                             # directory can be deleted in Windows

    #print dijkring_arrays[9][0][0].max(), dijkring_arrays[9][1][0].max()
    #print np.maximum(dijkring_arrays[9][0][0], dijkring_arrays[9][1][0]).max()

    for dijkringnr, array in dijkring_arrays.items():
        # for each dijkringnr, calculate max(arrays)
        #print 'dijkringnr %d' % dijkringnr
        # 0 is masked_array, 1 is geo_transform
        #max_array = np_max([array[0] for array in arrays])
        max_array = array[0]
        geo_transform = array[1]
        geo_projection = array[2]

        # Commented this out, because everything was masked away in the test case.
        # # Apply dijkring mask
        # mask = get_dijkring_mask(
        #     dijkringnr, geo_projection, geo_transform,
        #     max_array.shape[1], max_array.shape[0])
        # # Everything is masked: a) if it was masked already OR b) it's in the dijkring_mask
        # max_array.mask = np.maximum(mask, max_array.mask)

        result[dijkringnr] = (max_array, geo_transform)

        ascii_filename = mktemp()
        write_masked_array_as_ascii(ascii_filename, max_array, geo_transform)
	if dijkringnr is None:
            dijkringnr = 0
        arc_name = '%s_%d.asc' % (gridtype, dijkringnr)
        add_to_zip(tmp_zip_filename,
                   [{'filename': ascii_filename, 'arcname': arc_name, 'delete_after': True}])

    return result


def calc_max_waterdepths(tmp_zip_filename, export_run):
    log.debug('export_max_waterdepth')
    gridtype = 'gridmaxwaterdepth'
    # Calc max waterdepth
    export_result_type = ResultType.objects.get(name=gridtype).id
    # Find out input files for this type
    input_files = export_run.input_files(export_result_type)
    if len(input_files) <= 0:
        log.warn("No file to calc max watedepths.")
        return {}
    max_waterdepths = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, gridtype,
        gridsize=export_run.gridsize)
    return max_waterdepths


def calc_max_flowvelocity(tmp_zip_filename, export_run):
    # Calc max flow velocity
    log.debug('export_max_flowvelocity')
    gridtype = 'gridmaxflowvelocity'
    export_result_type = ResultType.objects.get(name=gridtype).id
    # Find out input files for this type
    input_files = export_run.input_files(export_result_type)
    if len(input_files) <= 0:
        log.warn("No file to calc max flowvelocity.")
        return {}
    max_flowvelocities = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, gridtype,
        gridsize=export_run.gridsize)
    return max_flowvelocities


def calc_possible_flooded_area(tmp_zip_filename, max_waterdepths):
    # Calculate the possible flooded area
    log.debug('export_possibly_flooded')
    for dijkringnr, array in max_waterdepths.items():
        flooded_array = np.ma.where(array[0] < 0.02, 0, 1)
        #possibly_flooded[dijkringnr] = flooded_array
        ascii_filename = mktemp()
        if dijkringnr is None:
            dijkringnr = 0
        arc_name = 'possibly_flooded_%d.asc' % (dijkringnr)
        geo_transform = array[1]
        write_masked_array_as_ascii(
            ascii_filename, flooded_array, geo_transform)
        add_to_zip(
            tmp_zip_filename,
            [{'filename': ascii_filename,
              'arcname': arc_name,
              'delete_after': True}])


def calculate_export_maps(exportrun_id):
    """
    Execute an ExportRun that creates different maps.

    The function makes temp result files in the temp directory. Output
    is a zip file (in Settings -> EXPORT_FOLDER) containing these
    files and a Result object associated to it. Old Result objects are
    deleted (and associated files are not deleted).

    Note: only the basename is saved. You have to calculate the full
    path yourself by prepending the name with Setting.EXPORT_FOLDER.
    """
    export_run = ExportRun.objects.get(id=exportrun_id)
    export_folder = Setting.objects.get(key='EXPORT_FOLDER').value
    result_files = []
    max_waterdepths = {}

    tmp_zip_filename = mktemp()
    
    if export_run.export_max_waterdepth or export_run.export_possibly_flooded:
        max_waterdepths = calc_max_waterdepths(
            tmp_zip_filename, export_run)

    if export_run.export_max_flowvelocity:
        max_flowvelocities = calc_max_flowvelocity(
            tmp_zip_filename, export_run)

    if export_run.export_possibly_flooded:
        # Calculate the possible flooded area
        log.debug('export_possibly_flooded')
        calc_possible_flooded_area(tmp_zip_filename,
                                   max_waterdepths)

    dst_basename = generate_dst_filename(export_run)
    dst_filename = os.path.join(export_folder, dst_basename)

    log.debug("create meta")
    create_json_meta_file(tmp_zip_filename, export_run, dst_filename)

    log.debug('Moving file from %s to %s...' % (tmp_zip_filename, dst_filename))
    shutil.move(tmp_zip_filename, dst_filename)

    result_count = Result.objects.filter(export_run=export_run).count()
    if result_count > 0:
        log.warn('Warning: deleting old Result objects for this export run...')
        Result.objects.filter(export_run=export_run).delete()

    log.debug('Making Result object with link to file...')
    result = Result(
        name=export_run.name,
        file_basename=dst_basename,
        area=Result.RESULT_AREA_DIKED_AREA, export_run=export_run)
    result.save()

    log.debug('Updating state of export_run...')
    export_run.state = ExportRun.EXPORT_STATE_DONE
    export_run.save()

    log.debug('Finished.')
