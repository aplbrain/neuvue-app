import json
import logging
from django.http import HttpResponse
from django.views.generic.base import View
from ..models import Namespace
from ..plugins import NEUROGLANCER_PLUGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NgStatePluginsView(View):

    def post(self, request, *args, **kwargs):
        data = str(request.body.decode("utf-8"))
        data = json.loads(data)

        # Make sure input state is well formed
        try:
            namespace = data["namespace"]
            ng_state = dict(data["ng_state"])
        except:
            return HttpResponse("Ng state could not be parsed into dict", status=500)

        # Make sure plugin exists
        try:
            # Get name and params from namespace
            namespace = Namespace.objects.get(namespace=namespace)
            ng_state_plugin_name = namespace.ng_state_plugin.name
            ng_state_plugin_params = namespace.get_effective_plugin_params()
            print(type(ng_state_plugin_params))
            print(ng_state_plugin_params)
            ng_state_plugin = NEUROGLANCER_PLUGINS[ng_state_plugin_name](**ng_state_plugin_params)
        except:
            return HttpResponse(f"Ng state plugin {ng_state_plugin} does not exist", status=501)
        
        plugin_response = ng_state_plugin.modify_state(ng_state)
        payload = {"message" : plugin_response.message, "ngstate" : plugin_response.modified_state}
        return HttpResponse(json.dumps(payload), content_type="application/json", status=plugin_response.status_code)
