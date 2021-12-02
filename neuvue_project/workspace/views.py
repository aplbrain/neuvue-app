from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Namespace

from neuvueclient import NeuvueQueue
from datetime import datetime, timezone
from pytz import timezone
import pytz
import numpy as np
import pandas as pd
import time
import json

from .neuroglancer import construct_proofreading_url, construct_url_from_existing
from .analytics import user_stats


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
        num_visits = request.session.get('num_visits', 0)
        sidebar_status = request.session.get('sidebar', 1)
        
        request.session['num_visits'] = num_visits + 1
        request.session['sidebar'] = sidebar_status

        context = {
            'ng_url': settings.NG_CLIENT,
            'pcg_url': Namespace.objects.get(namespace = namespace).pcg_source,
            'task_id': '',
            'seg_id': '',
            'is_open': False,
            'tasks_available': True,
            'instructions': '',
            'display_name': Namespace.objects.get(namespace = namespace).display_name,
            'submission_method': Namespace.objects.get(namespace = namespace).submission_method,
            'sidebar': sidebar_status,
            'num_visits': num_visits
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

        elif task_df['status'] == 'open':
            # Reset session timer
            request.session["start_time"] = time.time()
            # Update Context
            context['is_open'] = True
            context['task_id'] = task_df['_id']
            context['seg_id'] = task_df['seg_id']
            context['instructions'] = task_df['instructions']
 
            # Construct NG URL from points or existing state
            try:
                ng_state = json.loads(task_df.get('ng_state'))['value']
            except Exception as e:
                logging.warning(f'Unable to pull ng_state for task: {e}')
                ng_state = None 
    
            if ng_state:
                context['ng_url'] = construct_url_from_existing(json.dumps(ng_state))
            else:
                # Manually get the points for now, populate in client later.
                points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
                context['ng_url'] = construct_proofreading_url(task_df, points)
        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        
        namespace = kwargs.get('namespace')

        # Current task that is opened in this namespace.
        task_df = self.client.get_next_task(str(request.user), namespace)

        button = request.POST.get('button')

        ng_state = request.POST.get('ngState')
        start_time = request.session.get('start_time')
        duration = time.time() - start_time if start_time else 0
        
        if button == 'submit':
            logger.debug('Submitting task')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state)
        
        elif button in ['yes', 'no', 'unsure', 'yesConditional']:
            logger.debug('Submitting task')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="closed",
                ng_state=ng_state,
                metadata={
                    'decision': button
                })

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
                metadata=metadata)
        
        elif button == 'start':
            logger.debug('Starting new task')
            if not task_df:
                logging.warning('Cannot start task, no tasks available.')
            else:
                self.client.patch_task(task_df["_id"], status="open")
            
            #initialize timer 
            request.session["start_time"] = time.time()
        
        elif button == 'stop':
            logger.debug('Stopping proofreading app')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                ng_state=ng_state)
            return redirect(reverse('tasks'))
        
        elif request.body:
            try:
                body = json.loads(request.body)
                if 'sidebar_tab' in body:
                    request.session['sidebar'] = body['sidebar_tab']
            except Exception as e:
                logging.error(f"POST Error: {e}")
        
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
                context[namespace]["end"] = (non_empty_namespace+1)*2
                non_empty_namespace += 1

            context[namespace]['stats'] = user_stats(context[namespace]['closed'])
        
        return render(request, "tasks.html", {'data':context})

    def _generate_table(self, table, username, namespace):
        def utc_to_eastern(time_value):
                utc = pytz.UTC
                eastern = timezone('US/Eastern')
                date_time = time_value.to_pydatetime()
                date_time = utc.localize(time_value)
                date_time = date_time.astimezone(eastern)
                return date_time

        if table == 'pending':
            pending_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'pending'
                })
            open_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'open'
                })
            tasks = pd.concat([pending_tasks, open_tasks]).sort_values('created')
            
            tasks['created'] = tasks['created'].apply(lambda x: utc_to_eastern(x))
            

        elif table == 'closed':
            closed_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'closed'
                })
            errored_tasks = self.client.get_tasks(sieve={
                "assignee": username, 
                "namespace": namespace,
                "status": 'errored'
                })
            tasks = pd.concat([closed_tasks, errored_tasks]).sort_values('closed')
            
            tasks['opened'] = tasks['opened'].apply(lambda x: utc_to_eastern(x))
            tasks['closed'] = tasks['closed'].apply(lambda x: utc_to_eastern(x))

        tasks.drop(columns=[
                'active',
                'metadata',
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
