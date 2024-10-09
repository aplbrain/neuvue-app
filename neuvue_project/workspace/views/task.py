import logging
import pandas as pd

from django.http import HttpResponse
from django.apps import apps
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Namespace, UserProfile

from neuvue.client import client

from ..analytics import create_stats_table
from ..utils import utc_to_eastern, is_member, is_authorized


# import the logging library
logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)


class TaskView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {}
        self_assign_group = "Can self assign tasks"

        for i, n_s in enumerate(Namespace.objects.filter(namespace_enabled=True)):
            namespace = n_s.namespace
            logging.debug(f"Loading data for namespace {namespace}.")
            context[namespace] = {}
            context[namespace]["display_name"] = n_s.display_name
            context[namespace]["ng_link_type"] = n_s.ng_link_type
            context[namespace]["pcg_source"] = n_s.pcg_source
            context[namespace]["img_source"] = n_s.img_source
            context[namespace]["pending"] = []
            context[namespace]["closed"] = []
            context[namespace]["total_pending"] = 0
            context[namespace]["total_closed"] = 0
            context[namespace]["total_tasks"] = 0
            context[namespace]["start"] = ""
            context[namespace]["end"] = ""
            context[namespace]["can_self_assign_tasks"] = is_member(
                request.user, self_assign_group
            )
            context[namespace][
                "max_pending_tasks_allowed"
            ] = n_s.max_number_of_pending_tasks_per_user
            context[namespace]["submission_method"] = str(n_s.submission_method)

            # get user profile
            userProfile, _ = UserProfile.objects.get_or_create(user=request.user)
            namespace_name = n_s.namespace

            # get user level for each enabled namespace
            user_level = "novice"
            for ns in userProfile.intermediate_namespaces.all():
                if ns.namespace == namespace_name:
                    user_level = "intermediate"
            for ns in userProfile.expert_namespaces.all():
                if ns.namespace == namespace_name:
                    user_level = "expert"

            ## get if user can unassign tasks in this namespace
            namespace_obj = Namespace.objects.get(namespace=namespace)
            group_to_push_to = ""
            if user_level == "novice":
                group_to_push_to = namespace_obj.novice_push_to
            elif user_level == "intermediate":
                group_to_push_to = namespace_obj.intermediate_push_to
            else:
                group_to_push_to = namespace_obj.expert_push_to

            if group_to_push_to == "Queue Tasks Not Allowed":
                context[namespace]["can_unassign_tasks"] = False
            else:
                context[namespace]["can_unassign_tasks"] = True

        if not is_authorized(request.user):
            logging.warning(f"Unauthorized requests from {request.user}.")
            return redirect(reverse("index"))

        pending_tasks = client.get_tasks(
            sieve={"status": ["open", "pending"], "assignee": str(request.user)},
            select=[
                "seg_id",
                "namespace",
                "status",
                "created",
                "priority",
                "opened",
                "metadata",
            ],
        )

        closed_tasks = client.get_tasks(
            sieve={
                "status": ["closed", "errored"],
                "assignee": str(request.user),
            },
            select=[
                "seg_id",
                "namespace",
                "status",
                "opened",
                "closed",
                "duration",
                "tags",
            ],
        )

        for namespace in context.keys():
            namespace_pending_tasks = pending_tasks[
                pending_tasks["namespace"] == namespace
            ]
            namespace_closed_tasks = closed_tasks[
                closed_tasks["namespace"] == namespace
            ]
            (
                context[namespace]["pending"],
                context[namespace]["closed"],
            ) = self._generate_tables(namespace_pending_tasks, namespace_closed_tasks)
            context[namespace]["total_closed"] = len(context[namespace]["closed"])
            context[namespace]["total_pending"] = len(context[namespace]["pending"])
            context[namespace]["total_tasks"] = (
                context[namespace]["total_closed"] + context[namespace]["total_pending"]
            )

        # Reorder context dict by total pending tasks (descending order)
        context = dict(
            sorted(context.items(), key=lambda x: x[1]["total_pending"], reverse=True)
        )

        # Provide table index
        non_empty_namespace = 0
        for namespace in context.keys():
            if context[namespace]["total_tasks"]:
                context[namespace]["start"] = non_empty_namespace * 2
                context[namespace]["end"] = (non_empty_namespace * 2) + 2
                non_empty_namespace += 1

        # Reset session count when task page loads. This ensures session counts only increment
        # for one task type at a time
        request.session["session_task_count"] = 0

        # create settings and context dicts
        settings_dict = {"SANDBOX_ID": settings.SANDBOX_ID}
        daily_changelog, full_changelog = create_stats_table(
            pending_tasks, closed_tasks
        )
        data_dict = {
            "settings": settings_dict,
            "namespaces": context,
            "daily_changelog": daily_changelog,
            "full_changelog": full_changelog,
        }

        return render(request, "tasks.html", {"data": data_dict})

    def _generate_tables(self, pending_tasks, closed_tasks):

        pending_tasks = pending_tasks.rename_axis("task_id").reset_index()
        closed_tasks = closed_tasks.rename_axis("task_id").reset_index()

        metadata = pending_tasks["metadata"].values
        skipped = []
        for data in metadata:
            if "skipped" in data.keys():
                skipped.append(int(data["skipped"]))
            else:
                skipped.append(0)

        pending_tasks["skipped"] = skipped

        # Sort the tasks
        pending_tasks = pending_tasks.sort_values(
            by=["priority", "created"], ascending=[False, True]
        )
        closed_tasks = closed_tasks.sort_values("closed", ascending=False)

        # Check if there are any NaNs in opened column
        # TODO: Fix this in the database side of things
        if (
            closed_tasks["opened"].isnull().values.any()
            or closed_tasks["closed"].isnull().values.any()
        ):
            default = pd.to_datetime("1969-12-31")
            closed_tasks["opened"] = closed_tasks["opened"].fillna(default)
            closed_tasks["closed"] = closed_tasks["closed"].fillna(default)

        # Convert timepoints to eastern
        pending_tasks["created"] = pending_tasks["created"].apply(
            lambda x: utc_to_eastern(x)
        )
        closed_tasks["opened"] = closed_tasks["opened"].apply(
            lambda x: utc_to_eastern(x)
        )
        closed_tasks["closed"] = closed_tasks["closed"].apply(
            lambda x: utc_to_eastern(x)
        )

        return pending_tasks.to_dict("records"), closed_tasks.to_dict("records")

    # This post endpoint does not redirect to another webpage, it returns a response that the view must handle.
    # Sorry for breaking form, but forcing django to be dynamic for this feature was the best solution
    def post(self, request, *args, **kwargs):
        # Pull information we need
        namespace = request.POST.get("namespace", "")
        namespace_obj = Namespace.objects.get(namespace=namespace)
        username = request.user.username
        num_tasks = namespace_obj.number_of_tasks_users_can_self_assign
        max_tasks = namespace_obj.max_number_of_pending_tasks_per_user

        # Dev Note: Below is the logic for handling re-assignment of tasks. User levels default to novice and
        # can be overridden by the user profile in the admin page. How levels affect what group the namespace
        # belongs to depends on how the namespace configures the push to and pull from attributes.
        # By default, namespaces do not allow for reassignment.

        # determine if our user's highest level is novice, intermediate, or expert
        userProfile = UserProfile.objects.get(user=request.user)
        user_level = "novice"
        for ns in userProfile.intermediate_namespaces.all():
            if namespace == ns.namespace:
                user_level = "intermediate"
        for ns in userProfile.expert_namespaces.all():
            if namespace == ns.namespace:
                user_level = "expert"

        # for the appropriate user level (found above), get the group tasks will be pushed to for this namespace
        if user_level == "novice":
            group_to_push_to = namespace_obj.novice_push_to
            group_to_pull_from = namespace_obj.novice_pull_from
        elif user_level == "intermediate":
            group_to_push_to = namespace_obj.intermediate_push_to
            group_to_pull_from = namespace_obj.intermediate_pull_from
        else:
            group_to_push_to = namespace_obj.expert_push_to
            group_to_pull_from = namespace_obj.expert_pull_from

        if "reassignTasks" in request.POST.keys():
            # determine if our user's highest level is novice, intermediate, or expert
            user_level = "novice"
            for ns in userProfile.intermediate_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "intermediate"
            for ns in userProfile.expert_namespaces.all():
                if namespace == ns.namespace:
                    user_level = "expert"

            # determine if the user's group is allowed to reassign in this namespace
            if group_to_push_to == "Queue Tasks Not Allowed":
                return HttpResponse(
                    "You do not have permission to reassign tasks in this namespace.",
                    content_type="text/plain",
                )
            else:
                # get all the users tasks in this namespace
                # run through all of them to see if they have been skipped
                # if they've been skipped, reassign to the correct group with the appropriate priority
                tasks = client.get_tasks(
                    sieve={
                        "assignee": username,
                        "namespace": namespace,
                    },
                    select=["metadata", "priority"],
                )

                tasks["task_id"] = tasks.index

                # iterate through tasks, check if the task has been skipped, reassign to appropriate bucket
                reassign_count = 0
                for i in range(0, len(tasks)):
                    row = tasks.iloc[i]
                    metadata = row["metadata"]
                    skipped_keyword = "skipped"
                    if (skipped_keyword in metadata.keys()) and (
                        metadata[skipped_keyword] > 0
                    ):
                        original_priority = row["priority"] + metadata[skipped_keyword]
                        client.patch_task(
                            row["task_id"],
                            assignee=group_to_push_to,
                            status="pending",
                            priority=int(original_priority),
                            metadata={"skipped": 0},
                        )
                        reassign_count += 1

                http_message = "Reassigned {} skipped tasks".format(reassign_count)
                if reassign_count == 0:
                    http_message = "You did not have any skipped tasks in your queue. No tasks reassigned."

                return HttpResponse(http_message, content_type="text/plain")

        else:
            # Get x unassigned tasks to assign. Return if none
            unassigned_tasks = client.get_tasks(
                sieve={"assignee": group_to_pull_from, "namespace": namespace},
                limit=num_tasks,
                select=["_id"],
                sort="-priority"
            )
            if len(unassigned_tasks) == 0:
                # Warn the user that no tasks are left in the queue
                return HttpResponse(
                    "Unable to assign new tasks. No unassigned tasks left in queue.",
                    content_type="text/plain",
                )

            # Get tasks currently assigned to user to make sure we don't exceed the limit
            assigned_tasks = client.get_tasks(
                sieve={
                    "assignee": username,
                    "namespace": namespace,
                    "status": ["pending", "open"],
                },
                select=["_id"],
            )
            while (len(unassigned_tasks) + len(assigned_tasks)) > max_tasks:
                unassigned_tasks = unassigned_tasks.iloc[:-1, :]

            # Assign the tasks
            ids = unassigned_tasks.index.tolist()
            for id in ids:
                client.patch_task(id, assignee=username)

            return HttpResponse()
