from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Namespace

from neuvueclient import NeuvueQueue
import numpy as np
import pandas as pd
import json

from .neuroglancer import construct_proofreading_state, construct_url_from_existing
from .analytics import user_stats
from .utils import utc_to_eastern

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)

class WorkspaceView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, namespace=None, **kwargs):
        # TODO:
        # This redirects NG static files.  Currently, NG redirects directly to root in their js
        # e.g tries to load /workspace/chunk_worker.bundle.js
        # This hacky solution works.
        if namespace in settings.STATIC_NG_FILES:
            return redirect(f'/static/workspace/{namespace}', content_type='application/javascript')

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
            'timeout': settings.TIMEOUT
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
                self.client.patch_task(task_df["_id"], status="open")
            
            # Update Context
            context['is_open'] = True
            context['task_id'] = task_df['_id']
            context['seg_id'] = task_df['seg_id']
            context['instructions'] = task_df['instructions']
            if task_df['priority'] < 2:
                context['skipable'] = False
 
            # Construct NG URL from points or existing state
            try:
                ng_state = json.loads(task_df.get('ng_state'))
            except Exception as e:
                logging.warning(f'Unable to pull ng_state for task: {e}')
                ng_state = None 
    
            if ng_state:
                if ng_state.get('value'):
                    ng_state = ng_state['value']
                context['ng_state'] = json.dumps(ng_state)
            else:
                # Manually get the points for now, populate in client later.
                points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
                context['ng_state'] = construct_proofreading_state(task_df, points, return_as='json')
        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        
        namespace = kwargs.get('namespace')

        # Current task that is opened in this namespace.
        task_df = self.client.get_next_task(str(request.user), namespace)

        # All form submissions include button name and ng state
        button = request.POST.get('button')
        ng_state = request.POST.get('ngState')
        duration = int(request.POST.get('duration', 0))
        tags = [tag.strip() for tag in set(request.POST.get('tags', '').split(',')) if tag]
        if button == 'submit':
            logger.debug('Submitting task')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state,
                tags=tags)
        
        elif button in ['yes', 'no', 'unsure', 'yesConditional', 'errorNearby']:
            logger.debug('Submitting task')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state,
                metadata={
                    'decision': button
                },
                tags=tags)
        
        elif button == 'skip':
            logger.debug('Skipping task')
            try:
                self.client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    priority=task_df['priority']-1, 
                    status="pending",
                    metadata={'skipped': True},
                    tags=tags)
            except Exception:
                logging.warning(f'Unable to lower priority for current task: {task_df["_id"]}')
                logging.warning(f'This task has reached the maximum number of skips.')
                self.client.patch_task(
                    task_df["_id"],
                    duration=duration,
                    status="pending",
                    metadata={'skipped': True},
                    tags=tags)
        
        elif button == 'flag':
            logger.debug('Flagging task')
            flag_reason = request.POST.get('flag')
            other_reason = request.POST.get('flag-other')
            metadata = {'flag_reason': flag_reason if flag_reason else other_reason}

            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="errored", 
                ng_state=ng_state,
                metadata=metadata,
                tags=tags,
                )
        
        elif button == 'start':
            logger.debug('Starting new task')
            if not task_df:
                logging.warning('Cannot start task, no tasks available.')
            else:
                self.client.patch_task(task_df["_id"], status="open")
            
        
        elif button == 'stop':
            logger.debug('Stopping proofreading app')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                ng_state=ng_state,
                tags=tags)
            return redirect(reverse('tasks'))
    
        return redirect(reverse('workspace', args=[namespace]))


class TaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {}

        for i, n_s in enumerate(Namespace.objects.all()):
            namespace = n_s.namespace
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

        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        non_empty_namespace = 0

        for namespace in context.keys():
            context[namespace]['pending'] = self._generate_table('pending', str(request.user), namespace)
            context[namespace]['closed'] = self._generate_table('closed', str(request.user), namespace)
            context[namespace]['total_closed'] = len(context[namespace]['closed'])
            context[namespace]['total_pending'] = len(context[namespace]['pending'])
            context[namespace]["total_tasks"] = context[namespace]['total_closed'] + context[namespace]['total_pending']
            if (context[namespace]["total_tasks"]):
                context[namespace]["start"] = non_empty_namespace*2
                context[namespace]["end"] = (non_empty_namespace*2)+2
                non_empty_namespace += 1

            context[namespace]['stats'] = user_stats(context[namespace]['closed'])
        
        return render(request, "tasks.html", {'data':context})

    def _generate_table(self, table, username, namespace):
        if table == 'pending':
            pending_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'pending'
                }, return_metadata=False, return_states=False)
            open_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'open'
                }, return_metadata=False, return_states=False)
            tasks = pd.concat([pending_tasks, open_tasks]).sort_values('created')
            
            tasks['created'] = tasks['created'].apply(lambda x: utc_to_eastern(x))
            

        elif table == 'closed':
            closed_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'closed'
                }, return_metadata=False, return_states=False)
            errored_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'errored'
                }, return_metadata=False, return_states=False)
            tasks = pd.concat([closed_tasks, errored_tasks]).sort_values('closed')
            
            # Check if there are any NaNs in opened column
            # TODO: Fix this in the database side of things 
            if tasks['opened'].isnull().values.any() or tasks['closed'].isnull().values.any():
                default =  pd.to_datetime('1969-12-31')
                tasks['opened'] = tasks['opened'].fillna(default)
                tasks['closed'] = tasks['closed'].fillna(default)
    
            tasks['opened'] = tasks['opened'].apply(lambda x: utc_to_eastern(x))
            tasks['closed'] = tasks['closed'].apply(lambda x: utc_to_eastern(x))

        tasks.drop(columns=[
                'active',
                'points',
                'assignee',
                'namespace',
                'instructions',
                '__v'
            ], inplace=True)
        
        tasks['task_id'] = tasks.index
        return tasks.to_dict('records')


class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")

class AuthView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "auth_redirect.html")

class InspectTaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR)
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
        try:
            ng_state = json.loads(task_df.get('ng_state'))
        except Exception as e:
            logging.warning(f'Unable to pull ng_state for task: {e}')
            ng_state = None 

        if ng_state:
            if ng_state.get('value'):
                ng_state = ng_state['value']
            context['ng_state'] = json.dumps(ng_state)
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
        
        metadata = task_df['metadata']
        if metadata.get('decision'):
            context['decision'] = metadata['decision']
        return render(request, "inspect.html", context)


    def post(self, request, *args, **kwargs):
        task_id = request.POST.get("task_id")
        return redirect(reverse('inspect', kwargs={"task_id":task_id}))
