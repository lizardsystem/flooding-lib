# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

# from datetime import datetime as Datetime
from datetime import timedelta as Timedelta

from netCDF4 import Dataset, num2date

import numpy as np

from flooding_lib.tools.threeditool.quads import get_layout


def maximum(reader):
        """
        Determine the maximum of the reader.
        """
        # we need the absolute minimum for the maximum aggregation
        MINIMUM = np.finfo(reader.dtype).min

        # create double precision work array
        result = np.full(reader.shape[-1], MINIMUM, dtype=reader.dtype)

        for batch in reader:
            if reader.no_data_value is not None:
                # replace batch no data with minimum
                batch[batch == reader.no_data_value] = MINIMUM

            # replace result with maximum of result and batch
            np.maximum(result, batch.max(0), out=result)

        # reinstall the original no data value
        if reader.no_data_value is not None:
            result[result == MINIMUM] = reader.no_data_value

        return result


class Time(object):
    def __init__(self, data, units):
        datetimes = num2date(data, units=units)
        self.time = np.array(datetimes, dtype='M8[us]')

    def __len__(self):
        return len(self.time)

    def find(self, dt):
        dt64 = np.datetime64(dt)
        index = (np.abs(self.time - dt64)).argmin()
        return index, self.time[index].item()

    @property
    def period(self):
        return self.time[0].item(), self.time[-1].item()


