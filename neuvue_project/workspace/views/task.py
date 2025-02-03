import logging
import pandas as pd

from django.http import HttpResponse
from django.apps import apps
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Namespace, UserProfile, TaskBucket

from neuvue.client import client

from ..analytics import create_stats_table
from ..utils import utc_to_eastern, is_member, is_authorized, get_or_create_public_taskbucket


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
            context[namespace]["ng_host"] = n_s.ng_host
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

            # Try to find a user-specific push rule for this namespace
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            user_push_rule = user_profile.namespace_rule.filter(
                namespace=n_s, action="push"
            ).first()

            # If user has a push rule, use it; otherwise fallback to the default push rule
            if user_push_rule:
                push_bucket_assignee = user_push_rule.task_bucket.bucket_assignee
            elif n_s.default_push_rule:
                push_bucket_assignee = n_s.default_push_rule.task_bucket.bucket_assignee
            else:
                push_bucket_assignee = None

            # If no valid push bucket, user cannot unassign tasks
            if push_bucket_assignee:
                context[namespace]["can_unassign_tasks"] = True
            else:
                context[namespace]["can_unassign_tasks"] = False


        if is_authorized(request.user):
            assignee = str(request.user)
        else:
            assignee = get_or_create_public_taskbucket().bucket_assignee
            # logging.warning(f"Unauthorized requests from {request.user}.")
            # return redirect(reverse("index"))

        pending_tasks = client.get_tasks(
            sieve={"status": ["open", "pending"], "assignee": assignee},
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
        settings_dict = {
            "SANDBOX_ID": settings.SANDBOX_ID,
            "is_authorized": is_authorized(request.user)
        }
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

        user_profile = UserProfile.objects.get(user=request.user)
        
        
        # -----------------------------------------
        # 2. Get PULL bucket (from either user rule or namespace default)
        # -----------------------------------------
        # Check if user has a custom rule for pulling in this namespace
        user_pull_rule = user_profile.namespace_rule.filter(
            namespace=namespace_obj, action="pull"
        ).first()

        if user_pull_rule:
            pull_bucket_assignee = user_pull_rule.task_bucket.bucket_assignee
        else:
            # If no user-specific rule, use the namespace default pull rule (if any)
            if namespace_obj.default_pull_rule:
                pull_bucket_assignee = namespace_obj.default_pull_rule.task_bucket.bucket_assignee
            else:
                pull_bucket_assignee = None  

        # -----------------------------------------
        # 3. Get PUSH bucket (from either user rule or namespace default)
        # -----------------------------------------
        user_push_rule = user_profile.namespace_rule.filter(
            namespace=namespace_obj, action="push"
        ).first()

        if user_push_rule:
            push_bucket_assignee = user_push_rule.task_bucket.bucket_assignee
        else:
            if namespace_obj.default_push_rule:
                push_bucket_assignee = namespace_obj.default_push_rule.task_bucket.bucket_assignee
            else:
                push_bucket_assignee = None  

        # -----------------------------------------
        # 4. Handle "reassignTasks"
        # -----------------------------------------
        if "reassignTasks" in request.POST:
            # If push_bucket_assignee is None, treat it like "no permission"
            if not push_bucket_assignee:
                return HttpResponse(
                    "You do not have permission to reassign tasks in this namespace.",
                    content_type="text/plain",
                )

            # Gather all tasks assigned to current user in this namespace
            tasks = client.get_tasks(
                sieve={
                    "assignee": username,
                    "namespace": namespace,
                },
                select=["metadata", "priority"],
            )
            tasks["task_id"] = tasks.index

            # Reassign any "skipped" tasks
            reassign_count = 0
            for _, row in tasks.iterrows():
                metadata = row["metadata"]
                if "skipped" in metadata and metadata["skipped"] > 0:
                    original_priority = row["priority"] + metadata["skipped"]
                    client.patch_task(
                        row["task_id"],
                        assignee=push_bucket_assignee,
                        status="pending",
                        priority=int(original_priority),
                        metadata={"skipped": 0},
                    )
                    reassign_count += 1

            if reassign_count == 0:
                http_message = "You did not have any skipped tasks in your queue. No tasks reassigned."
            else:
                http_message = f"Reassigned {reassign_count} skipped tasks."

            return HttpResponse(http_message, content_type="text/plain")

        # -----------------------------------------
        # 5. Otherwise, user wants to PULL tasks for themselves
        # -----------------------------------------
        # If pull_bucket_assignee is None, treat as no tasks available
        if not pull_bucket_assignee:
            return HttpResponse(
                "Unable to assign new tasks. No configured pull bucket for this namespace.",
                content_type="text/plain",
            )

        # Get up to `num_tasks` tasks from the designated pull bucket
        unassigned_tasks = client.get_tasks(
            sieve={"assignee": pull_bucket_assignee, "namespace": namespace},
            limit=num_tasks,
            select=["_id"],
            sort="-priority",
        )
        if len(unassigned_tasks) == 0:
            return HttpResponse(
                "Unable to assign new tasks. No unassigned tasks left in queue.",
                content_type="text/plain",
            )

        # Check how many tasks the user already has so we don't exceed `max_tasks`
        assigned_tasks = client.get_tasks(
            sieve={
                "assignee": username,
                "namespace": namespace,
                "status": ["pending", "open"],
            },
            select=["_id"],
        )

        # Make sure we don't exceed the user's max number
        while (len(unassigned_tasks) + len(assigned_tasks)) > max_tasks:
            unassigned_tasks = unassigned_tasks.iloc[:-1, :]

        # Assign the tasks to the user
        ids = unassigned_tasks.index.tolist()
        for task_id in ids:
            client.patch_task(task_id, assignee=username)

        return HttpResponse()
