import json
import logging
from django.http import HttpResponse
from django.views.generic.base import View
from ..models import Namespace
from ..plugins import NEUROGLANCER_PLUGINS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def plugin_response(message, ng_state=None, status=500, additional_info=None):
    payload = {
        "message": message,
        "ngstate": ng_state,
        "additional_info": additional_info or {},
    }
    return HttpResponse(
        json.dumps(payload),
        content_type="application/json",
        status=status,
    )


class NgStatePluginsView(View):
    def post(self, request, *args, **kwargs):
        # Make sure input state is well formed
        try:
            data = str(request.body.decode("utf-8"))
            data = json.loads(data)
            namespace = data["namespace"]
            ng_state = dict(data["ng_state"])
            plugin_inputs = data.get("plugin_inputs", {})
            if not isinstance(plugin_inputs, dict):
                raise ValueError("plugin_inputs must be an object")
        except Exception as e:
            return plugin_response(
                f"Ng state plugin request could not be parsed: {e}",
                status=400,
            )

        # Make sure plugin exists
        try:
            # Get name and params from namespace
            namespace = Namespace.objects.get(namespace=namespace)
            if not namespace.ng_state_plugin:
                return plugin_response(
                    "No ng state plugin is configured for this namespace.",
                    ng_state=ng_state,
                    status=400,
                )
            ng_state_plugin_name = namespace.ng_state_plugin.name
            ng_state_plugin_params = namespace.get_effective_plugin_params()
            ng_state_plugin_cls = NEUROGLANCER_PLUGINS[ng_state_plugin_name]
            if ng_state_plugin_cls is None:
                return plugin_response(
                    f"Ng state plugin {ng_state_plugin_name} is disabled.",
                    ng_state=ng_state,
                    status=400,
                )
            ng_state_plugin = ng_state_plugin_cls(**ng_state_plugin_params)
        except Exception as e:
            logger.exception("Ng state plugin could not be initialized")
            return plugin_response(
                f"Ng state plugin could not be initialized: {e}",
                ng_state=ng_state,
                status=501,
            )

        try:
            response = ng_state_plugin.modify_state(
                ng_state,
                namespace=namespace,
                datastack=namespace.datastack,
                plugin_inputs=plugin_inputs,
            )
        except Exception as e:
            logger.exception("Ng state plugin failed")
            return plugin_response(
                f"Ng state plugin failed unexpectedly: {e}",
                ng_state=ng_state,
                status=500,
            )

        return plugin_response(
            response.message,
            ng_state=response.modified_state,
            status=response.status_code,
            additional_info=response.additional_info,
        )
