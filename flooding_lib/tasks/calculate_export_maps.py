# Run under linux
# Task 200 (sorry that I didn't put that in the filename)

from __future__ import unicode_literals
from __future__ import print_function

import tempfile
import os
from django.utils import simplejson as json
from StringIO import StringIO

from datetime import datetime

from flooding_lib.models import ResultType
from flooding_lib.tools.exporttool.models import ExportRun
from flooding_lib.tools.exporttool.models import Setting
from flooding_lib.tools.exporttool.models import Result
from flooding_lib.util import files

import numpy as np
import zipfile
import shutil

from osgeo import gdal

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
    if number < 10:
        number = "{0}{1}".format(0, number)
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
    export_meta = {
        "name": export_run.name,
        "owner": export_run.owner.username,
        "creationdate": export_run.creation_date.isoformat(),
        "description": export_run.description,
        "selectedmaps": export_run.selected_maps,
        "scenarios": export_run.meta_scenarios,
        "filelocation": dst_filename,
        "gridsize": export_run.gridsize}
    return export_meta


def create_json_meta_file(tmp_zip_filename, export_run, dst_filename):
    """Create meta file."""
    export_meta = generate_export_meta(export_run, dst_filename)
    io = StringIO()
    json.dump(export_meta, io, indent=4)
    meta_filename = mktemp()
    meta_file = open(meta_filename, 'wb')
    meta_file.write(io.getvalue())
    meta_file.close()
    add_to_zip(tmp_zip_filename,
               [{'filename': meta_filename,
                 'arcname': "meta.json",
                 'delete_after': True}])
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
    NO_DATA_VALUE = -9999
    masked_array.fill_value = NO_DATA_VALUE
    filled = masked_array.filled()
    size_y, size_x = filled.shape
    num_bands = 1
    driver = gdal.GetDriverByName(b'gtiff')
    ds = driver.Create(b'{0}'.format(filename), size_x, size_y, num_bands,
                       gdal.gdalconst.GDT_Byte)
    band = ds.GetRasterBand(1)
    band.WriteArray(filled)
    band.SetNoDataValue(NO_DATA_VALUE)
    #Xp = padfTransform[0] + P*padfTransform[1] + L*padfTransform[2];
    #Yp = padfTransform[3] + P*padfTransform[4] + L*padfTransform[5];
    #[1] is pixel width, [5] is pixel height, upper left is [0], [3]
    ds.SetGeoTransform(geo_transform)

    # Now it gets written to the disk
    gdal.GetDriverByName(b'aaigrid').CreateCopy(b'{0}'.format(filename), ds)
    ds = None
    del ds


def add_to_zip(output_zipfile, zip_result):
    """
    Zip all files listed in zip_result

    zip_result is a list with keys:
    - filename: filename on disc
    - arcname: target filename in archive
    - delete_after: set this to remove file from file system after zipping
    """
    #print 'zipping result into %s' % output_zipfile
    with zipfile.ZipFile(output_zipfile, 'a', zipfile.ZIP_DEFLATED, allowZip64=True) as myzip:
        for file_in_zip in zip_result:
            #print 'zipping %s...' % file_in_zip['arcname']
            myzip.write(file_in_zip['filename'], file_in_zip['arcname'])
            if file_in_zip.get('delete_after', False):
                #print 'removing %r (%s in arc)' % (file_in_zip['filename'], file_in_zip['arcname'])
                os.remove(file_in_zip['filename'])


def find_boundary(input_files):
    """Return dict with x_min, x_max, y_min, y_max."""
    x_min = None
    x_max = None
    y_max = None
    y_min = None

    for input_file in input_files:
        log.debug('  - checking bbox of %s...' % input_file['scenario'])
        linux_filename = linuxify_pathname(input_file['filename'])
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

                dataset = None
                del dataset
    return {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}


def dataset2array(dataset):
    """ Return numpy masked array. """
    data = dataset.ReadAsArray()
    mask = np.equal(data, dataset.GetRasterBand(1).GetNoDataValue())
    return np.ma.array(data, mask=mask)


