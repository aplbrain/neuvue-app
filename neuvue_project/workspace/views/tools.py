import json
import logging
from datetime import datetime
from urllib.parse import urlparse

from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from neuvue.client import client

from ..models import Namespace, NeuroglancerHost, Datastack
from ..neuroglancer import (
    construct_proofreading_state,
    construct_cell_viewer_state,
    get_from_state_server,
    get_from_json,
    construct_url_from_existing,
)
from ..utils import is_url, is_json, is_authorized

# import the logging library

logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)


def queue_settings():
    queue_addr = settings.NEUVUE_QUEUE_ADDR
    parsed_queue_addr = urlparse(queue_addr)
    return {
        "queue_addr": queue_addr,
        "queue_display": parsed_queue_addr.netloc or queue_addr.rstrip("/"),
    }


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

    def _base_context(self, task_id=None, error=None):
        context = {
            "task_id": task_id,
            "ng_state": None,
            "ng_url": None,
            "ng_host": None,
            "error": error,
            "num_edits": 0,
            "task_summary": None,
            "task_metadata_rows": [],
            "data": {"settings": queue_settings()},
        }
        context["inspect_config"] = self._build_inspect_config(context)
        return context

    def _render_inspect(self, request, context):
        context["inspect_config"] = self._build_inspect_config(context)
        return render(request, "inspect.html", context)

    def _build_task_summary(self, context):
        return {
            "namespace_display": context.get("display_name"),
            "task_id": context.get("task_id"),
            "seg_id": context.get("seg_id"),
            "pcg_url": context.get("pcg_url"),
            "assignee": context.get("assignee"),
            "status": context.get("status"),
            "flag_reason": context.get("flag_reason"),
            "decision": context.get("decision"),
            "num_edits": context.get("num_edits", 0),
            "tags": context.get("tags"),
        }

    def _build_task_metadata_rows(self, task_summary):
        row_specs = [
            ("Namespace", "namespace_display", "Copy namespace"),
            ("Task ID", "task_id", "Copy task ID"),
            ("Segmentation ID", "seg_id", "Copy segmentation ID"),
            ("PCG Endpoint", "pcg_url", "Copy PCG endpoint"),
            ("Assignee", "assignee", "Copy assignee"),
            ("Status", "status", "Copy status"),
            ("Flag Reason", "flag_reason", "Copy flag reason"),
            ("Decision", "decision", "Copy decision"),
            ("Number of Edits", "num_edits", "Copy number of edits"),
            ("Tags", "tags", "Copy tags"),
        ]

        rows = []
        for label, key, copy_title in row_specs:
            value = task_summary.get(key)
            if value is None or value == "":
                continue
            rows.append(
                {
                    "label": label,
                    "value": value,
                    "copy_title": copy_title,
                }
            )
        return rows

    def _build_inspect_config(self, context):
        return {
            "ngHost": context.get("ng_host"),
            "ngUrl": context.get("ng_url"),
            "ngState": self._normalize_ng_state_for_config(context.get("ng_state")),
            "taskId": context.get("task_id"),
            "urls": {
                "inspect": reverse("inspect"),
            },
        }

    def _normalize_ng_state_for_config(self, ng_state):
        if not isinstance(ng_state, str):
            return ng_state

        try:
            parsed_state = json.loads(ng_state)
        except (TypeError, json.JSONDecodeError):
            return ng_state

        if isinstance(parsed_state, dict) and "value" in parsed_state:
            return parsed_state["value"]

        return parsed_state

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

        context = self._base_context(task_id=task_id)

        # if not is_authorized(request.user):
        #     logging.warning(f"Unauthorized requests from {request.user}.")
        #     return redirect(reverse("index"))

        if task_id is None:
            return self._render_inspect(request, context)

        try:
            task_df = client.get_task(task_id)
        except Exception as e:
            context["error"] = e
            return self._render_inspect(request, context)

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
        context["task_summary"] = self._build_task_summary(context)
        context["task_metadata_rows"] = self._build_task_metadata_rows(
            context["task_summary"]
        )
        return self._render_inspect(request, context)

    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        return redirect(reverse("inspect", kwargs={"task_id": task_id}))


