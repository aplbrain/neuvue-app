import logging

from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from neuvue.client import client

from ..models import Namespace, NeuroglancerHost
from ..neuroglancer import (
    construct_proofreading_state,
    construct_lineage_state_and_graph,
    construct_synapse_state,
    construct_nuclei_state,
    get_from_state_server,
    get_from_json,
    construct_url_from_existing,
)
from ..utils import is_url, is_json, is_authorized

# import the logging library

logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)


class InspectTaskView(View):
    def get(self, request, task_id=None, *args, **kwargs):
        if task_id in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{task_id}", content_type="application/javascript"
            )

        context = {
            "task_id": task_id,
            "ng_state": None,
            "ng_url": None,
            "ng_host": None,
            "error": None,
            "num_edits": 0,
        }

        # if not is_authorized(request.user):
        #     logging.warning(f"Unauthorized requests from {request.user}.")
        #     return redirect(reverse("index"))

        if task_id is None:
            return render(request, "inspect.html", context)

        try:
            task_df = client.get_task(task_id)
        except Exception as e:
            context["error"] = e
            return render(request, "inspect.html", context)

        namespace = task_df["namespace"]
        ng_state = task_df.get("ng_state")
        namespace_obj = Namespace.objects.get(namespace=namespace)

        if ng_state:
            if is_url(ng_state):
                if namespace_obj.ng_host != NeuroglancerHost.NEUVUE:
                    # Assume its a url to json state
                    context["ng_state"] = ng_state
                    context["ng_url"] = construct_url_from_existing(
                        context["ng_state"], namespace_obj.ng_host
                    )
                else:
                    logging.debug("Getting state from JSON State Server")
                    context["ng_state"] = get_from_state_server(ng_state)

            elif is_json(ng_state):
                # NG State is already in JSON format
                context["ng_state"] = get_from_json(ng_state)

        else:
            # Manually get the points for now, populate in client later.
            points = [client.get_point(x)["coordinate"] for x in task_df["points"]]
            context["ng_state"] = construct_proofreading_state(
                task_df, points, return_as="json"
            )

        context["ng_host"] = namespace_obj.ng_host
        context["task_id"] = task_df["_id"]
        context["seg_id"] = task_df["seg_id"]
        context["instructions"] = task_df["instructions"]
        context["assignee"] = task_df["assignee"]
        context["display_name"] = namespace_obj.display_name
        context["pcg_url"] = namespace_obj.pcg_source
        context["status"] = task_df["status"]
        if "flag_reason" in task_df["metadata"].keys():
            context["flag_reason"] = task_df["metadata"]["flag_reason"]

        metadata = task_df["metadata"]
        if metadata.get("decision"):
            context["decision"] = metadata["decision"]
        if metadata.get("operation_ids"):
            context["num_edits"] = len(metadata["operation_ids"])
        if task_df.get("tags"):
            context["tags"] = ",".join(task_df["tags"])
        return render(request, "inspect.html", context)

    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        return redirect(reverse("inspect", kwargs={"task_id": task_id}))


class LineageView(View):
    def get(self, request, root_id=None, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(reverse("index"))

        if root_id in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{root_id}", content_type="application/javascript"
            )

        context = {"root_id": root_id, "ng_state": None, "graph": None, "error": None}

        if root_id is None:
            return render(request, "lineage.html", context)

        try:
            context["ng_state"], context["graph"] = construct_lineage_state_and_graph(
                root_id
            )
        except Exception as e:
            context["error"] = e
            return render(request, "lineage.html", context)
        return render(request, "lineage.html", context)

    def post(self, request, *args, **kwargs):
        root_id = request.POST.get("root_id")
        return redirect(reverse("lineage", kwargs={"root_id": root_id}))


class SynapseView(View):
    def get(
        self,
        request,
        root_ids=None,
        pre_synapses=None,
        post_synapses=None,
        cleft_layer=None,
        timestamp=None,
        *args,
        **kwargs,
    ):
        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        if root_ids in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{root_ids}", content_type="application/javascript"
            )
        if timestamp in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{timestamp}", content_type="application/javascript"
            )

        context = {
            "root_ids": None,
            "pre_synapses": None,
            "post_synapses": None,
            "cleft_layer": None,
            "timestamp": None,
            "ng_state": None,
            "synapse_stats": None,
            "error": None,
        }

        if root_ids is None:
            return render(request, "synapse.html", context)

        root_ids = [x.strip() for x in root_ids.split(",")]
        flags = {
            "pre_synapses": pre_synapses,
            "post_synapses": post_synapses,
            "cleft_layer": cleft_layer,
            "timestamp": timestamp,
        }
        try:
            context["root_ids"] = root_ids
            context["pre_synapses"] = pre_synapses
            context["post_synapses"] = post_synapses
            context["cleft_layer"] = cleft_layer
            context["timestamp"] = timestamp
            context["ng_state"], context["synapse_stats"] = construct_synapse_state(
                root_ids=root_ids, flags=flags
            )
        except Exception as e:
            print(e)
            context["error"] = e

        return render(request, "synapse.html", context)

    def post(self, request, *args, **kwargs):
        root_ids = request.POST.get("root_ids")
        pre_synapses = request.POST.get("pre_synapses")
        post_synapses = request.POST.get("post_synapses")
        cleft_layer = request.POST.get("cleft_layer")
        timestamp = request.POST.get("timestamp")
        if not timestamp or timestamp in settings.STATIC_NG_FILES:
            timestamp = "None"

        return redirect(
            reverse(
                "synapse",
                kwargs={
                    "root_ids": root_ids,
                    "pre_synapses": pre_synapses,
                    "post_synapses": post_synapses,
                    "cleft_layer": cleft_layer,
                    "timestamp": timestamp,
                },
            )
        )


class NucleiView(View):
    def get(self, request, given_ids=None, *args, **kwargs):
        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        if given_ids in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{given_ids}", content_type="application/javascript"
            )

        context = {"given_ids": None, "error": None}

        if given_ids is None:
            return render(request, "nuclei.html", context)

        given_ids = [x.strip() for x in given_ids.split(",")]

        try:
            context["given_ids"] = given_ids
            (
                context["ng_state"],
                context["cell_types"],
                context["ids_not_found"],
            ) = construct_nuclei_state(given_ids=given_ids)
        except Exception as e:
            context["error"] = e

        return render(request, "nuclei.html", context)

    def post(self, request, *args, **kwargs):
        given_ids = request.POST.get("given_ids")

        return redirect(
            reverse(
                "nuclei",
                kwargs={
                    "given_ids": given_ids,
                },
            )
        )
