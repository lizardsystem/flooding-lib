"""Views for Pyramid-related URLs (usually called from Javascript)."""

import logging

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