def dijkring_arrays_to_zip(input_files, tmp_zip_filename, gridtype='output', gridsize=50):
    """
    Return arrays in a dict with key 'dijkringnr'.
    Value is a tif dataset

    Input_files is a list with dicts 'dijkringnr' and 'filename'

    gridtype is used to generate useful arcnames
    """
    NO_DATA_VALUE = -9999
    tifdriver = gdal.GetDriverByName(b'gtiff')
    ascdriver = gdal.GetDriverByName(b'aaigrid')

    dijkring_datasets = {}  # key is dijkringnr
    boundary = find_boundary(input_files)
    x_min = boundary.get("x_min")
    x_max = boundary.get("x_max")
    y_max = boundary.get("y_max")
    y_min = boundary.get("y_min")

    size_x = int(abs((x_max - x_min) / gridsize))
    size_y = int(abs((y_max - y_min) / gridsize))
    log.debug('resulting image: %f %f %f %f size: %f %f' % (
        x_min, y_min, x_max, y_max, size_x, size_y))

    len_input_files = len(input_files)
    for index, input_file in enumerate(input_files):
        log.debug(
            '  - processing result (%d/%d) for scenario %s...' % (index + 1, len_input_files, input_file['scenario']))
        #print input_file
        linux_filename = linuxify_pathname(input_file['filename'])
        if not is_valid_zipfile(linux_filename):
            continue
        log.debug("Linuxified filepath: {0}".format(linux_filename))
        dijkringnr = input_file['dijkringnr']
        if dijkringnr is None:
            dijkringnr = 0
        with files.temporarily_unzipped(linux_filename) as files_in_zip:
            for filename_in_zip in files_in_zip:

                dataset = gdal.Open(str(filename_in_zip))

                tif_filename = tempfile.mkstemp()[1]
                reprojected_dataset = tifdriver.Create(
                    str(tif_filename), size_x, size_y, 1, gdal.gdalconst.GDT_Float64, options=['COMPRESS=DEFLATE']
                )
                reprojected_dataset.SetGeoTransform((x_min, gridsize, 0, y_max, 0, -gridsize))
                reprojected_band = reprojected_dataset.GetRasterBand(1)

                reprojected_band.SetNoDataValue(NO_DATA_VALUE)
                log.debug("Sart filling reprojected dataset with {}".format(NO_DATA_VALUE))
                log.debug("TIME: {}".format(datetime.today().isoformat()))
                reprojected_band.Fill(NO_DATA_VALUE)
                log.debug("END TIME: {}".format(datetime.today().isoformat()))
                log.debug("Start reprojecting image.")
                log.debug("TIME: {}".format(datetime.today().isoformat()))
                gdal.ReprojectImage(dataset, reprojected_dataset)
                log.debug("END TIME: {}".format(datetime.today().isoformat()))

                if dijkringnr in dijkring_datasets:
                    log.debug("Open tif {}".format(dijkring_datasets[dijkringnr]))
                    log.debug("TIME: {}".format(datetime.today().isoformat()))
                    oldmaxdataset = gdal.Open(
                            str(dijkring_datasets[dijkringnr]),
                            gdal.GA_Update,
                    )
                    log.debug("Calculate maxarray")
                    log.debug("TIME: {}".format(datetime.today().isoformat()))
                    oldmax_band = oldmaxdataset.GetRasterBand(1)
                    for lineno in range(reprojected_dataset.RasterYSize):

                        newlinearray = np.fromstring(
                            reprojected_band.ReadRaster(0, lineno, reprojected_dataset.RasterXSize, 1),
                            dtype=np.float64,
                        )
                        newlinemaskedarray = np.ma.array(
                            newlinearray,
                            mask=np.equal(newlinearray, NO_DATA_VALUE),
                        )

                        oldmaxlinearray = np.fromstring(
                            oldmax_band.ReadRaster(0, lineno, reprojected_dataset.RasterXSize, 1),
                            dtype=np.float64,
                        )
                        oldmaxlinemaskedarray = np.ma.array(
                            oldmaxlinearray,
                            mask=np.equal(oldmaxlinearray, NO_DATA_VALUE),
                        )
                        newmaxlinemaskedarray = np.ma.array([oldmaxlinemaskedarray,
                                                             newlinemaskedarray]).max(0)
                        oldmax_band.WriteRaster(0, lineno, reprojected_dataset.RasterXSize, 1,
                                                newmaxlinemaskedarray.filled(NO_DATA_VALUE).tostring())

                    log.debug("END TIME: {}".format(datetime.today().isoformat()))
                else:
                    # The tempfile wil be removed at the end of export
                    tmp_file_name = tempfile.mkstemp(prefix=str(dijkringnr), suffix='.tif')[1]
                    log.debug("Start copy to {}".format(tmp_file_name))
                    log.debug("TIME: {}".format(datetime.today().isoformat()))
                    tifdriver.CreateCopy(tmp_file_name, reprojected_dataset, options=['COMPRESS=DEFLATE'])
                    log.debug("END COPY TIME: {}".format(datetime.today().isoformat()))
                    dijkring_datasets[dijkringnr] = tmp_file_name
                    del reprojected_dataset
                if os.path.isfile(tif_filename):
                    os.remove(tif_filename)

    #for dijkringnr, dataset in dijkring_datasets.items():
    for dijkringnr, dataset_filename in dijkring_datasets.items():
        log.debug("Create ascii file for {}".format(dataset_filename))
        dataset = gdal.Open(str(dataset_filename))

        # Commented this out, because everything was masked away in the test case.
        # # Apply dijkring mask
        # mask = get_dijkring_mask(
        #     dijkringnr, geo_projection, geo_transform,
        #     max_array.shape[1], max_array.shape[0])
        # # Everything is masked: a) if it was masked already OR b) it's in the dijkring_mask
        # max_array.mask = np.maximum(mask, max_array.mask)

        ascii_filename = tempfile.mkstemp()[1]
        ascdriver.CreateCopy(ascii_filename, dataset)
        if dijkringnr is None:
            dijkringnr = 0
        arc_name = '%s_%d.asc' % (gridtype, dijkringnr)
        add_to_zip(tmp_zip_filename,
                   [{'filename': ascii_filename, 'arcname': arc_name, 'delete_after': True}])
        if os.path.isfile(ascii_filename):
            os.remove(ascii_filename)

        del dataset

    return dijkring_datasets


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
    dijkring_datasets = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, gridtype,
        gridsize=export_run.gridsize)
    return dijkring_datasets


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
    dijkring_datasets = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, gridtype,
        gridsize=export_run.gridsize)
    return dijkring_datasets


