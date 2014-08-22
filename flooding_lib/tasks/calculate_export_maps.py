# Run under linux
# Task 200

# TODO: Instead of unzipping zipfiles to get to the datasets inside,
#       it's possible to use /vsizip/ gdal paths. We didn't do that for
#       two reasons:
#       - The script was inexplicably slow and we thought /vsizip/ might
#         be the cause (it wasn't), so we took the cases we had out
#       - There are files with more than one dataset inside, need to think
#         how to handle that. But probably the current code doesn't do it
#         entirely correctly either.

from __future__ import unicode_literals
from __future__ import print_function

from collections import namedtuple

import json
import tempfile
import os
from StringIO import StringIO

from flooding_lib.models import ResultType
from flooding_lib.tools.importtool.models import InputField
from flooding_lib.tools.exporttool.models import ExportRun
from flooding_lib.tools.exporttool.models import Setting
from flooding_lib.models import Result as FloodingResult
from flooding_lib.tools.exporttool.models import Result
from flooding_lib.util import files

import numpy as np
import zipfile
import shutil

from osgeo import gdal

import logging
log = logging.getLogger(__name__)

INPUTFIELD_STARTMOMENT_BREACHGROWTH_ID = 9
INPUTFIELD_SCENARIO_DURATION = 72
INPUTFIELD_BUITENWATERTYPE = 10

NO_DATA_VALUE = -9999

TIFDRIVER = gdal.GetDriverByName(b'gtiff')
AAIGRIDDRIVER = gdal.GetDriverByName(b'aaigrid')

SizeInfo = namedtuple(
    'Size', 'x_min x_max y_min y_max size_x size_y gridsize')


def fix_path(path):
    """Linuxify pathname, force bytestring."""
    if isinstance(path, unicode):
        path = path.encode('utf8')
    return path.replace(b'\\', b'/')


def gdal_open(filepath):
    """Open the dataset in filepath. Linuxify path and turn it into a
    bytestring."""
    log.debug("gdal_open({f})".format(f=filepath))

    filepath = fix_path(filepath)
    if filepath.endswith('.zip'):
        filepath = b'/vsizip/' + filepath
    try:
        return gdal.Open(filepath)
    except RuntimeError:
        return None


def maxwaterdepth_geotransform(scenario):
    """Return the geotransform of this scenario's max water depth grid.
    Returns None if it doesn't have one."""

    log.debug("maxwaterdepth_geotransform({s})".format(s=scenario))
    try:
        maxdepth_result = scenario.result_set.get(
            resulttype__name='gridmaxwaterdepth')
        resultloc = maxdepth_result.absolute_resultloc

        for fn in all_files_in(resultloc):
            dataset = gdal_open(fn)

            if dataset is None:
                log.debug("Gdal failed to open: {}".format(resultloc))
                return None

            return dataset.GetGeoTransform()
    except FloodingResult.DoesNotExist:
        return None


def mktemp():
    log.debug("mktemp()")
    """Make a temp file

    You are responsible for deleting it.
    """
    f = tempfile.NamedTemporaryFile(delete=False, prefix='task_200_')
    pathname = f.name
    f.close()
    return pathname


def remove_mkstemp(fd, path):
    """Close a temporary file that was opened with mkstemp()."""
    if os.path.isfile(path):
        os.close(fd)
        os.remove(path)


def is_valid_zipfile(linux_filename):
    """Check if the passed file is a valid zipfile."""
    # log.debug disabled due error
    #log.debug("is_valid_zipfile({f})".format(f=linux_filename))
    if not os.path.isfile(linux_filename):
        return False
    try:
        zipf = zipfile.ZipFile(open(linux_filename, 'rb'))
        test = zipf.testzip()
        if test is not None:
            log.warn("Corrupted zipfile {0}".format(linux_filename))
            return False
    except:
        return False

    return True


def all_files_in(filename):
    """Generator that yields filename if it is not a zip, and all
    files inside otherwise. First linuxifies filename. Yields nothing
    in case filename is not a file, or a bad zip file.

    Unzipped files are cleaned up (and thus unusable) after looping
    through this! Therefore if you only need to read the first file,
    don't use next(), but use a pattern like:

    for f in all_files_in(path):
        process(f)  # Process first file
        break       # Skip rest; files are cleaned up here
    """
    filename = fix_path(filename)
    log.debug(b"all_files_in({f})".format(f=filename))

    if is_valid_zipfile(filename):
        with files.temporarily_unzipped(filename) as files_in_zip:
            for filename_in_zip in files_in_zip:
                yield filename_in_zip
    else:
        if os.path.isfile(filename) and not filename.endswith(".zip"):
            yield filename
        # If it's not a file, or a bad zip, just return without
        # yielding anything.


