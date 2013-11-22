"""Views for Pyramid-related URLs (usually called from Javascript)."""

import logging

from gislib import projections

from django.http import Http404
from django.views.decorators.http import require_GET

from flooding_presentation import models
from flooding_lib.services import JSONResponse

logger = logging.getLogger(__name__)


def get_result_by_presentationlayer_id(presentationlayer_id):
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
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    result = get_result_by_presentationlayer_id(presentationlayer_id)
    pyramid = result.layer

    # Pyramids don't support get_value at a point yet, I have to stop
    # here.

    values = pyramid.get_data(
        wkt='POINT({lat} {lon})'.format(lat=lat, lon=lon),
        crs=projections.WGS84)

    if values and values[0] is not None:
        return JSONResponse({'value': values[0]})
    else:
        return JSONResponse({})

