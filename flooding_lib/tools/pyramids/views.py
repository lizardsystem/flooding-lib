"""Views for Pyramid-related URLs (usually called from Javascript)."""

import logging

from osgeo import gdal
from osgeo import gdal_array
import numpy as np

from django.http import Http404
from django.views.decorators.http import require_GET

from flooding_presentation import models
from flooding_lib.util import geo
from flooding_lib.services import JSONResponse

logger = logging.getLogger(__name__)


def get_result_by_presentationlayer_id(
    presentationlayer_id, return_layer=False):
    try:
        presentation_layer = models.PresentationLayer.objects.get(
            pk=presentationlayer_id)
    except models.PresentationLayer.DoesNotExist:
        logger.debug("pyramid_parameters called with nonexisting id {}"
                     .format(presentationlayer_id))
        raise Http404()

    results = presentation_layer.results()
    if not results:
        logger.debug("pyramid parameters called on a "
                     "presentationlayer ({}) without results"
                     .format(presentationlayer_id))
        raise Http404()

    result = results[0]

    if not result.raster and not result.animation:
        logger.debug(
            "pyramid result (presentationlayer {}, result {})"
            " does not have a raster or animation."
            .format(presentationlayer_id, result.id))
        raise Http404()

    if return_layer:
        return result, presentation_layer
    else:
        return result


@require_GET
def pyramid_parameters(request):
    presentationlayer_id = request.GET.get('presentationlayer_id')
    result = get_result_by_presentationlayer_id(presentationlayer_id)

    return JSONResponse({
            'layer': result.raster.layer,
            'styles': 'PuBu'
            })


@require_GET
def animated_pyramid_parameters(request):
    presentationlayer_id = request.GET.get('presentationlayer_id')
    result = get_result_by_presentationlayer_id(presentationlayer_id)

    return JSONResponse({
            'frames': result.animation.frames,
            'layer': result.animation.layer(frame_nr='FRAME'),
            'styles': 'PuBu'
            })


@require_GET
def pyramid_value(request):
    """Get value in pyramid at some lat/lon coordinate."""
    presentationlayer_id = request.GET.get('presentationlayer_id')
    x = request.GET.get('lon')  # In Google
    y = request.GET.get('lat')

    rd_x, rd_y = geo.google_to_rd(x, y)

    result, presentation_layer = get_result_by_presentationlayer_id(
        presentationlayer_id, return_layer=True)
    unit = presentation_layer.presentationtype.unit

    pyramid = result.raster.pyramid

    value = pyramid.fetch_single_point(rd_x, rd_y)[0]

    if value is not None and value > 0:
        return JSONResponse({
                'value': value,
                'unit': unit or ""
                })
    else:
        return JSONResponse({})


@require_GET
def animation_value(request):
    presentationlayer_id = request.GET.get('presentationlayer_id')
    framenr = request.GET.get('framenr')
    x = request.GET.get('lon')  # In Google
    y = request.GET.get('lat')

    if None in (presentationlayer_id, framenr, x, y):
        raise Http404()

    try:
        framenr = int(framenr)
    except ValueError:
        raise Http404()

    result, presentation_layer = get_result_by_presentationlayer_id(
        presentationlayer_id, return_layer=True)
    unit = presentation_layer.presentationtype.unit

    animation = result.animation

    if animation is None:
        return JSONResponse({})

    if not (0 <= int(framenr) < animation.frames):
        raise Http404()

    rd_x, rd_y = geo.google_to_rd(x, y)

    value = point_from_dataset(animation, framenr, (rd_x, rd_y))

    return JSONResponse({'value': value, 'unit': unit})


def point_from_dataset(animation, framenr, point):
    x, y = point
    p, a, b, q, c, d = animation.get_geotransform()
    minv = np.linalg.inv([[a, b], [c, d]])
    u, v = np.dot(minv, [x - p, y - q])

    u = int(u)
    v = int(v)

    if not ((0 <= u < animation.cols) and (0 <= v < animation.rows)):
        # Outside animation
        return None

    dataset = gdal.Open(animation.get_dataset_path(framenr))
    if dataset is None:
        return None

    data = dataset.ReadRaster(u, v, 1, 1, band_list=[1])
    data_type = gdal_array.flip_code(dataset.GetRasterBand(1).DataType)
    return np.fromstring(data, dtype=data_type)[0]
