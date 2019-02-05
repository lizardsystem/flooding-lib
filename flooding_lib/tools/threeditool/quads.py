# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from math import ceil
from six.moves import zip_longest
import logging

from osgeo import osr
import netCDF4
import numpy as np

from flooding_lib.tools.threeditool import utils

logger = logging.getLogger(__name__)

CORRECTIONS = {'EPGS:28992': 'EPSG:28992'}


def get_groups(array):
    """
    Return (group, index) tuple.

    This is an efficient way of finding sets of indices to the unique values in
    an array.
    """
    order = array.argsort()
    group, i = np.unique(array[order], return_index=True)
    return group, [order[a:b] for a, b in zip_longest(i, i[1:])]


class Data(object):
    @classmethod
    def from_type_A(cls, nc):
        """
        Load and init from netCDF with results (type A).

        The netCDF contains 2D-node data starting at some index. There is no
        groundwater.
        """
        obj = Data()

        # determine 2D node slice
        n = nc.nFlowElem2d.item()

        # read centers
        centers = np.empty((n, 2), dtype='f8')
        centers[:, 0] = nc['FlowElem_xcc'][:n]
        centers[:, 1] = nc['FlowElem_ycc'][:n]
        obj.centers = centers

        # read node x coordinates for size analysis
        edges_x = nc['FlowElemContour_x'][:n]
        x1, x2 = edges_x.min(1), edges_x.max(1)
        obj.size, obj.index = get_groups(array=x2 - x1)

        # create trivial mapping returned node index to netcdf node index
        obj.nodes_sw = np.arange(n)
        obj.nodes_gw = np.full(n, n, dtype='i8')
        obj.no_data_node = n  # since there are no groundwater nodes

        # attributes
        projection = nc['projected_coordinate_system'].EPSG_code
        projection = CORRECTIONS.get(projection, projection)
        obj.kwargs = {
            'no_data_value': n,
            'projection': osr.GetUserInputAsWKT(str(projection)),
        }

        return obj

    @classmethod
    def from_type_B(cls, nc):
        """
        Load and init netCDF with results (type B).

        The netCDF contains separate variables for 2D nodes, but contain
        groundwater and surface water nodes mixed together.

        Convention: variable names referring to netCDF variables or indices
        thereof are prefixed with an underscore.

        All unique centers are placed on self, but the mapping for node types
        other than surface and groundwater are not included.
        """
        obj = Data()

        # find the indexes per node type
        _node_type = nc['Mesh2DNode_type']
        _node_type_data = _node_type[:]
        _node_type_sw = int(_node_type.surface_water_2d)
        _node_type_gw = int(_node_type.groundwater_2d)
        _index_all = dict(zip(*get_groups(_node_type_data)))
        _index_sw = _index_all.get(_node_type_sw, np.array([], int))
        _index_gw = _index_all.get(_node_type_gw, np.array([], int))

        # read centers of 2d nodes
        _n = nc.dimensions['nMesh2D_nodes'].size
        _centers = np.empty((_n, 2), 'f8')
        _centers[:, 0] = nc['Mesh2DFace_xcc'][:]
        _centers[:, 1] = nc['Mesh2DFace_ycc'][:]

        # determine unique set of centers
        _centers1d = _centers.view('f8,f8').ravel()
        centers, unique = np.unique(_centers1d, return_index=True)
        obj.centers = centers.view('f8').reshape(-1, 2)
        n = len(centers)

        # read only x coordinates for size analysis assuming square nodes
        edges_x = nc['Mesh2DContour_x'][:]
        x1, x2 = edges_x[unique].min(1), edges_x[unique].max(1)
        obj.size, obj.index = get_groups(array=x2 - x1)

        # derive a mapping from returned node index to netcdf node index
        index_sw = np.searchsorted(centers, _centers1d[_index_sw])
        obj.nodes_sw = np.full(n, _n, dtype='i8')
        obj.nodes_sw[index_sw] = _index_sw
        index_gw = np.searchsorted(centers, _centers1d[_index_gw])
        obj.nodes_gw = np.full(n, _n, dtype='i8')
        obj.nodes_gw[index_gw] = _index_gw
        obj.no_data_node = _n

        # attributes
        projection = nc['projected_coordinate_system'].EPSG_code
        obj.kwargs = {
            'no_data_value': n,
            'projection': osr.GetUserInputAsWKT(str(projection)),
        }

        return obj

    def analyze(self):
        """
        Derive shape and geo_transform from centers and size of nodes.

        The routine that will be used to rasterize the locations of the nodes
        into a 2D index array needs the extent of the model inflated to match
        an integer number of the largest node present in the model.
        """
        # determine tentative extent from the centers
        (x1, y1), (x2, y2) = self.centers.min(0), self.centers.max(0)

        # geo_transform terms defining cellsize are based on smallest node
        s1 = self.size[0]  # width of smallest cells
        a, b, c, d = s1, 0, 0, -s1

        # the topleft of an arbitrary largest size cell serves as anchor for
        # the inflation procedure
        s2 = self.size[-1]  # width of largest cells
        m, n = self.centers[self.index[-1][0]] - 0.5 * s2

        # inflation is done by ceiling the extent on all sides to an integer
        # number of the largest cell dimensions
        X1 = m - s2 * ceil((m - x1) / s2)
        Y1 = n - s2 * ceil((n - y1) / s2)
        X2 = m + s2 * ceil((x2 - m) / s2)
        Y2 = n + s2 * ceil((y2 - n) / s2)

        self.shape = int((Y2 - Y1) / s1), int((X2 - X1) / s1)
        self.kwargs['geo_transform'] = utils.GeoTransform((X1, a, b, Y2, c, d))

    def layout(self):
        """
        Return a dict with data about the 2D node layout.

        The dict contains:
            array, kwargs      : enough to create a GDAL dataset
            centers            : coords of node centers for interpolation
            nodes_gw, nodes_sw : corresponding nodes in the netCDF file

        The 2D node layout array contains the indices to the calculation cells
        with the resolution of the smallest cells.
        """
        s1 = self.size[0]  # width of smallest cells
        geo_transform = self.kwargs['geo_transform']
        no_data_value = self.kwargs['no_data_value']
        array = np.full(self.shape, no_data_value, dtype='u4')

        # loop quads grouped by width
        msg = 'Add quads with width {} to result'
        for s2, i1 in zip(self.size, self.index):
            # an auxiliary array is used of which the cells correspond to the
            # size of the calculations cells of the current iteration

            # determine zoom factor, aux array and geo_transform
            factor = int(s2 / s1)
            aux_shape = tuple(int(n / factor) for n in array.shape)
            aux_array = np.full(aux_shape, no_data_value, dtype='u4')
            aux_geo_transform = geo_transform.scale(x=factor, y=factor)

            # fill-in the quads in the auxiliary array
            aux_centers = self.centers[i1]
            aux_indices = aux_geo_transform.get_indices(aux_centers)
            aux_array[aux_indices] = i1

            # resample using broadcasting to match the shape of main array
            aux_array.shape = (aux_shape + (1, 1))
            resampled_aux_array = np.broadcast_to(
                aux_array, aux_shape + (factor, factor),
            ).transpose(0, 2, 1, 3).reshape(array.shape)

            # paste active pixels from resampled array into main array
            i2 = resampled_aux_array != no_data_value
            array[i2] = resampled_aux_array[i2]

            logger.debug(msg.format(s2))

        layout = {
            'array': array[np.newaxis, ...],
            'kwargs': self.kwargs,
            'centers': self.centers,
            'nodes_gw': self.nodes_gw,
            'nodes_sw': self.nodes_sw,
            'no_data_node': self.no_data_node,
        }
        return layout


def get_layout(path):
    """
    Return dict with layout of calculation nodes.

    :param path: path to netCDF file containing simulation results.

    The returned dict contains:

        array: numpy array representing a spatial layout of node ids
        kwargs: dict with geo_transform, projection to position the layout
            array on the map and no_data_value indicating no calculation node
        centers: centers of calculation nodes by layout id
        nodes_gw: netCDF indices of groundwater nodes by layout id
        nodes_sw: netCDF indices of surface water nodes by layout id
        no_data_node: value in nodes_gw or nodes_sw indicating no netCDF index
            exists for given node type

    The no_data_value is a value in array indicating no calculation node exists
    at all for a given location on the map

    The no_data_node is a value in nodes_gw and nodes_sw indicating no
    calculation node of a given water type exists and therefore no mapping
    exists from the layout node id in array to the index in the node dimension
    in the netCDF.
    """
    with netCDF4.Dataset(path) as nc:
        if hasattr(nc, 'threedicore_version'):
            data = Data.from_type_B(nc)
        else:
            data = Data.from_type_A(nc)
        data.analyze()
        return data.layout()