def generate_dst_filename(export_run):
    """Create filename like
    [export name]_ddmmyyyy_hhMM.zip.

    Replace all ' ' with '_' in export name
    Cat export name to 20 chars."""
    log.debug("generate_dst_filename({e})".format(e=export_run))
    max_length = 20
    export_name = ""
    if export_run.name is not None:
        export_name = export_run.name[:max_length]
        export_name = export_name.strip()
        export_name = export_name.replace(' ', '_')

    c_date = export_run.creation_date

    dst_basename = "{0}_{1:02}{2:02}{3:04}_{4:02}{5:02}.zip".format(
        export_name, c_date.day, c_date.month,
        c_date.year, c_date.hour, c_date.minute)

    return dst_basename


def generate_export_meta(export_run, dst_filename):
    """Generate a dict with meta data for
    passed export."""
    log.debug("generate_export_meta({e}, {d})"
              .format(e=export_run, d=dst_filename))
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
    log.debug("create_json_meta_file({t}, {e}, {d})"
              .format(t=tmp_zip_filename, e=export_run, d=dst_filename))
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
    Actual legitimate use of reduce()!
    """
    log.debug("np_max({l})".format(l=list_of_arrays))
    return reduce(np.maximum, list_of_arrays)


def write_masked_array(
    filename, masked_array, geo_transform, driver=AAIGRIDDRIVER):
    """
    Use gdal to write a masked_array to a ascii file (or other type of file if
    a driver is passed). Normal (non-masked) arrays work as well.
    """
    log.debug("write_masked_array({f}, {m}, {g}, {d})"
              .format(f=filename, m=masked_array, g=geo_transform, d=driver))
    filename = fix_path(filename)  # GDAL wants bytestring filenames

    if hasattr(masked_array, 'fill_value'):
        masked_array.fill_value = NO_DATA_VALUE
        filled = masked_array.filled()
    else:
        filled = masked_array  # Not masked at all
    size_y, size_x = filled.shape
    num_bands = 1

    ds = TIFDRIVER.Create(filename, size_x, size_y, num_bands,
                          gdal.GDT_Byte)
    band = ds.GetRasterBand(1)
    band.WriteArray(filled)
    band.SetNoDataValue(NO_DATA_VALUE)
    ds.SetGeoTransform(geo_transform)

    # Now it gets written to the disk as ascii
    driver.CreateCopy(filename, ds)


def add_to_zip(output_zipfile, zip_result):
    """
    Zip all files listed in zip_result

    zip_result is a list of dictionaries with keys:
    - filename: filename on disc
    - arcname: target filename in archive
    - delete_after: set this to remove file from file system after zipping
    """
    log.debug("add_to_zip({o}, {z})".format(o=output_zipfile, z=zip_result))
    with zipfile.ZipFile(
        output_zipfile, 'a', zipfile.ZIP_DEFLATED, allowZip64=True) as myzip:
        for file_in_zip in zip_result:
            myzip.write(file_in_zip['filename'], file_in_zip['arcname'])
            if file_in_zip.get('delete_after', False):
                os.remove(file_in_zip['filename'])


def find_boundary(input_files, gridsize):
    """Return a SizeInfo object that contains the size information of
    the bounding box of the input_files. Yields an exception if there
    are 0 input files."""
    log.debug(b"find_boundary({i}, {g})".format(i=input_files, g=gridsize))
    x_min = None
    x_max = None
    y_max = None
    y_min = None

    log.debug("Length of input_files: {}".format(len(input_files)))

    if len(input_files) == 0:
        raise ValueError("find_boundary() called without input_files.")

    for input_file in input_files:
        log.debug(input_file)
        for filename in all_files_in(input_file['filename']):
            dataset = gdal_open(filename)
            if dataset is None:
                log.debug("Not found: {}".format(filename))
                continue  # Skip, corrupt file
            dataset.RasterXSize, dataset.RasterYSize
            geo_transform = dataset.GetGeoTransform()
            # something like (183050.0, 25.0, 0.0, 521505.0, 0.0, -25.0)
            this_x_min, this_y_max = geo_transform[0], geo_transform[3]
            this_x_max = (
                this_x_min + dataset.RasterXSize * geo_transform[1])
            this_y_min = (
                this_y_max + dataset.RasterYSize * geo_transform[5])

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

    return SizeInfo(
        x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
        size_x=size_x, size_y=size_y, gridsize=gridsize)


def dataset2array(dataset):
    """ Return numpy masked array. """
    log.debug("dataset2array({d})".format(d=dataset))
    data = dataset.ReadAsArray()
    mask = np.equal(data, dataset.GetRasterBand(1).GetNoDataValue())
    return np.ma.array(data, mask=mask)


def get_dataset_line_masked_array(dataset, band, line):
    # this debug line is too slow
    #log.debug("get_dataset_line_masked_array({d}, {b}, {l})"
    #          .format(d=dataset, b=band, l=line))
    linearray = np.fromstring(
        band.ReadRaster(
            0, line, dataset.RasterXSize, 1), dtype=np.float64)

    linemaskedarray = np.ma.array(
        linearray,
        mask=np.equal(linearray, NO_DATA_VALUE),
        )
    return linemaskedarray


def get_dataset_line_byte(band, xsize, line):
    return np.fromstring(
        band.ReadRaster(
            0, line, xsize, 1), dtype=np.int8)


def combine_with_dijkring_datasets(
    dijkring_datasets, dijkringnr, filename, size_info, combine_method='max'):
    """Dijkring_datasets is a dictionary with keys dijkring numbers
    and values combined datasets for that dijkring. This function adds
    a new dataset to a given dijkring's dataset, using either 'max' or
    'min' methods. Dataset values are float64."""
    log.debug("combine_with_dijkring_datasets({dd}, {d}, {f}, {s}, {c})"
              .format(dd=dijkring_datasets, d=dijkringnr, f=filename,
                      s=size_info, c=combine_method))

    reprojected_dataset = None
    fd = None
    tif_filename = None
    for dataset_pathname in all_files_in(filename):
        dataset = gdal_open(dataset_pathname)

        # Reproject dataset into TIF
        fd, tif_filename = tempfile.mkstemp()
        reprojected_dataset = TIFDRIVER.Create(
            tif_filename, size_info.size_x, size_info.size_y, 1,
            gdal.gdalconst.GDT_Float64,
            options=[b'COMPRESS=DEFLATE', b'BIGTIFF=YES']
            )
        reprojected_dataset.SetGeoTransform(
            (size_info.x_min, size_info.gridsize, 0,
             size_info.y_max, 0, -size_info.gridsize))
        reprojected_band = reprojected_dataset.GetRasterBand(1)
        reprojected_band.SetNoDataValue(NO_DATA_VALUE)
        reprojected_band.Fill(NO_DATA_VALUE)
        gdal.ReprojectImage(dataset, reprojected_dataset)
        dataset = None
        break

    if reprojected_dataset is None:
        # There were no files?
        if fd is not None:
            remove_mkstemp(fd, tif_filename)
        return

    if dijkringnr in dijkring_datasets:
        # Combine with existing dataset
        oldmaxdataset = gdal.Open(
            str(dijkring_datasets[dijkringnr]),
            gdal.GA_Update,
            )
        oldmax_band = oldmaxdataset.GetRasterBand(1)

        for lineno in range(reprojected_dataset.RasterYSize):
            # New line as masked array
            newlinemaskedarray = get_dataset_line_masked_array(
                reprojected_dataset, reprojected_band, lineno)

            # Existing line as masked array
            oldmaxlinemaskedarray = get_dataset_line_masked_array(
                reprojected_dataset, oldmax_band, lineno)

            # Combine
            if combine_method == 'min':
                newmaxlinemaskedarray = np.ma.array(
                    [oldmaxlinemaskedarray, newlinemaskedarray]).min(0)
            else:
                # Default is max
                newmaxlinemaskedarray = np.ma.array(
                    [oldmaxlinemaskedarray, newlinemaskedarray]).max(0)

            # Save to raster
            oldmax_band.WriteRaster(
                0, lineno, reprojected_dataset.RasterXSize, 1,
                newmaxlinemaskedarray.filled(NO_DATA_VALUE)
                .tostring())

        oldmaxdataset = None
        reprojected_dataset = None
    else:
        # Create new dijkring dataset
        # The tempfile wil be removed at the end of export
        tmp_file_name = tempfile.mkstemp(
            prefix=str(dijkringnr), suffix='.tif')[1]
        TIFDRIVER.CreateCopy(
            tmp_file_name, reprojected_dataset,
            options=[b'COMPRESS=DEFLATE', b'BIGTIFF=YES'])
        dijkring_datasets[dijkringnr] = tmp_file_name
        reprojected_dataset = None

    # Remove reprojected dataset
    remove_mkstemp(fd, tif_filename)


def combine_with_dijkring_datasets_byte(
    dijkring_datasets, dijkringnr, filename, size_info):
    """Similar to combine_with_dijkring_datasets, but for datasets of
    which the datatype is int8 (signed byte). The only combine method
    so far is "bitwise or", used for the inundation sources map. Datasets
    are filled with the nodata value 0 instead of -9999."""

    dataset = gdal_open(filename)
    if dataset is None:
        return

    # Reproject dataset into TIF of correct size
    fd, tif_filename = tempfile.mkstemp()

    reprojected_dataset = TIFDRIVER.Create(
        tif_filename, size_info.size_x, size_info.size_y, 1,
        gdal.gdalconst.GDT_Byte, options=['COMPRESS=DEFLATE'])

    reprojected_dataset.SetGeoTransform(
        (size_info.x_min, size_info.gridsize, 0,
         size_info.y_max, 0, -size_info.gridsize))
    reprojected_band = reprojected_dataset.GetRasterBand(1)
    reprojected_band.SetNoDataValue(0)
    reprojected_band.Fill(0)
    log.debug("dataset {}".format(dataset))
    log.debug("reprojected_dataset {}".format(reprojected_dataset))
    gdal.ReprojectImage(dataset, reprojected_dataset)

    if dijkringnr in dijkring_datasets:
        # Combine with existing dataset
        olddataset = gdal.Open(
            str(dijkring_datasets[dijkringnr]),
            gdal.GA_Update)
        oldband = olddataset.GetRasterBand(1)

        for lineno in range(reprojected_dataset.RasterYSize):
            newline = get_dataset_line_byte(
                reprojected_band, size_info.size_x, lineno)
            oldline = get_dataset_line_byte(
                oldband, size_info.size_x, lineno)

            # Combine
            newline = np.bitwise_or(
                oldline.astype(np.int8),
                newline.astype(np.int8))

            # Save to raster
            oldband.WriteRaster(
                0, lineno, reprojected_dataset.RasterXSize, 1,
                newline.tostring())

        olddataset = None
        reprojected_dataset = None
    else:
        # Create new dijkring dataset
        # The tempfile wil be removed at the end of export
        tmp_file_name = tempfile.mkstemp(
            prefix=str(dijkringnr), suffix='.tif')[1]
        TIFDRIVER.CreateCopy(
            tmp_file_name, reprojected_dataset,
            options=[b'COMPRESS=DEFLATE'])
        dijkring_datasets[dijkringnr] = tmp_file_name
        reprojected_dataset = None

    # Remove reprojected dataset
    remove_mkstemp(fd, tif_filename)


def dijkring_arrays_to_zip(
    input_files, zip_filename, gridtype='output', gridsize=50,
    combine_method='max'):
    """
    Return arrays in a dict with key 'dijkringnr'.
    Value is a tif dataset

    Input_files is a list with dicts 'dijkringnr' and 'filename'

    gridtype is used to generate useful arcnames
    """
    if len(input_files) == 0:
        return dict()

    log.debug(b"dijkring_arrays_to_zip({i}, {z}, {g}, {gs}, {c})"
              .format(i=input_files, z=zip_filename, g=gridtype,
                      gs=gridsize, c=combine_method))

    dijkring_datasets = {}  # key is dijkringnr, values are tif
                            # filenames of combined datasets

    # Extent over all input files
    size_info = find_boundary(input_files, gridsize)

    for num, input_file in enumerate(input_files, 1):
        dijkringnr = input_file['dijkringnr'] or 0
        for filename in all_files_in(input_file['filename']):
            combine_with_dijkring_datasets(
                dijkring_datasets, dijkringnr, filename, size_info,
                combine_method=combine_method)

    save_dijkring_datasets_to_zip(
        zip_filename, dijkring_datasets, gridtype)

    return dijkring_datasets


def save_dijkring_datasets_to_zip(zip_file, dijkring_datasets, gridtype):
    log.debug(b"save_dijkring_datasets_to_zip({z}, {dd}, {g}"
              .format(z=zip_file, dd=dijkring_datasets, g=gridtype))

    for dijkringnr, dataset_filename in dijkring_datasets.items():
        dataset = gdal_open(dataset_filename)

        fd, ascii_filename = tempfile.mkstemp()

        AAIGRIDDRIVER.CreateCopy(ascii_filename, dataset)

        arc_name = '%s_%d.asc' % (gridtype, dijkringnr)
        add_to_zip(
            zip_file,
            [{
                    'filename': ascii_filename,
                    'arcname': arc_name,
                    'delete_after': True
                    }])

        remove_mkstemp(fd, ascii_filename)


def calc_max_waterdepths(tmp_zip_filename, export_run):
    log.debug('calc_max_waterdepths({t}, {e})'
              .format(t=tmp_zip_filename, e=export_run))

    gridtype = 'gridmaxwaterdepth'
    # Find out input files for this type
    input_files = export_run.input_files(gridtype)
    if not input_files:
        log.warn("No file to calc max waterdepths.")
        return {}
    dijkring_datasets = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, gridtype,
        gridsize=export_run.gridsize)
    return dijkring_datasets


def calc_sources_of_inundation(tmp_zip_filename, export_run):
    input_files = export_run.input_files('gridmaxwaterdepth')
    if not input_files:
        return

    temp_dirs = []

    buitenwatertype_inputfield = InputField.objects.get(
        pk=INPUTFIELD_BUITENWATERTYPE)

    for input_file in input_files:
        dataset = gdal_open(input_file['filename'])
        if dataset is None:
            log.debug(
                "Dataset {f} not found.".format(f=input_file['filename']))
            continue
        geo_transform = dataset.GetGeoTransform()
        maxarray = dataset2array(dataset)
        del dataset

        buitenwater_type = input_file['scenario'].value_for_inputfield(
            buitenwatertype_inputfield)

        buitenwater_type = {
            1: 1,
            2: 1,
            3: 2,
            4: 2,
            5: 2,
            6: 2,
            7: 2,
            8: 2,
            9: 4,
            10: 4}[buitenwater_type]

        log.debug("buitenwater_type: {}".format(buitenwater_type))
        flooded_array = (maxarray >= 0.02).filled(0).astype(np.int8)
        flooded_array *= buitenwater_type

        temp_dir = tempfile.mkdtemp()
        temp_dirs.append(temp_dir)
        temp_file = os.path.join(temp_dir, b'temptif.tif')

        write_masked_array(
            temp_file, flooded_array, geo_transform,
            driver=TIFDRIVER)

        input_file['filename'] = temp_file

    dijkring_datasets = {}  # key is dijkringnr, values are tif
                            # filenames of combined datasets

    # Extent over all input files
    size_info = find_boundary(input_files, export_run.gridsize)

    for num, input_file in enumerate(input_files, 1):
        dijkringnr = input_file['dijkringnr'] or 0
        combine_with_dijkring_datasets_byte(
            dijkring_datasets, dijkringnr, input_file['filename'], size_info)

    save_dijkring_datasets_to_zip(
        tmp_zip_filename, dijkring_datasets, 'grid_sources')

    for d in temp_dirs:
        shutil.rmtree(d)


def calc_wavefronts(tmp_zip_filename, export_run):
    log.debug("calc_wavefronts({t}, {e})"
              .format(t=tmp_zip_filename, e=export_run))

    input_files = export_run.input_files('computed_arrival_time')
    if not input_files:
        return {}

    dijkring_datasets = dijkring_arrays_to_zip(
        input_files, tmp_zip_filename, 'gridta',
        gridsize=export_run.gridsize, combine_method='min')

    return dijkring_datasets


def calc_rise_period(tmp_zip_filename, export_run):
    log.debug("calc_rise_period({t}, {e})"
              .format(t=tmp_zip_filename, e=export_run))

    input_files = export_run.input_files('computed_difference')
    if not input_files:
        return {}

    temp_dirs = []
    # Temporarily, re-compute the difference from time_of_max and
    # arrival_time, because it was computed the wrong way.
    new_input_files = []
    for input_file in input_files:
        filename = input_file['filename']
        arrival_time = filename.replace(
            'computed_difference', 'computed_arrival_time')
        time_of_max = filename.replace(
            'computed_difference', 'computed_time_of_max')

        arrival_time_dataset = gdal_open(arrival_time)
        if not arrival_time_dataset:
            continue

        grid = arrival_time_dataset.GetRasterBand(1).ReadAsArray()
        del arrival_time_dataset

        tmpdir = tempfile.mkdtemp()
        temp_dirs.append(tmpdir)
        tmpfile = os.path.join(tmpdir, b'computed_difference.tiff')

        time_of_max_dataset = gdal_open(time_of_max)
        if not time_of_max_dataset:
            continue

        difference_dataset = TIFDRIVER.CreateCopy(
            tmpfile, time_of_max_dataset)

        time_of_max_grid = (
            time_of_max_dataset.GetRasterBand(1).ReadAsArray())

        difference_grid = time_of_max_grid - grid
        difference_dataset.GetRasterBand(1).WriteArray(difference_grid)
        input_file['filename'] = tmpfile
        new_input_files.append(input_file)

    dijkring_datasets = dijkring_arrays_to_zip(
        new_input_files, tmp_zip_filename, 'grid_rise_period',
        gridsize=export_run.gridsize, combine_method='min')

    for tmpdir in temp_dirs:
        shutil.rmtree(tmpdir)

    return dijkring_datasets


def calc_max_flowvelocity(tmp_zip_filename, export_run):
    # Calc max flow velocity
    log.debug('calc_max_flowvelocity({t}, {e})'
              .format(t=tmp_zip_filename, e=export_run))

    gridtype = 'gridmaxflowvelocity'
    export_result_type = ResultType.objects.get(name=gridtype)
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
    log.debug('calc_possible_flooded_area({t}, {m})'
              .format(t=tmp_zip_filename, m=max_waterdepths_datasets))

    for dijkringnr, dataset_filename in max_waterdepths_datasets.items():

        dataset = gdal_open(dataset_filename)

        geo_transform = dataset.GetGeoTransform()
        maxarray = dataset2array(dataset)

        del dataset

        flooded_array = np.ma.zeros(maxarray.shape, dtype=np.int8)
        flooded_array[np.ma.greater_equal(maxarray, 0.02)] = 1

        fd, ascii_filename = tempfile.mkstemp()
        if dijkringnr is None:
            dijkringnr = 0
        arc_name = 'possibly_flooded_%d.asc' % (dijkringnr)

        write_masked_array(
            ascii_filename, flooded_array, geo_transform)

        add_to_zip(
            tmp_zip_filename,
            [{'filename': ascii_filename,
              'arcname': arc_name,
              'delete_after': True}])
        if os.path.isfile(ascii_filename):
            os.close(fd)
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
    log.debug("calculate_export_maps({e})".format(e=exportrun_id))
    export_run = ExportRun.objects.get(id=exportrun_id)
    export_folder = Setting.objects.get(key='EXPORT_FOLDER').value
    max_waterdepths = {}
    max_flowvelocity = {}

    zip_fd, tmp_zip_filename = tempfile.mkstemp()

    if export_run.export_max_waterdepth or export_run.export_possibly_flooded:
        max_waterdepths = calc_max_waterdepths(
            tmp_zip_filename, export_run)

    if export_run.export_max_flowvelocity:
        max_flowvelocity = calc_max_flowvelocity(
            tmp_zip_filename, export_run)

    if export_run.export_possibly_flooded:
        # Calculate the possible flooded area
        calc_possible_flooded_area(tmp_zip_filename,
                                   max_waterdepths)

    if export_run.export_arrival_times:
        calc_wavefronts(tmp_zip_filename, export_run)

    if export_run.export_period_of_increasing_waterlevel:
        calc_rise_period(tmp_zip_filename, export_run)

    if export_run.export_inundation_sources:
        calc_sources_of_inundation(tmp_zip_filename, export_run)

    dst_basename = generate_dst_filename(export_run)
    dst_filename = os.path.join(export_folder, dst_basename)

    create_json_meta_file(tmp_zip_filename, export_run, dst_filename)

    shutil.move(tmp_zip_filename, dst_filename)

    result_count = Result.objects.filter(export_run=export_run).count()
    if result_count > 0:
        log.warn('Warning: deleting old Result objects for this export run...')
        Result.objects.filter(export_run=export_run).delete()

    result = Result(
        name=export_run.name,
        file_basename=dst_basename,
        area=Result.RESULT_AREA_DIKED_AREA, export_run=export_run)
    result.save()

    export_run.state = ExportRun.EXPORT_STATE_DONE
    export_run.save()

    # remove tmp files
    if os.path.isfile(tmp_zip_filename):
        os.close(zip_fd)
        os.remove(tmp_zip_filename)

    for tmp_file in max_waterdepths.values():
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)

    for tmp_file in max_flowvelocity.values():
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)

    log.debug('Finished.')
