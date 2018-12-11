import json
from django.http import HttpResponse


def JSONResponse(ob):
    return HttpResponse(
        json.dumps(ob), content_type="application/json")
