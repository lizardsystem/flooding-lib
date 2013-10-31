"""Views for Pyramid-related URLs (usually called from Javascript)."""

import logging

from django.http import Http404
from django.views.decorators.http import require_GET

from flooding_presentation import models
from flooding_lib.services import JSONResponse

logger = logging.getLogger(__name__)


@require_GET
def pyramid_parameters(request):
    presentationlayer_id = request.GET.get('presentationlayer_id')

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

    if not result.raster:
        logger.debug(
            "pyramid result (presentationlayer {}, result {})"
            " does not have a raster."
            .format(presentationlayer_id, result.id))
        raise Http404()

    layer = result.raster.layer

    return JSONResponse({
            'layer': layer,
            'styles': 'PuBu'
            })
