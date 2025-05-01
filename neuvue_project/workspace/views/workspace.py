import json
import logging

from django.apps import apps
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse

from neuvue.client import client

from ..models import (
    Namespace,
    UserProfile,
    ForcedChoiceButtonGroup,
    ForcedChoiceButton,
    NeuroglancerHost
)
from ..neuroglancer import (
    construct_proofreading_state,
    construct_url_from_existing,
    get_from_state_server,
    get_from_json,
    apply_state_config,
    refresh_ids,
    post_to_state_server
)
from ..utils import is_url, is_json, is_authorized, get_or_create_public_taskbucket


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
                f"/static/{request.path.split('/')[1]}/{namespace}",
                content_type="application/javascript",
            )

        session_task_count = request.session.get("session_task_count", 0)
        namespace_obj = Namespace.objects.get(namespace=namespace)
        submission_method = namespace_obj.submission_method
        context = {
            "ng_state": {},
            "ng_url": None,
            "ng_host": namespace_obj.ng_host,
            "pcg_url": namespace_obj.pcg_source,
            "task_id": "",
            "seg_id": "",
            "is_open": False,
            "tasks_available": True,
            "skippable": True if namespace_obj.decrement_priority > 0 else False,
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
            "ng_state_plugin": None
        }

        if  namespace_obj.ng_state_plugin:
            context["ng_state_plugin"] = namespace_obj.ng_state_plugin.name

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

        if is_authorized(request.user):
            assignee = str(request.user)
        else:
            assignee = get_or_create_public_taskbucket().bucket_assignee

        if namespace is None:
            logging.debug("No namespace query provided.")
            # TODO: Redirect to task page for now, something went wrong...
            return redirect(reverse("tasks"))

        # Get the next task. If its open already display immediately.
        # TODO: Save current task to session.
        task_df = client.get_next_task(assignee, namespace)

        if not task_df:
            context["tasks_available"] = False

        else:
            if task_df["status"] == "pending":

                client.patch_task(
                    task_df["_id"],
                    str(request.user),
                    status="open",
                    assignee=str(request.user),
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
                context["skippable"] = False

            # Pass User configs to Neuroglancer
            try:
                config = Config.objects.filter(user=str(request.user)).order_by("-id")[
                    0
                ]
                context["show_slices"] = config.show_slices
            except Exception as e:
                logging.error(e)

            # Construct NG URL from points or existing state
            # Dev Note: We always load ng state if one is available, overriding
            # generating the state. However, config options can be applied after
            # a state is obtained.
            ng_state = task_df.get("ng_state")

            if ng_state:
                if is_url(ng_state.replace("middleauth+", "")):
                    if namespace_obj.ng_host not in [NeuroglancerHost.NEUVUE, NeuroglancerHost.SPELUNKER]:
                        # Assume its a url to json state
                        context["ng_state"] = ng_state
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

            #############################      NG HOST      ########################################
            # NOTE: State configs are only applied to neuvue NG states. If using an iframe or Spelunker
            # url, we just load it as is.
            if namespace_obj.ng_host in [NeuroglancerHost.NEUVUE]:
                # TODO: Apply middleauth config to spelunker states
                context["ng_state"] = apply_state_config(
                    context["ng_state"], str(request.user)
                )
                context["ng_state"] = refresh_ids(context["ng_state"], namespace)

            elif namespace_obj.ng_host in [NeuroglancerHost.SPELUNKER]:
                # TODO: Add Spelunker NG configuration here
                pass
            else:
                context["ng_url"] = construct_url_from_existing(
                    context["ng_state"], namespace_obj.ng_host
                )

            ############################# ALLOW TO REASSIGN ########################################
            # get user profile object
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            namespace_obj = Namespace.objects.get(namespace=namespace)
            
            user_push_rule = user_profile.namespace_rule.filter(
                namespace=namespace_obj, action="push"
            ).first()

            # If user has a push rule, use it; otherwise fallback to the default push rule
            if user_push_rule:
                push_bucket_assignee = user_push_rule.task_bucket.bucket_assignee
            elif namespace_obj.default_push_rule:
                push_bucket_assignee = namespace_obj.default_push_rule.task_bucket.bucket_assignee
            else:
                push_bucket_assignee = None

            # If no valid push bucket, user cannot unassign tasks
            context["allowed_to_reassign"] = bool(push_bucket_assignee)
            #######################################################################################

        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        namespace = kwargs.get("namespace")
        namespace_obj = Namespace.objects.get(namespace=namespace)

        # Current task that is opened in this namespace.
        task_df = client.get_task(request.POST.get("taskId"))

        # All form submissions include button name and ng state
        button = request.POST.get("button")
        ng_state = request.POST.get("ngState", task_df["ng_state"])
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

        try:
            ng_state = post_to_state_server(ng_state, public = namespace_obj.ng_host != NeuroglancerHost.NEUVUE)
        except:
            logger.warning("Unable to post state to JSON State Server")

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

        if namespace_obj.is_demo:
            logger.info("User took action on a demo task. Patching priority only.")
            new_priority = task_df["priority"] - namespace_obj.decrement_priority
            try:
                client.patch_task(
                    task_df["_id"],
                    priority=new_priority
                )
            except Exception:
                logging.warning(
                    f'Unable to lower priority for current task: {task_df["_id"]}'
                )
                logging.warning(f"This task has reached the maximum number of skips.")
        elif button == "submit":
            logger.info("Submitting task")
            request.session["session_task_count"] = session_task_count + 1
            # Update task data
            client.patch_task(
                task_df["_id"],
                str(request.user),
                duration=duration,
                status="closed",
                ng_state=ng_state,
                tags=tags,
                metadata=metadata,
                assignee=str(request.user)
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
                str(request.user),
                duration=duration,
                status="closed",
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
                assignee=str(request.user)
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
                if new_priority < 0:
                    new_priority = 0
                client.patch_task(
                    task_df["_id"],
                    str(request.user),
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
                    str(request.user),
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
                str(request.user),
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
            # Fetch the user's profile and see if they have a custom "push" rule for this namespace
            user_profile = UserProfile.objects.get(user=request.user)
            user_push_rule = user_profile.namespace_rule.filter(
                namespace=namespace_obj, 
                action="push"
            ).first()

            # If user has a specific push rule, use it; otherwise fall back to namespace's default
            if user_push_rule:
                new_assignee = user_push_rule.task_bucket.bucket_assignee
            elif namespace_obj.default_push_rule:
                new_assignee = namespace_obj.default_push_rule.task_bucket.bucket_assignee
            else:
                return HttpResponse(
                    "You do not have permission to remove tasks from this queue. No push rule found.",
                    content_type="text/plain",
                )

            # Use the existing logic to patch the task with the new assignee
            current_priority = task_df["priority"]
            task_metadata = task_df["metadata"]
            num_skipped = task_metadata.get("skipped", 0)

            client.patch_task(
                task_df["_id"],
                str(request.user),
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
                str(request.user),
                duration=duration,
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
            )
            # Add new differ stack entry
            if ng_differ_stack != []:
                client.post_differ_stack(task_df["_id"], ng_differ_stack)
            return redirect(reverse("tasks"))
        else:
            logging.error(f"Invalid button submission: {button}")

        #### REDIRECT BACK TO WORKSPACE
        if namespace_obj.ng_host == NeuroglancerHost.SPELUNKER:
            return redirect(reverse("spelunker-workspace", args=[namespace]))
        else:
            return redirect(reverse("workspace", args=[namespace]))