class LineageView(DatastackMixin, View):
    def get(self, request, datastack=None, root_id=None, *args, **kwargs):
        return CellViewerView.as_view()(
            request,
            viewer_type="lineage",
            datastack=datastack,
            query_ids=root_id,
            *args,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        return CellViewerView.as_view()(request, *args, **kwargs)


class CellViewerView(DatastackMixin, View):
    template_name = "cell_viewer.html"
    valid_viewer_types = {"synapse", "nuclei", "lineage"}

    def _clean_timestamp(self, timestamp):
        if not timestamp or timestamp == "None":
            return "None"

        timestamp = str(timestamp).strip()
        if not timestamp or timestamp in settings.STATIC_NG_FILES:
            return "None"

        try:
            return datetime.strptime(timestamp, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError("Timestamp must use YYYY-MM-DD.")

    def _timestamp_input_value(self, timestamp):
        try:
            timestamp = self._clean_timestamp(timestamp)
        except ValueError:
            return ""

        return "" if timestamp == "None" else timestamp

    def _base_context(self, datastack=None, viewer_type="synapse"):
        datastack_name = self.get_datastack({"datastack": datastack})
        return {
            "viewer_type": viewer_type if viewer_type in self.valid_viewer_types else "synapse",
            "query_ids": "",
            "datastack": datastack_name,
            "datastacks": Datastack.objects.filter(enabled=True),
            "pre_synapses": "True",
            "post_synapses": "True",
            "cleft_layer": "True",
            "timestamp": "None",
            "timestamp_input_value": "",
            "ng_state": None,
            "error": None,
            "result_title": "",
            "result_headers": [],
            "result_rows": [],
            "ids_not_found": "",
            "copy_payload": "",
            "graph": "",
            "data": {"settings": queue_settings()},
            "cell_viewer_config": {
                "ngState": None,
                "viewerType": viewer_type,
                "urls": {"cellViewer": reverse("cell-viewer")},
            },
        }

    def _render(self, request, context):
        context["timestamp_input_value"] = self._timestamp_input_value(
            context.get("timestamp")
        )
        context["cell_viewer_config"] = {
            "ngState": context.get("ng_state"),
            "viewerType": context.get("viewer_type"),
            "urls": {"cellViewer": reverse("cell-viewer")},
        }
        return render(request, self.template_name, context)

    def get(
        self,
        request,
        viewer_type=None,
        datastack=None,
        query_ids=None,
        pre_synapses="True",
        post_synapses="True",
        cleft_layer="True",
        timestamp="None",
        *args,
        **kwargs,
    ):
        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        if query_ids in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{query_ids}", content_type="application/javascript"
            )
        if timestamp in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{timestamp}", content_type="application/javascript"
            )

        viewer_type = viewer_type if viewer_type in self.valid_viewer_types else "synapse"
        datastack_name = self.get_datastack({"datastack": datastack})
        context = self._base_context(datastack=datastack_name, viewer_type=viewer_type)
        try:
            timestamp = self._clean_timestamp(timestamp)
        except ValueError as e:
            context.update(
                {
                    "error": e,
                    "query_ids": query_ids or "",
                    "timestamp": "None",
                }
            )
            return self._render(request, context)

        if query_ids is None:
            return self._render(request, context)

        query_id_list = [x.strip() for x in query_ids.split(",") if x.strip()]
        flags = {
            "pre_synapses": pre_synapses,
            "post_synapses": post_synapses,
            "cleft_layer": cleft_layer,
            "timestamp": timestamp,
        }
        context.update(
            {
                "viewer_type": viewer_type,
                "query_ids": ",".join(query_id_list),
                "pre_synapses": pre_synapses,
                "post_synapses": post_synapses,
                "cleft_layer": cleft_layer,
                "timestamp": timestamp,
            }
        )

        try:
            result = construct_cell_viewer_state(
                viewer_type=viewer_type,
                ids=query_id_list,
                flags=flags,
                datastack=datastack_name,
            )
            context.update(
                {
                    "ng_state": result["ng_state"],
                    "result_title": result["table_title"],
                    "result_headers": result["table_headers"],
                    "result_rows": result["table_rows"],
                    "copy_payload": result["copy_payload"],
                    "ids_not_found": result["ids_not_found"],
                    "graph": result.get("graph", ""),
                }
            )
        except Exception as e:
            context["error"] = e

        return self._render(request, context)

    def post(self, request, *args, **kwargs):
        viewer_type = request.POST.get("viewer_type")
        if viewer_type not in self.valid_viewer_types:
            if request.POST.get("given_ids"):
                viewer_type = "nuclei"
            elif request.POST.get("root_id"):
                viewer_type = "lineage"
            else:
                viewer_type = "synapse"

        datastack = request.POST.get("datastack")
        query_ids = (
            request.POST.get("query_ids")
            or request.POST.get("root_ids")
            or request.POST.get("given_ids")
            or request.POST.get("root_id")
            or ""
        )
        query_ids = ",".join(
            query_id.strip() for query_id in query_ids.split(",") if query_id.strip()
        )

        if not query_ids:
            context = self._base_context(datastack=datastack, viewer_type=viewer_type)
            context["error"] = "Enter at least one ID."
            return self._render(request, context)

        if viewer_type == "lineage" and "," in query_ids:
            context = self._base_context(datastack=datastack, viewer_type=viewer_type)
            context.update(
                {
                    "error": "Lineage mode accepts one root ID.",
                    "query_ids": query_ids,
                }
            )
            return self._render(request, context)

        if viewer_type in ["nuclei", "lineage"]:
            return redirect(
                reverse(
                    "cell-viewer-query",
                    kwargs={
                        "viewer_type": viewer_type,
                        "datastack": datastack,
                        "query_ids": query_ids,
                    },
                )
            )

        timestamp = request.POST.get("timestamp")
        try:
            timestamp = self._clean_timestamp(timestamp)
        except ValueError as e:
            context = self._base_context(datastack=datastack, viewer_type=viewer_type)
            context.update(
                {
                    "error": e,
                    "query_ids": query_ids,
                    "timestamp": "None",
                }
            )
            return self._render(request, context)

        return redirect(
            reverse(
                "cell-viewer-synapse",
                kwargs={
                    "viewer_type": "synapse",
                    "datastack": datastack,
                    "query_ids": query_ids,
                    "pre_synapses": request.POST.get("pre_synapses", "False"),
                    "post_synapses": request.POST.get("post_synapses", "False"),
                    "cleft_layer": request.POST.get("cleft_layer", "False"),
                    "timestamp": timestamp,
                },
            )
        )


class SynapseView(CellViewerView):
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
        return super().get(
            request,
            viewer_type="synapse",
            datastack=datastack,
            query_ids=root_ids,
            pre_synapses=pre_synapses or "True",
            post_synapses=post_synapses or "True",
            cleft_layer=cleft_layer or "True",
            timestamp=timestamp or "None",
            *args,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class NucleiView(CellViewerView):
    def get(self, request, datastack=None, given_ids=None, *args, **kwargs):
        return super().get(
            request,
            viewer_type="nuclei",
            datastack=datastack,
            query_ids=given_ids,
            *args,
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