class Reader(object):
    """
    Wraps a netcdf variable, making batched reading and no data operations
    easier.
    """
    def __init__(self, variable):
        """
        Because variables have different names in different versions of the
        result netCDF files, some renaming is done here.
        """
        self._variable = variable

    def __getitem__(self, index):
        return self._variable.__getitem__(index)

    def __iter__(self):
        """ Return generator of batches. """
        nrows, ncols = self.shape
        nsize_batch = 2 ** 20 / self._variable.dtype.itemsize
        nrows_batch = max(1, int(nsize_batch // ncols))

        nbatch = -int(-nrows // nrows_batch)

        for i in range(nbatch):
            start = i * nrows_batch
            stop = start + nrows_batch
            yield np.asarray(self._variable[start:stop])

    @property
    def no_data_value(self):
        try:
            return self._variable._FillValue
        except AttributeError:
            return None

    @property
    def shape(self):
        return self._variable.shape

    @property
    def dtype(self):
        return self._variable.dtype


class MagnitudeReader(object):
    """
    Reads magnitude of two readers.
    """
    def __init__(self, reader_x, reader_y):
        self._reader_x = reader_x
        self._reader_y = reader_y

    @property
    def no_data_value(self):
        return self._reader_x.no_data_value

    @property
    def shape(self):
        return self._reader_x.shape

    @property
    def dtype(self):
        return self._reader_x.dtype

    def __iter__(self):
        """ Return generator of batches. """
        for batch1, batch2 in zip(self._reader_x, self._reader_y):
            # determine the selection that has data
            if self.no_data_value is None:
                sel = True
            else:
                sel = (batch1 != self.no_data_value)

            # calculate magnitude
            result = np.full_like(batch1, self.no_data_value)
            result[sel] = np.sqrt(batch1[sel] ** 2 + batch2[sel] ** 2)

            yield result


class Converter(object):
    """
    there are three ways in which the no data value can end up in the resulting
    arrays.

    1) no calculation node is defined on that place on the map at all.
    2) the type of water (surface water) is not defined on that spot.
    3) the node has no data at that timestep.

    """
    DTYPE = 'f4'
    NO_DATA_VALUE = -9999.

    def __init__(self, results_3di_path):
        """ only remember the path to the 3di results. """
        self.results_3di_path = results_3di_path

    def __enter__(self):
        """ init quads and arrays. """
        self.nc = Dataset(self.results_3di_path)

        # add a time object
        time_variable = self.nc['time']
        time_units = time_variable.getncattr('units')
        time_data = time_variable[:]
        self.time = Time(data=time_data, units=time_units)

        # analyze the layout of the results
        self.layout = get_layout(self.nc)

        # determine variable mappings and variable prefix
        if hasattr(self.nc, 'threedicore_version'):
            self.prefix = 'Mesh2D_'
            self.rename = {
                'sumax': 'Mesh2DFace_sumax',
                'bath': 'Mesh2DFace_zcc',
            }
        else:
            self.prefix = ''
            self.rename = {}

        return self

    # @property
    # def period(self):
        # return self.time.period

    @property
    def kwargs(self):
        return {
            'no_data_value': self.NO_DATA_VALUE,
            'projection': self.layout['kwargs']['projection'],
            'geo_transform': self.layout['kwargs']['geo_transform'],
        }

    def __exit__(self, exception_type, error, traceback):
        """ close netcdf dataset. """
        self.nc.close()

    def _get_reader(self, name):
        """
        :param name: Old version name of the variable.
        """
        if name in self.rename:
            variable_name = self.rename[name]
        else:
            variable_name = self.prefix + name

        return Reader(self.nc[variable_name])

    def _pad_and_replace(self, values, no_data_value):
        """
        Return numpy array one cell bigger than values.

        The returned array has our dtype and no data value. The added cell
        contains no data value. This is used in the conversion to 2D.
        """
        # create an oversized array of our dtype
        result = np.full(
            values.size + 1,
            self.NO_DATA_VALUE,
            dtype=self.DTYPE,
        )

        # determine where the data is in values
        if no_data_value is None:
            select = True
        else:
            select = values != no_data_value

        # use that to paste the data
        result[:-1][select] = values[select]

        return result

    def _make_2d(self, values, no_data_value):
        """
        return 2d array with values.

        :param values: a 1d array produced by one of the _read methods.
        :param no_data_value: no data value.

        Note that values[-1] should already contain the no data value.
        """
        # need an oversized values array in the final dtype
        values = self._pad_and_replace(
            values=values,
            no_data_value=no_data_value,
        )

        # a lookup array will be constructed containing the values from the
        # netcdf at the correct positions for making a 2d array.
        lookup_size = self.layout['kwargs']['no_data_value'] + 1
        lookup = np.empty(lookup_size, dtype=self.DTYPE)
        lookup[-1] = self.NO_DATA_VALUE

        # reorder the data from netcdf to the layout order, putting the index
        # of the last element in the values where the netcdf has no data
        # (indicated by the 'no data node')
        nodes = self.layout['nodes_sw']
        reorder = np.where(
            nodes == self.layout['no_data_node'],
            len(values) - 1,
            nodes,
        )
        lookup[:-1] = values[reorder]

        result = lookup[self.layout['array']]
        return result

    def _read_snapshot(self, name, index):
        """ Return a 2D array. """
        reader = self._get_reader(name)
        return self._make_2d(
            values=reader[index],
            no_data_value=reader.no_data_value,
        )

    def extract(self, name, offset=0, interval=3600):
        """
        Return generator of (datetime, array) tuples.

        Yield arrays at times in the simulation accordin to given offset and
        interval. It also yields at the last timestep in the period, because
        animation (elsewhere in this repository) is only detected if there are
        multiple frames to display.

        :param name: name of netcdf variable to extract
        :param offset: offset in seconds from start of calculation
        :param interval: seconds between generated arrays
        """
        start, stop = self.time.period
        current = start + Timedelta(seconds=offset)
        step = Timedelta(seconds=interval)

        def result_for_time(time):
            index, datetime = self.time.find(time)
            array = self._read_snapshot(name=name, index=index)
            return datetime, array

        while current <= stop:
            yield result_for_time(current)
            current += step
        yield result_for_time(stop)

    def maxlevel(self):
        """ Return numpy array. """
        reader = self._get_reader('s1')
        aggregated = maximum(reader)
        return self._make_2d(
            values=aggregated,
            no_data_value=reader.no_data_value,
        )

    def maxflow(self):
        """ Return numpy array. """
        reader = MagnitudeReader(
            self._get_reader('ucx'),
            self._get_reader('ucy'),
        )
        aggregated = maximum(reader)
        return self._make_2d(
            values=aggregated,
            no_data_value=reader.no_data_value,
        )
