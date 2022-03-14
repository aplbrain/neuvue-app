from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin 

from .models import Namespace

from neuvueclient import NeuvueQueue
import pandas as pd
import json

from .neuroglancer import (
    construct_proofreading_state, 
    construct_lineage_state_and_graph,
    construct_synapse_state,
    get_from_state_server, 
    post_to_state_server, 
    get_from_json,
    apply_state_config,
    refresh_ids
    )

from .analytics import user_stats
from .utils import utc_to_eastern, is_url, is_json, is_member

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)


class WorkspaceView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, namespace=None, **kwargs):
        # TODO:
        # This redirects NG static files.  Currently, NG redirects directly to root in their js
        # e.g tries to load /workspace/chunk_worker.bundle.js
        # This hacky solution works.
        if namespace in settings.STATIC_NG_FILES:
            return redirect(f'/static/workspace/{namespace}', content_type='application/javascript')

        session_task_count = request.session.get('session_task_count', 0)
        context = {
            'ng_state': {},
            'pcg_url': Namespace.objects.get(namespace = namespace).pcg_source,
            'task_id': '',
            'seg_id': '',
            'is_open': False,
            'tasks_available': True,
            'skipable': True,
            'instructions': '',
            'display_name': Namespace.objects.get(namespace = namespace).display_name,
            'submission_method': Namespace.objects.get(namespace = namespace).submission_method,
            'timeout': settings.TIMEOUT,
            'session_task_count' : session_task_count,
            'was_skipped':False,
        }

        if namespace is None:
            logging.debug("No namespace query provided.")
            # TODO: Redirect to task page for now, something went wrong...
            return redirect(reverse('tasks'))

        # Get the next task. If its open already display immediately.
        # TODO: Save current task to session.
        task_df = self.client.get_next_task(str(request.user), namespace)
        
        if not task_df:
            context['tasks_available'] = False
            pass

        else:
            if task_df['status'] == 'pending':

                self.client.patch_task(
                    task_df["_id"], 
                    status="open", 
                    overwrite_opened=not task_df.get('opened')
                    )
            
            # Update Context
            context['is_open'] = True
            context['task_id'] = task_df['_id']
            context['seg_id'] = task_df['seg_id']
            context['instructions'] = task_df['instructions']
            context['was_skipped'] = task_df['metadata'].get('skipped')
            if task_df['priority'] < 2:
                context['skipable'] = False
                
 
            # Construct NG URL from points or existing state
            # Dev Note: We always load ng state if one is available, overriding 
            # generating the state. However, config options can be applied after
            # a state is obtained.
            ng_state = task_df.get('ng_state')
    
            if ng_state:
                if is_url(ng_state):
                    logging.debug("Getting state from JSON State Server")
                    context['ng_state'] = get_from_state_server(ng_state)

                elif is_json(ng_state):
                    # NG State is already in JSON format
                    context['ng_state'] = get_from_json(ng_state)

            else:
                # Manually get the points for now, populate in client later.
                points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
                context['ng_state'] = construct_proofreading_state(task_df, points, return_as='json')

            # Apply configuration options.
            context['ng_state'] = apply_state_config(context['ng_state'], str(request.user))
            context['ng_state'] = refresh_ids(context['ng_state'], namespace)

        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        
        namespace = kwargs.get('namespace')
        namespace_obj = Namespace.objects.get(namespace = namespace)

        # Current task that is opened in this namespace.
        task_df = self.client.get_next_task(str(request.user), namespace)

        # All form submissions include button name and ng state
        button = request.POST.get('button')
        ng_state = request.POST.get('ngState')
        duration = int(request.POST.get('duration', 0))
        session_task_count = request.session.get('session_task_count', 0)
        ng_differ_stack = json.loads(request.POST.get('ngDifferStack', '[]'), strict=False)
        new_operation_ids = json.loads(request.POST.get('new_operation_ids', '[]'))
    
        try:
            ng_state = post_to_state_server(ng_state)
        except:
            logger.warning("Unable to post state to JSON State Server")
            
        tags = [tag.strip() for tag in set(request.POST.get('tags', '').split(',')) if tag]

        # Add operation ids to task metadata
        # Only if track_operation_ids is set to true at the namespace level
        # Make sure not to overwrite existing operation ids
        metadata = {}
        if new_operation_ids and namespace_obj.track_operation_ids:
            task_metadata = task_df['metadata']
            if 'operation_ids' in task_metadata: 
                metadata['operation_ids'] = task_metadata['operation_ids'] + new_operation_ids
            else:
                metadata['operation_ids'] = new_operation_ids

        if button == 'submit':
            logger.info('Submitting task')
            request.session['session_task_count'] = session_task_count +1
            # Update task data
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state,
                tags=tags,
                metadata=metadata)
            # Add new differ stack entry
            if ng_differ_stack != []:
                self.client.post_differ_stack(
                    task_df["_id"],
                    ng_differ_stack
                )
        
        elif button in ['yes', 'no', 'unsure', 'yesConditional', 'errorNearby']:
            logger.info('Submitting task')
            request.session['session_task_count'] = session_task_count +1
            metadata['decision'] = button
            # Update task data
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state,
                metadata=metadata,
                tags=tags)
            # Add new differ stack entry
            if ng_differ_stack != []:
                self.client.post_differ_stack(
                    task_df["_id"],
                    ng_differ_stack
                )
        
        elif button == 'skip':
            logger.info('Skipping task')
            metadata['skipped'] = True
            try:
                self.client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    priority=task_df['priority']-1, 
                    status="pending",
                    metadata=metadata,
                    ng_state=ng_state, 
                    tags=tags)
                # Add new differ stack entry
                if ng_differ_stack != []:
                    self.client.post_differ_stack(
                        task_df["_id"],
                        ng_differ_stack
                    )
            except Exception:
                logging.warning(f'Unable to lower priority for current task: {task_df["_id"]}')
                logging.warning(f'This task has reached the maximum number of skips.')
                metadata['skipped'] = True
                self.client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    status="pending",
                    metadata=metadata,
                    ng_state=ng_state, 
                    tags=tags)
        
        elif button == 'flag':
            logger.info('Flagging task')
            flag_reason = request.POST.get('flag')
            other_reason = request.POST.get('flag-other')
            
            metadata['flag_reason'] = flag_reason
            if other_reason:
                metadata['flag_other'] = other_reason
    
            request.session['session_task_count'] = session_task_count +1

            # Update task data
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="errored", 
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
                )
            # Add new differ stack entry
            if ng_differ_stack != []:
                self.client.post_differ_stack(
                    task_df["_id"],
                    ng_differ_stack
                )
        
        elif button == 'start':
            logger.info('Starting new task')
            if not task_df:
                logging.warning('Cannot start task, no tasks available.')
            else:
                self.client.patch_task(task_df["_id"], status="open")
            
        
        elif button == 'stop':
            logger.info('Stopping proofreading app')
            # Update task data
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                ng_state=ng_state,
                tags=tags,
                metadata=metadata)
            # Add new differ stack entry
            if ng_differ_stack != []:
                self.client.post_differ_stack(
                    task_df["_id"],
                    ng_differ_stack
                )
            return redirect(reverse('tasks'))
    
        return redirect(reverse('workspace', args=[namespace]))


class TaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)
        return super().dispatch(request, *args, **kwargs)

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
            context[namespace]["can_self_assign_tasks"] = is_member(request.user, self_assign_group)
            context[namespace]["max_pending_tasks_allowed"] = n_s.max_number_of_pending_tasks_per_user

        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        non_empty_namespace = 0

        for namespace in context.keys():
            context[namespace]['pending'], context[namespace]['closed'] = self._generate_tables(str(request.user), namespace)
            context[namespace]['total_closed'] = len(context[namespace]['closed'])
            context[namespace]['total_pending'] = len(context[namespace]['pending'])
            context[namespace]["total_tasks"] = context[namespace]['total_closed'] + context[namespace]['total_pending']
            if (context[namespace]["total_tasks"]):
                context[namespace]["start"] = non_empty_namespace*2
                context[namespace]["end"] = (non_empty_namespace*2)+2
                non_empty_namespace += 1

            context[namespace]['stats'] = user_stats(context[namespace]['closed'])
        
        
        # Reset session count when task page loads. This ensures session counts only increment
        # for one task type at a time
        request.session['session_task_count'] = 0

        return render(request, "tasks.html", {'data':context})

    def _generate_tables(self, username, namespace):
        tasks = self.client.get_tasks(sieve={
            "assignee": username, 
            "namespace": namespace,
        }, select=['seg_id', 'created', 'priority', 'status', 'opened', 'closed', 'duration'])
        
        tasks['task_id'] = tasks.index
        tasks['created'] = tasks['created'].apply(lambda x: utc_to_eastern(x))

        pending_tasks = tasks[tasks.status.isin(['pending', 'open'])].sort_values('created')
        closed_tasks = tasks[tasks.status.isin(['closed', 'errored'])].sort_values('closed', ascending=False)
        
            
        # Check if there are any NaNs in opened column
        # TODO: Fix this in the database side of things 
        if closed_tasks['opened'].isnull().values.any() or closed_tasks['closed'].isnull().values.any():
            default =  pd.to_datetime('1969-12-31')
            closed_tasks['opened'] = closed_tasks['opened'].fillna(default)
            closed_tasks['closed'] = closed_tasks['closed'].fillna(default)
    
        closed_tasks['opened'] = closed_tasks['opened'].apply(lambda x: utc_to_eastern(x))
        closed_tasks['closed'] = closed_tasks['closed'].apply(lambda x: utc_to_eastern(x))

        return pending_tasks.to_dict('records'), closed_tasks.to_dict('records')
    
    # This post endpoint does not redirect to another webpage, it returns a response that the view must handle.
    # Sorry for breaking form, but forcing django to be dynamic for this feature was the best solution
    def post(self, request, *args, **kwargs):
        # Pull information we need
        namespace = request.POST.get("namespace", "")
        namespace_obj = Namespace.objects.get(namespace = namespace)
        username = request.user.username
        num_tasks = namespace_obj.number_of_tasks_users_can_self_assign
        max_tasks = namespace_obj.max_number_of_pending_tasks_per_user

        # Get x unassigned tasks to assign. Return if none
        unassigned_tasks = self.client.get_tasks(
            sieve={"assignee": "unassigned", "namespace": namespace}, 
            limit=num_tasks, 
            return_states=False, 
            return_metadata=False
        )
        if len(unassigned_tasks) == 0:
            # TODO: Should we warn the user that no tasks are left in the queue?
            return HttpResponse("Unable to assign new tasks. No unassigned tasks left in queue.", content_type="text/plain")

        # Get tasks currently assigned to user to make sure we don't exceed the limit
        assigned_tasks = self.client.get_tasks(
            sieve={"assignee": username, "namespace": namespace, "status": ["pending", "open"]}, 
            return_states=False, 
            return_metadata=False
        )
        while ( len(unassigned_tasks) + len(assigned_tasks) ) > max_tasks:
            unassigned_tasks = unassigned_tasks.iloc[:-1 , :]

        # Assign the tasks
        ids = unassigned_tasks.index.tolist()
        for id in ids:
            self.client.patch_task(id, assignee=username)

        return HttpResponse()


class InspectTaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, task_id=None, *args, **kwargs):
        if task_id in settings.STATIC_NG_FILES:
            return redirect(f'/static/workspace/{task_id}', content_type='application/javascript')

        context = {
            "task_id": task_id,
            "ng_state": None,
            "error": None
        }

        if task_id is None:
            return render(request, "inspect.html", context)

        try:
            task_df = self.client.get_task(task_id)
        except Exception as e: 
            context['error'] = e
            return render(request, "inspect.html", context)
    
        namespace =  task_df['namespace']
        ng_state = task_df.get('ng_state')

        if ng_state:
            if is_url(ng_state):
                logging.debug("Getting state from JSON State Server")
                context['ng_state'] = get_from_state_server(ng_state)

            elif is_json(ng_state):
                # NG State is already in JSON format
                context['ng_state'] = get_from_json(ng_state)

        else:
            # Manually get the points for now, populate in client later.
            points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
            context['ng_state'] = construct_proofreading_state(task_df, points, return_as='json')

        context['task_id'] = task_df['_id']
        context['seg_id'] = task_df['seg_id']
        context['instructions'] = task_df['instructions']
        context['assignee'] = task_df['assignee']
        context['display_name'] = Namespace.objects.get(namespace = namespace).display_name
        context['pcg_url'] = Namespace.objects.get(namespace = namespace).pcg_source
        context['status'] =  task_df['status']
        if 'flag_reason' in task_df['metadata'].keys():
            context['flag_reason'] =  task_df['metadata']['flag_reason']
        
        metadata = task_df['metadata']
        if metadata.get('decision'):
            context['decision'] = metadata['decision']
        return render(request, "inspect.html", context)


    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        return redirect(reverse('inspect', kwargs={"task_id":task_id}))

class LineageView(View):
    def get(self, request, root_id=None, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(reverse('index'))

        if root_id in settings.STATIC_NG_FILES:
            return redirect(f'/static/workspace/{root_id}', content_type='application/javascript')

        context = {
            "root_id": root_id,
            "ng_state": None,
            "graph": None,
            "error": None
        }

        if root_id is None:
            return render(request, "lineage.html", context)

        try:
            context['ng_state'], context['graph'] = construct_lineage_state_and_graph(root_id)
        except Exception as e: 
            context['error'] = e
            return render(request, "lineage.html", context)
        return render(request, "lineage.html", context)


    def post(self, request, *args, **kwargs):
        root_id = request.POST.get("root_id")
        return redirect(reverse('lineage', kwargs={"root_id":root_id}))


class SynapseView(View):
    def get(self, request, root_id=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('index'))

        if root_id in settings.STATIC_NG_FILES:
            return redirect(f'/static/workspace/{root_id}', content_type='application/javascript')

        context = {
            "root_id": root_id,
            "ng_state": None,
            "synapse_stats": None,
            "error": None
        }

        if root_id is None:
            return render(request, "synapse.html", context)

        try:
            context['ng_state'], context['synapse_stats'] = construct_synapse_state(root_id)
        except Exception as e: 
            context['error'] = e
            return render(request, "synapse.html", context)
        return render(request, "synapse.html", context)


    def post(self, request, *args, **kwargs):
        root_id = request.POST.get("root_id")
        return redirect(reverse('synapse', kwargs={"root_id":root_id}))


#TODO: Move simple views to other file 
class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")

class AuthView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "auth_redirect.html")

class TokenView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "token.html", context={'code': request.GET.get('code')})