def calc_possible_flooded_area(tmp_zip_filename, max_waterdepths_datasets):
    # Calculate the possible flooded area
    log.debug('export_possibly_flooded')
    for dijkringnr, dataset_filename in max_waterdepths_datasets.items():

        dataset = gdal.Open(str(dataset_filename))

        geo_transform = dataset.GetGeoTransform()
        maxarray = dataset2array(dataset)

        del dataset

        flooded_array = np.ma.zeros(maxarray.shape, dtype=np.uint8)
        flooded_array[np.ma.greater_equal(maxarray, 0.02)] = 1

        ascii_filename = tempfile.mkstemp()[1]
        if dijkringnr is None:
            dijkringnr = 0
        arc_name = 'possibly_flooded_%d.asc' % (dijkringnr)

        write_masked_array_as_ascii(
            ascii_filename, flooded_array, geo_transform)

        add_to_zip(
            tmp_zip_filename,
            [{'filename': ascii_filename,
              'arcname': arc_name,
              'delete_after': True}])
        if os.path.isfile(ascii_filename):
            os.remove(ascii_filename)


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
    max_waterdepths = {}
    max_flowvelocity = {}

    tmp_zip_filename = tempfile.mkstemp()[1]

    if export_run.export_max_waterdepth or export_run.export_possibly_flooded:
        max_waterdepths = calc_max_waterdepths(
            tmp_zip_filename, export_run)

    if export_run.export_max_flowvelocity:
        max_flowvelocity = calc_max_flowvelocity(
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

    # remove tmp files
    if os.path.isfile(tmp_zip_filename):
        os.remove(tmp_zip_filename)

    for tmp_file in max_waterdepths.values():
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)

    for tmp_file in max_flowvelocity.values():
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)

    log.debug('Finished.')
