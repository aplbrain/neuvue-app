import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.generic.base import View
from ..models import NG_STATE_PLUGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NgStatePluginsView(View):

    def post(self, request, *args, **kwargs):
        data = str(request.body.decode("utf-8"))
        data = json.loads(data)

        # Make sure input state is well formed
        try:
            ng_state = dict(data["ng_state"])
        except:
            return HttpResponse("Ng state could not be parsed into dict", status=500)

        # Make sure plugin exists
        try:
            ng_state_plugin = data["ng_state_plugin"]
            ng_state_function = NG_STATE_PLUGINS[ng_state_plugin]
        except:
            return HttpResponse(f"Ng state plugin {ng_state_plugin} does not exist", status=501)

        ng_state = ng_state_function(ng_state)
        return JsonResponse(ng_state)

def test(ng_state):
    ng_state["position"] = [0,0,0]
    logger.info("Neuroglancer state modified by test plugin")
    return(ng_state)

# When creating a new plugin, don't forget to add it here and to the options in ../models.py
NG_STATE_PLUGINS = {"None": None, "Test": test}
