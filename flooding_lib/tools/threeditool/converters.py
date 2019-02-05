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

# resulting dtypes for the 3Di variable data
DTYPE = 'f4'
NO_DATA_VALUE = np.finfo(DTYPE).min.item()


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


class Converter(object):
    """
    there are three ways in which the no data value can end up in the resulting
    arrays.

    1) no calculation node is defined on that place on the map at all.
    2) the type of water (surface water) is not defined on that spot.
    3) the node has no data at that timestep.

    """

    def __init__(self, results_3di_path):
        """ only remember the path to the 3di results. """
        self.results_3di_path = results_3di_path

    def get_variable(self, name):
        """
        Return the variable corresponding to a variable name.

        Because variables have different names in different versions of the
        result netCDF files, some renaming is done here.
        """
        if name.startswith('time'):
            variable_name = name
        elif name in self.rename:
            variable_name = self.rename[name]
        else:
            variable_name = self.prefix + name
        return self.nc[variable_name]

    def __enter__(self):
        """ init quads and arrays. """
        self.nc = Dataset(self.results_3di_path)

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

        # add a time object
        time_variable = self.get_variable('time')
        time_units = time_variable.getncattr('units')
        time_data = time_variable[:]
        self.time = Time(data=time_data, units=time_units)

        # analyze the layout of the results
        self.layout = get_layout(self.results_3di_path)

        return self

    @property
    def period(self):
        return self.time.period

    @property
    def kwargs(self):
        return {
            'no_data_value': NO_DATA_VALUE,
            'projection': self.layout['kwargs']['projection'],
            'geo_transform': self.layout['kwargs']['geo_transform'],
        }

    def __exit__(self, exception_type, error, traceback):
        """ close netcdf dataset. """
        self.nc.close()

    def _no_data_value(self, variable):
        """ return variable, no_data_value. """
        try:
            return variable._FillValue.astype(DTYPE)
        except AttributeError:
            return None

    def _read_snapshot(self, variable, index):
        """ Return a 1d array with replaced no data values. """
        # create an oversized array of the correct dtype
        values = np.empty(variable.shape[-1] + 1, dtype=DTYPE)

        # put global no data value in the last position
        values[-1] = NO_DATA_VALUE

        # read the variable into the remaining part
        values[:-1] = variable[index]

        # replace variable no data with global no data if applicable
        no_data_value = self._no_data_value(variable)
        if no_data_value is not None:
            values[values == no_data_value] = NO_DATA_VALUE

        # convert to 2d array
        return self._make_2d(values)

    def _get_batches(self, variable):
        """ Return generator of variable batches. """
        nrows, ncols = variable.shape
        nsize_batch = 2 ** 20 / variable.dtype.itemsize
        nrows_batch = max(1, int(nsize_batch // ncols))

        nbatch = -int(-nrows // nrows_batch)

        for i in range(nbatch):
            start = i * nrows_batch
            stop = start + nrows_batch
            yield np.asarray(variable[start:stop])

    def _get_magnitude_batches(self, variable1, variable2):
        """ Return generator of magnitude batches. """
        batches1 = self._get_batches(variable1)
        batches2 = self._get_batches(variable2)

        no_data_value = self._no_data_value(variable1)

        for batch1, batch2 in zip(batches1, batches2):
            # determine the selection that has data
            if no_data_value is not None:
                sel = (batch1 != no_data_value)
            else:
                sel = True

            # calculate magnitude
            magnitude = np.full_like(batch1, no_data_value)
            magnitude[sel] = np.sqrt(batch1[sel] ** 2 + batch2[sel] ** 2)

            yield magnitude

    def _read_maximum(self, variables):
        """
        Return a 1d array with added no_data_value element.

        The returned values are the timewise maximum of the variable. To
        prevent the method from being too memory-hungry, the maximum is found
        incrementally on the double precision data.
        """
        # create double precision work array
        doubles = np.empty(variable1.shape[-1], dtype=variable.dtype)

        no_data_value = self._no_data_value(variable)
        if no_data_value is not None:
            # we need the absolute minimum for the maximum aggregation
            MINIMUM = np.finfo(variable.dtype).min

        for batch in self._get_batches(variable):
            # replace variable no data with minimum
            if no_data_value is not None:
                batch[batch == no_data_value] = MINIMUM

            # replace doubles with maximum of doubles and batch
            np.maximum(doubles, batch.max(0), out=doubles)

        # replace the double precision minimum with the global no data value
        if no_data_value is not None:
            doubles[doubles == MINIMUM] = NO_DATA_VALUE

        # single precision part - create oversized array for the singles
        singles = np.empty(variable.shape[-1] + 1, dtype=DTYPE)

        # put global no data value in the last position
        singles[-1] = NO_DATA_VALUE

        # paste the data from the doubles
        singles[:-1] = doubles

        # convert to 2d array
        return self._make_2d(singles)


            



            if no_data_value is not None:
                batch[batch == no_data_value] = 0

            # replace doubles with maximum of doubles and batch
            np.maximum(doubles, batch.max(0), out=doubles)

        # replace the double precision minimum with the global no data value
        if no_data_value is not None:
            doubles[doubles == MINIMUM] = NO_DATA_VALUE

        # single precision part - create oversized array for the singles
        singles = np.empty(variable.shape[-1] + 1, dtype=DTYPE)

        # put global no data value in the last position
        singles[-1] = NO_DATA_VALUE

        # paste the data from the doubles
        singles[:-1] = doubles

        # convert to 2d array
        return self._make_2d(singles)

    def _make_2d(self, values):
        """
        return 2d array with values.

        :param values: a 1d array produced by one of the _read methods.
        :param no_data_value: no data value.

        Note that values[-1] should already contain the no data value.
        """
        nodes = self.layout['nodes_sw']

        # a lookup array will be constructed containing the values from the
        # netcdf at the correct positions for making a 2d array.
        lookup_size = self.layout['kwargs']['no_data_value'] + 1
        lookup = np.empty(lookup_size, dtype=DTYPE)
        lookup[-1] = NO_DATA_VALUE

        # reorder the data from netcdf to the layout order, putting the index
        # of the last element in the values where the netcdf has no data
        # (indicated by the 'no data node')
        reorder = np.where(
            nodes == self.layout['no_data_node'],
            len(values) - 1,
            nodes,
        )
        lookup[:-1] = values[reorder]

        return lookup[self.layout['array']]

    def extract(self, name, offset=0, interval=3600):
        """
        return dict containing datetime, values, no_data_value.

        :param name: name of netcdf variable to extract
        :param offset: offset in seconds from start of calculation
        :param interval: seconds between generated arrays
        """
        variable = self.get_variable(name)

        start, stop = self.time.period
        current = start + Timedelta(seconds=offset)
        step = Timedelta(seconds=interval)

        while current <= stop:
            index, datetime = self.time.find(current)
            array = self._read_snapshot(variable=variable, index=index)
            yield {'datetime': datetime, 'array': array}
            current += step

    def maximum(self, name):
        """
        return dict containing values, no_data_value.
        """
        variable = self.get_variable(name)
        return self._read_maximum(variable=variable)
