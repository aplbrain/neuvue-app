import json
import logging

from django.apps import apps
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from neuvue.client import client

from ..models import Namespace, UserProfile, ForcedChoiceButtonGroup, ForcedChoiceButton, NeuroglancerHost
from ..neuroglancer import (
    construct_proofreading_state,
    construct_url_from_existing,
    get_from_state_server,
    get_from_json,
    apply_state_config,
    refresh_ids,
)
from ..utils import is_url, is_json, is_authorized


# import the logging library
logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)
Config = apps.get_model("preferences", "Config")


class WorkspaceView(LoginRequiredMixin, View):
    def get(self, request, namespace=None, **kwargs):
        # TODO:
        # This redirects NG static files.  Currently, NG redirects directly to root in their js
        # e.g tries to load /workspace/chunk_worker.bundle.js
        # This hacky solution works.
        if namespace in settings.STATIC_NG_FILES:
            return redirect(
                f"/static/workspace/{namespace}", content_type="application/javascript"
            )

        session_task_count = request.session.get("session_task_count", 0)
        namespace_obj = Namespace.objects.get(namespace=namespace)
        submission_method = namespace_obj.submission_method
        context = {
            "ng_state": {},
            "ng_url": None,
            "pcg_url": namespace_obj.pcg_source,
            "task_id": "",
            "seg_id": "",
            "is_open": False,
            "tasks_available": True,
            "skipable": True if namespace_obj.decrement_priority > 0 else False,
            "instructions": "",
            "display_name": namespace_obj.display_name,
            "submission_method": submission_method,
            "session_task_count": session_task_count,
            "was_skipped": False,
            "show_slices": False,
            "namespace": namespace,
            "tags": "",
            "num_edits": 0,
            "track_selected_segments": namespace_obj.track_selected_segments,
        }

        forced_choice_buttons = ForcedChoiceButton.objects.filter(
            set_name=context.get("submission_method")
        ).all()
        if forced_choice_buttons:
            button_list = []
            for button in forced_choice_buttons:
                button_item = {
                    "display_name": getattr(button, "display_name"),
                    "submission_value": getattr(button, "submission_value"),
                    "button_color": getattr(button, "button_color"),
                    "button_color_active": getattr(button, "button_color_active"),
                    "hotkey": getattr(button, "hotkey"),
                }
                button_list.append(button_item)
            context["button_list"] = button_list

        button_group_obj = ForcedChoiceButtonGroup.objects.get(
            group_name=submission_method
        )
        context["submit_task_button"] = button_group_obj.submit_task_button

        number_of_selected_segments_expected = (
            button_group_obj.number_of_selected_segments_expected
        )
        if number_of_selected_segments_expected:
            context[
                "number_of_selected_segments_expected"
            ] = number_of_selected_segments_expected
        else:
            context["number_of_selected_segments_expected"] = None

        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        if namespace is None:
            logging.debug("No namespace query provided.")
            # TODO: Redirect to task page for now, something went wrong...
            return redirect(reverse("tasks"))

        # Get the next task. If its open already display immediately.
        # TODO: Save current task to session.
        task_df = client.get_next_task(str(request.user), namespace)

        if not task_df:
            context["tasks_available"] = False

        else:
            if task_df["status"] == "pending":

                client.patch_task(
                    task_df["_id"],
                    status="open",
                    overwrite_opened=not task_df.get("opened"),
                )

            # Update Context
            context["is_open"] = True
            context["task_id"] = task_df["_id"]
            context["seg_id"] = task_df["seg_id"]
            context["instructions"] = task_df["instructions"]
            context["was_skipped"] = task_df["metadata"].get("skipped")
            if task_df["metadata"].get("operation_ids"):
                context["num_edits"] = len(task_df["metadata"]["operation_ids"])
            if task_df.get("tags"):
                context["tags"] = ",".join(task_df["tags"])
            if task_df["priority"] < 2:
                context["skipable"] = False

            # Pass User configs to Neuroglancer
            try:
                config = Config.objects.filter(user=str(request.user)).order_by("-id")[0]
                context["show_slices"] = config.show_slices
            except Exception as e:
                logging.error(e)

            # Construct NG URL from points or existing state
            # Dev Note: We always load ng state if one is available, overriding
            # generating the state. However, config options can be applied after
            # a state is obtained.
            ng_state = task_df.get("ng_state")

            if ng_state:
                if is_url(ng_state):
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

            # Apply configuration options.
            context["ng_state"] = apply_state_config(
                context["ng_state"], str(request.user)
            )
            context["ng_state"] = refresh_ids(context["ng_state"], namespace)

            #############################      NG HOST      ########################################
            if namespace_obj.ng_host != NeuroglancerHost.NEUVUE:
                context['ng_url'] = construct_url_from_existing(
                    context['ng_state'], namespace_obj.ng_host
                )

            ############################# ALLOW TO REASSIGN ########################################
            # get user profile object
            userProfile, _ = UserProfile.objects.get_or_create(user=request.user)

            # determine if our user's highest level is novice, intermediate, or expert
            user_level = "novice"
            for ns in userProfile.intermediate_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "intermediate"
            for ns in userProfile.expert_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "expert"

            # get namespace object of task namespace
            namespace_obj = Namespace.objects.get(namespace=namespace)
            group_to_push_to = ""
            # for the appropriate user level (found above), get the group tasks will be pushed to for this namespace
            if user_level == "novice":
                group_to_push_to = namespace_obj.novice_push_to
            elif user_level == "intermediate":
                group_to_push_to = namespace_obj.intermediate_push_to
            else:
                group_to_push_to = namespace_obj.expert_push_to

            # determine if the user's group is allowed to reassign in this namespace
            if group_to_push_to == "Queue Tasks Not Allowed":
                context["allowed_to_reassign"] = False
            else:
                context["allowed_to_reassgin"] = True

            #######################################################################################

        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        namespace = kwargs.get("namespace")
        namespace_obj = Namespace.objects.get(namespace=namespace)

        # Current task that is opened in this namespace.
        task_df = client.get_next_task(str(request.user), namespace)

        # All form submissions include button name and ng state
        button = request.POST.get("button")
        ng_state = request.POST.get("ngState")
        duration = int(request.POST.get("duration", 0))
        tags = request.POST.get("tags")
        session_task_count = request.session.get("session_task_count", 0)
        ng_differ_stack = json.loads(
            request.POST.get("ngDifferStack", "[]"), strict=False
        )
        selected_segments = request.POST.get("selected_segments", "")

        # Parse tags
        if tags:
            tags = tags.split(",")
        else:
            tags = None

        # try:
        #     ng_state = post_to_state_server(ng_state)
        # except:
        #     logger.warning("Unable to post state to JSON State Server")

        # Add operation ids to task metadata
        # Only if track_operation_ids is set to true at the namespace level
        # Make sure not to overwrite existing operation ids
        metadata = {}

        # Add selected segments to task metadata
        # Only if track_selected_segments is set to true at the namespace level
        if selected_segments and namespace_obj.track_selected_segments:
            metadata["selected_segments"] = selected_segments.split(",")

        ### Forced Choice Button groups ###
        submission_method = namespace_obj.submission_method
        forced_choice_buttons = ForcedChoiceButton.objects.filter(
            set_name=submission_method
        ).all()

        if button == "submit":
            logger.info("Submitting task")
            request.session["session_task_count"] = session_task_count + 1
            # Update task data
            client.patch_task(
                task_df["_id"],
                duration=duration,
                status="closed",
                ng_state=ng_state,
                tags=tags,
                metadata=metadata,
            )
            # Add new differ stack entry
            if ng_differ_stack != []:
                client.post_differ_stack(task_df["_id"], ng_differ_stack)

        elif button in [x.submission_value for x in forced_choice_buttons]:
            logger.info("Submitting task")
            request.session["session_task_count"] = session_task_count + 1
            metadata["decision"] = button
            # Update task data
            client.patch_task(
                task_df["_id"],
                duration=duration,
                status="closed",
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
            )
            # Add new differ stack entry
            if ng_differ_stack != []:
                client.post_differ_stack(task_df["_id"], ng_differ_stack)

        elif button == "skip":
            logger.info("Skipping task")

            # keep track of the number of times a user skipped a task
            task_metadata = task_df["metadata"]
            if "skipped" in task_metadata.keys():
                num_skipped = task_metadata["skipped"]
                metadata["skipped"] = num_skipped + 1
            else:
                metadata["skipped"] = 1

            try:
                new_priority = task_df["priority"] - namespace_obj.decrement_priority
                if new_priority < 0: new_priority = 0
                client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    priority=new_priority,
                    status="pending",
                    metadata=metadata,
                    ng_state=ng_state,
                    tags=tags,
                )
                # Add new differ stack entry
                if ng_differ_stack != []:
                    client.post_differ_stack(task_df["_id"], ng_differ_stack)
            except Exception:
                logging.warning(
                    f'Unable to lower priority for current task: {task_df["_id"]}'
                )
                logging.warning(f"This task has reached the maximum number of skips.")
                client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    status="pending",
                    metadata=metadata,
                    ng_state=ng_state,
                )

        elif button == "flag":
            logger.info("Flagging task")
            flag_reason = request.POST.get("flag")
            other_reason = request.POST.get("flag-other")

            metadata["flag_reason"] = flag_reason
            if other_reason:
                metadata["flag_other"] = other_reason

            request.session["session_task_count"] = session_task_count + 1

            # Update task data
            client.patch_task(
                task_df["_id"],
                duration=duration,
                status="errored",
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
            )
            # Add new differ stack entry
            if ng_differ_stack != []:
                client.post_differ_stack(task_df["_id"], ng_differ_stack)
        elif button == "remove":
            # get user profile object
            userProfile = UserProfile.objects.get(user=request.user)

            # determine if our user's highest level is novice, intermediate, or expert
            user_level = "novice"
            for ns in userProfile.intermediate_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "intermediate"
            for ns in userProfile.expert_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "expert"

            # patch task to the correct group
            new_assignee = "novice_unassigned"
            # for the appropriate user level (found above), get the group tasks will be pushed to for this namespace
            if user_level == "novice":
                new_assignee = namespace_obj.novice_push_to
            elif user_level == "intermediate":
                new_assignee = namespace_obj.intermediate_push_to
            else:
                new_assignee = namespace_obj.expert_push_to

            # patch task to the new assignee
            current_priority = task_df["priority"]
            task_metadata = task_df["metadata"]
            num_skipped = 0
            if "skipped" in task_metadata.keys():
                num_skipped = task_metadata["skipped"]

            client.patch_task(
                task_df["_id"],
                assignee=new_assignee,
                status="pending",
                priority=current_priority + num_skipped,
                metadata={"skipped": 0},
            )

        elif button == "start":
            logger.info("Starting new task")
            if not task_df:
                logging.warning("Cannot start task, no tasks available.")
            else:
                client.patch_task(task_df["_id"], status="open")

        elif button == "stop":
            logger.info("Stopping proofreading app")
            # Update task data
            client.patch_task(
                task_df["_id"],
                duration=duration,
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
            )
            # Add new differ stack entry
            if ng_differ_stack != []:
                client.post_differ_stack(task_df["_id"], ng_differ_stack)
            return redirect(reverse("tasks"))

        return redirect(reverse("workspace", args=[namespace]))
