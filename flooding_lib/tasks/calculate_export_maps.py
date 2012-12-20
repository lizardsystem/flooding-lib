# Run under linux
# Task 200 (sorry that I didn't put that in the filename)

import tempfile
import os

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
    ds = gdal.GetDriverByName('mem').Create(
        filename, size_x, size_y, num_bands, gdal.gdalconst.GDT_Float64)
    band = ds.GetRasterBand(1)
    band.WriteArray(filled)
    band.SetNoDataValue(NO_DATA_VALUE)
    #Xp = padfTransform[0] + P*padfTransform[1] + L*padfTransform[2];
    #Yp = padfTransform[3] + P*padfTransform[4] + L*padfTransform[5];
    #[1] is pixel width, [5] is pixel height, upper left is [0], [3]
    ds.SetGeoTransform(geo_transform)

    # Now it gets written to the disk
    gdal.GetDriverByName('aaigrid').CreateCopy(filename, ds)
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
        driver = ogr.GetDriverByName('ESRI Shapefile')
        # Open a shapefile
        #DIJKRING_SHAPES_FOLDER = '/home/jack/git/sites/flooding/dijkringen_todo_move_somewhere'
        dijkring_shapes_folder = '/srv/test.flooding.lizard.net/dijkringen'  # Default
        try:
            dijkring_shapes_folder = Setting.objects.get(key='DIJKRING_SHAPES_FOLDER').value
        except:
            print 'Check Exporttool.Setting DIJKRING_SHAPES_FOLDER, taking %s' % dijkring_shapes_folder

        shapefile_name = os.path.join(dijkring_shapes_folder, 'dr__%d.shp' % dijkringnr)
        print 'Reading shapefile %s...' % (shapefile_name)
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
        print '  - checking bbox of %s...' % input_file['scenario']
        #print input_file
        linux_filename = linuxify_pathname(input_file['filename'])
        dijkringnr = input_file['dijkringnr']
        with files.temporarily_unzipped(linux_filename) as files_in_zip:
            for filename_in_zip in files_in_zip:
                print filename_in_zip
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
    print 'resulting image: %f %f %f %f size: %f %f' % (
        x_min, y_min, x_max, y_max, size_x, size_y)

    for input_file in input_files:
        print '  - processing result for scenario %s...' % input_file['scenario']
        #print input_file
        linux_filename = linuxify_pathname(input_file['filename'])
        print linux_filename
        dijkringnr = input_file['dijkringnr']
        with files.temporarily_unzipped(linux_filename) as files_in_zip:
            for filename_in_zip in files_in_zip:
                #print filename_in_zip
                dataset = gdal.Open(str(filename_in_zip))
                #reprojected_dataset = dataset
                reprojected_dataset = gdal.GetDriverByName('mem').Create(
                    'dummyname', size_x, size_y, 1, gdal.gdalconst.GDT_Float64)
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
                if dijkringnr not in dijkring_arrays:
                    dijkring_arrays[dijkringnr] = []
                #print masked_array.max()
                geo_transform = reprojected_dataset.GetGeoTransform()
                geo_projection = reprojected_dataset.GetProjection()  # why empty? does it matter?
                dijkring_arrays[dijkringnr].append((masked_array, geo_transform, geo_projection))
                #print masked_array.max()
                del dataset  # This closes the file, so that the
                             # directory can be deleted in Windows

    #print dijkring_arrays[9][0][0].max(), dijkring_arrays[9][1][0].max()
    #print np.maximum(dijkring_arrays[9][0][0], dijkring_arrays[9][1][0]).max()

    for dijkringnr, arrays in dijkring_arrays.items():
        # for each dijkringnr, calculate max(arrays)
        #print 'dijkringnr %d' % dijkringnr
        # 0 is masked_array, 1 is geo_transform
        max_array = np_max([array[0] for array in arrays])
        geo_transform = arrays[0][1]
        geo_projection = arrays[0][2]

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

    tmp_zip_filename = mktemp()

    if export_run.export_max_waterdepth or export_run.export_possibly_flooded:
        print 'export_max_waterdepth'
        gridtype = 'gridmaxwaterdepth'
        # Calc max waterdepth
        export_result_type = ResultType.objects.get(name=gridtype).id
        # Find out input files for this type
        input_files = export_run.input_files(export_result_type)
        max_waterdepths = dijkring_arrays_to_zip(
            input_files, tmp_zip_filename, gridtype,
            gridsize=export_run.gridsize)

    if export_run.export_max_flowvelocity:
        # Calc max flow velocity
        print 'export_max_flowvelocity'
        gridtype = 'gridmaxflowvelocity'
        # Calc max waterdepth
        export_result_type = ResultType.objects.get(name=gridtype).id
        # Find out input files for this type
        input_files = export_run.input_files(export_result_type)
        max_flowvelocities = dijkring_arrays_to_zip(
            input_files, tmp_zip_filename, gridtype,
            gridsize=export_run.gridsize)

    if export_run.export_possibly_flooded:
        # Calculate the possible flooded area
        print 'export_possibly_flooded'
        #possibly_flooded = {}
        for dijkringnr, array in max_waterdepths.items():
            flooded_array = np.ma.where(array[0] < 0.02, 0, 1)
            #possibly_flooded[dijkringnr] = flooded_array
            ascii_filename = mktemp()
            if dijkringnr is None:
                dijkringnr = 0
            arc_name = 'possibly_flooded_%d.asc' % (dijkringnr)
            geo_transform = array[1]
            write_masked_array_as_ascii(ascii_filename, flooded_array, geo_transform)
            add_to_zip(
                tmp_zip_filename,
                [{'filename': ascii_filename, 'arcname': arc_name, 'delete_after': True}])

    # Move file to destination.
    print tmp_zip_filename

    dst_basename = 'export_run_%d.zip' % export_run.id
    dst_filename = os.path.join(export_folder, dst_basename)

    print 'Moving file from %s to %s...' % (tmp_zip_filename, dst_filename)
    shutil.move(tmp_zip_filename, dst_filename)

    result_count = Result.objects.filter(export_run=export_run).count()
    if result_count > 0:
        print 'Warning: deleting old Result objects for this export run...'
        Result.objects.filter(export_run=export_run).delete()

    print 'Making Result object with link to file...'
    result = Result(
        name=export_run.name,
        file_basename=dst_basename,
        area=Result.RESULT_AREA_DIKED_AREA, export_run=export_run)
    result.save()

    print 'Updating state of export_run...'
    export_run.state = ExportRun.EXPORT_STATE_DONE
    export_run.save()

    print 'Finished.'
