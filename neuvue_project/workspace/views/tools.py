import logging

from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from neuvue.client import client

from ..models import Namespace, NeuroglancerHost, Datastack
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


class DatastackMixin:
    """Mixin to handle datastack selection and backward compatibility for URLs without datastack parameter"""

    def get_datastack(self, kwargs):
        """Get datastack from kwargs, default to first enabled datastack if not provided"""
        datastack = kwargs.get("datastack")
        if datastack is None:
            ds = Datastack.objects.filter(enabled=True).first()
            return ds.datastack_name if ds else "minnie65_phase3_v1"
        return datastack

    def get_datastack_object(self, datastack_name):
        """Get Datastack object, with fallback to default if not found"""
        try:
            return Datastack.objects.get(datastack_name=datastack_name, enabled=True)
        except Datastack.DoesNotExist:
            ds = Datastack.objects.filter(enabled=True).first()
            return ds if ds else None


class InspectTaskView(View):
    @staticmethod
    def _get_inspect_route_name(ng_host):
        if ng_host == NeuroglancerHost.SPELUNKER:
            return "spelunker-inspect-task"
        return "workspace-inspect-task"

    def get(self, request, task_id=None, *args, **kwargs):
        static_ng_root = request.path.split("/")[1]
        static_ng_name = static_ng_root.replace("-workspace", "")

        if task_id == static_ng_name:
            return redirect(
                f"/static/{static_ng_root}/index.html",
                content_type="text/html",
            )

        if task_id in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/{static_ng_root}/{task_id}",
                content_type="application/javascript",
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
        inspect_route_name = self._get_inspect_route_name(namespace_obj.ng_host)
        canonical_path = reverse(inspect_route_name, kwargs={"task_id": task_id})

        if request.path != canonical_path:
            return redirect(canonical_path)

        if ng_state:
            if is_url(ng_state.replace("middleauth+", "")):
                if namespace_obj.ng_host not in [
                    NeuroglancerHost.NEUVUE,
                    NeuroglancerHost.SPELUNKER,
                ]:
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


class LineageView(DatastackMixin, View):
    def get(self, request, datastack=None, root_id=None, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(reverse("index"))

        # Handle backward compatibility: redirect old URLs without datastack to new format
        if datastack is None and root_id is not None:
            ds = self.get_datastack({"datastack": None})
            return redirect(
                reverse("lineage", kwargs={"datastack": ds, "root_id": root_id})
            )

        if root_id in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{root_id}", content_type="application/javascript"
            )

        datastack_name = self.get_datastack({"datastack": datastack})
        ds_obj = self.get_datastack_object(datastack_name)

        context = {
            "root_id": root_id,
            "ng_state": None,
            "graph": None,
            "error": None,
            "datastack": datastack_name,
            "datastacks": Datastack.objects.filter(enabled=True),
        }

        if root_id is None:
            return render(request, "lineage.html", context)

        try:
            context["ng_state"], context["graph"] = construct_lineage_state_and_graph(
                root_id, datastack=datastack_name
            )
        except Exception as e:
            context["error"] = e
            return render(request, "lineage.html", context)
        return render(request, "lineage.html", context)

    def post(self, request, *args, **kwargs):
        datastack = request.POST.get("datastack")
        root_id = request.POST.get("root_id")
        return redirect(
            reverse("lineage", kwargs={"datastack": datastack, "root_id": root_id})
        )


class SynapseView(DatastackMixin, View):
    def get(
        self,
        request,
        datastack=None,
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

        # Handle backward compatibility: redirect old URLs without datastack to new format
        if datastack is None and root_ids is not None:
            ds = self.get_datastack({"datastack": None})
            return redirect(
                reverse(
                    "synapse",
                    kwargs={
                        "datastack": ds,
                        "root_ids": root_ids,
                        "pre_synapses": pre_synapses,
                        "post_synapses": post_synapses,
                        "cleft_layer": cleft_layer,
                        "timestamp": timestamp,
                    },
                )
            )

        if root_ids in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{root_ids}", content_type="application/javascript"
            )
        if timestamp in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{timestamp}", content_type="application/javascript"
            )

        datastack_name = self.get_datastack({"datastack": datastack})
        ds_obj = self.get_datastack_object(datastack_name)

        context = {
            "root_ids": None,
            "pre_synapses": None,
            "post_synapses": None,
            "cleft_layer": None,
            "timestamp": None,
            "ng_state": None,
            "synapse_stats": None,
            "error": None,
            "datastack": datastack_name,
            "datastacks": Datastack.objects.filter(enabled=True),
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
                root_ids=root_ids, flags=flags, datastack=datastack_name
            )
        except Exception as e:
            print(e)
            context["error"] = e

        return render(request, "synapse.html", context)

    def post(self, request, *args, **kwargs):
        datastack = request.POST.get("datastack")
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
                    "datastack": datastack,
                    "root_ids": root_ids,
                    "pre_synapses": pre_synapses,
                    "post_synapses": post_synapses,
                    "cleft_layer": cleft_layer,
                    "timestamp": timestamp,
                },
            )
        )


class NucleiView(DatastackMixin, View):
    def get(self, request, datastack=None, given_ids=None, *args, **kwargs):
        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        # Handle backward compatibility: redirect old URLs without datastack to new format
        if datastack is None and given_ids is not None:
            ds = self.get_datastack({"datastack": None})
            return redirect(
                reverse("nuclei", kwargs={"datastack": ds, "given_ids": given_ids})
            )

        if given_ids in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{given_ids}", content_type="application/javascript"
            )

        datastack_name = self.get_datastack({"datastack": datastack})
        ds_obj = self.get_datastack_object(datastack_name)

        context = {
            "given_ids": None,
            "error": None,
            "datastack": datastack_name,
            "datastacks": Datastack.objects.filter(enabled=True),
        }

        if given_ids is None:
            return render(request, "nuclei.html", context)

        given_ids = [x.strip() for x in given_ids.split(",")]

        try:
            context["given_ids"] = given_ids
            (
                context["ng_state"],
                context["cell_types"],
                context["ids_not_found"],
            ) = construct_nuclei_state(given_ids=given_ids, datastack=datastack_name)
        except Exception as e:
            context["error"] = e

        return render(request, "nuclei.html", context)

    def post(self, request, *args, **kwargs):
        datastack = request.POST.get("datastack")
        given_ids = request.POST.get("given_ids")

        return redirect(
            reverse(
                "nuclei",
                kwargs={
                    "datastack": datastack,
                    "given_ids": given_ids,
                },
            )
        )
