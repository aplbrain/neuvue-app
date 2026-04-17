import logging
from pathlib import Path
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.views.generic import TemplateView
from django.conf import settings
from neuvue.client import client

from ..models import Namespace, NeuroglancerHost, ImageChoices
from ..neuroglancer import (
    construct_proofreading_state,
    construct_lineage_state_and_graph,
    construct_synapse_state,
    construct_nuclei_state,
    get_from_state_server,
    get_from_json,
    construct_url_from_existing,
    construct_task_generation_proofreading_state,
)
from ..utils import is_url, is_json, is_authorized
from ..forms import TaskGenerationForm

# import the logging library

logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)


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


class TaskGenerationSuccessView(TemplateView):
    template_name = "task-generation-success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ns = kwargs["namespace"]
        relpath = f"task_generation/{ns}.csv"
        context["namespace"] = ns
        context["csv_url"] = settings.MEDIA_URL + relpath
        csv_path = Path(settings.MEDIA_ROOT) / relpath
        try:
            context["csv_text"] = csv_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            context["csv_text"] = ""
        return context


class GenerateTasksView(View):
    # Form fields that do not take default rendering
    skip_fields = [
        "seg_table_csv",
        "segmentation_layers",
        "em_zoom",
        "resolution",
        "alpha_selected",
        "alpha_3d",
        "img_source_other_name",
        "img_source_other_url",
        "pcg_source_other_name",
        "pcg_source_other_url",
    ]

    def get(self, request, *args, **kwargs):
        form = TaskGenerationForm(request.POST)
        return render(
            request,
            "task-generation.html",
            {"form": form, "skip_fields": self.skip_fields},
        )

    def post(self, request, *args, **kwargs):
        form = TaskGenerationForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "task-generation.html",
                {"form": form, "skip_fields": self.skip_fields},
            )
        try:
            namespace = form.save(commit=True)
            # namespace.save()
            # Save optional extra fields
            # resolution = form.cleaned_data.get('resolution')
            img_value = (form.cleaned_data.get("img_source") or "").strip()

            if img_value == ImageChoices.OTHER:
                img_layer = {
                    "name": (
                        form.cleaned_data.get("img_source_other_name") or ""
                    ).strip(),
                    "source": (
                        form.cleaned_data.get("img_source_other_url") or ""
                    ).strip(),
                }
            else:
                choice_label = dict(form.fields["img_source"].choices).get(
                    img_value, ""
                )
                img_layer = {
                    "name": (choice_label or "").strip(),
                    "source": img_value,
                }

            df = form.cleaned_data["seg_table_df"].copy()
            # POST states to server and get links
            df[["state_url", "ng_state"]] = df.apply(
                lambda row: construct_task_generation_proofreading_state(
                    row.seg_id,
                    [row.x, row.y, row.z],
                    namespace=namespace,
                    img_layer=img_layer,
                    seg_layer_list=form.cleaned_data.get(
                        "segmentation_layers_list", []
                    ),
                    segmentation_view_options={
                        "alpha_selected": form.cleaned_data.get("alpha_selected"),
                        "alpha_3d": form.cleaned_data.get("alpha_3d"),
                    },
                    zoom_image=form.cleaned_data.get("em_zoom", 20),
                ),
                axis=1,
                result_type="expand",
            )

            # Save CSV to MEDIA_ROOT/task_generation/<namespace>.csv
            out_dir = Path(settings.MEDIA_ROOT) / "task_generation"
            out_dir.mkdir(parents=True, exist_ok=True)
            csv_path = out_dir / f"{namespace.namespace}.csv"
            df.to_csv(csv_path, index=False)

            # Go to success page that shows a copy/paste block + download link of the created states
            return redirect("task-generation-success", namespace=namespace.namespace)
        except Exception as e:
            # Return form with error statement
            form.add_error(None, str(e))
            return render(
                request,
                "task-generation.html",
                {"form": form, "skip_fields": self.skip_fields},
            )
