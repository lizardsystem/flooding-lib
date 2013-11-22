import json
from django.http import HttpResponse


def JSONResponse(ob):
    return HttpResponse(
        json.dumps(ob), mimetype="application/json")
