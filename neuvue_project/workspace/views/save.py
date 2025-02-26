import json
import logging

from django.http import HttpResponse
from django.apps import apps
from django.views.generic.base import View
from django.conf import settings

from neuvue.client import client

from ..models import Namespace

# import the logging library

logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)
Config = apps.get_model("preferences", "Config")


class SaveStateView(View):
    def post(self, request, *args, **kwargs):
        data = str(request.body.decode("utf-8"))
        data = json.loads(data)
        ng_state = data.get("ng_state")
        task_id = data.get("task_id")
        requesting_user = request.user.username

        # do some validation on ng_state (should be a link) and task_id (should be a string of random numbers and letters)
        # make sure each is not empty, and what you expect

        if ((type(ng_state) == str) and (ng_state)) and (
            (type(task_id) == str) and (task_id)
        ):
            try:
                logging.debug("Patching task state")
                client.patch_task(task_id, requesting_user, ng_state=ng_state)
                return HttpResponse(
                    "Successfully saved state", status=201, content_type="text/plain"
                )
            except:
                return HttpResponse(
                    "Was unable to save state", status=400, content_type="text/plain"
                )

        return HttpResponse(
            "Was unable to save state", status=400, content_type="text/plain"
        )


class SaveOperationsView(View):
    def post(self, request, *args, **kwargs):

        data = str(request.body.decode("utf-8"))
        data = json.loads(data)
        namespace = data.get("namespace")
        namespace_obj = Namespace.objects.get(namespace=namespace)
        tracked_operation_ids = data.get("operation_ids")
        task_id = data.get("task_id")
        task = client.get_task(task_id)
        requesting_user = request.user.username

        metadata = {}
        # if edits are possible
        if namespace_obj.track_operation_ids:
            if tracked_operation_ids and task:
                task_metadata = task.get("metadata")
                if "operation_ids" in task_metadata:
                    metadata["operation_ids"] = list(
                        set(task_metadata["operation_ids"]).union(
                            set(tracked_operation_ids)
                        )
                    )
                else:
                    metadata["operation_ids"] = list(tracked_operation_ids)

            if (type(metadata) == dict) and (type(task_id) == str):
                try:
                    logging.debug("Patching task operations")
                    client.patch_task(task_id, requesting_user, metadata=metadata)
                    return HttpResponse(
                        "Successfully saved operations",
                        status=201,
                        content_type="text/plain",
                    )
                except:
                    return HttpResponse(
                        "Was unable to save operations",
                        status=400,
                        content_type="text/plain",
                    )
            return HttpResponse(
                "Was unable to save operations", status=400, content_type="text/plain"
            )
        return HttpResponse(
            "Operations not tracked in this namespace",
            status=201,
            content_type="text/plain",
        )
