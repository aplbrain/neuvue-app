from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from neuvueclient import NeuvueQueue
import numpy as np
import pandas as pd
import time

from .neuroglancer import construct_proofreading_url

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
        context = {
            'ng_url': settings.NG_CLIENT,
            'pcg_url': settings.PROD_PCG_SOURCE,
            'task_id': '',
            'seg_id': '',
            'is_open': False,
            'tasks_available': True,
            'instructions': '',
            'namespace': namespace
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


            # Manually get the points for now, populate in client later.
            points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
            
            # Construct NG URL from points
            context['ng_url'] = construct_proofreading_url(task_df, points)
        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):
        namespace = kwargs.get('namespace')
        logging.debug("POST REQUEST: " + str(request.POST))

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
        
        elif button == 'flag':
            logger.debug('Flagging task')
            self.client.patch_task(
                task_df["_id"], 
                duration=duration, 
                status="errored", 
                ng_state=ng_state)
        
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
        
        return redirect(reverse('workspace', args=[namespace]))


class TaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        
        context = settings.NAMESPACES

        for i, namespace in enumerate(context.keys()):
            context[namespace]["pending"] = []
            context[namespace]["closed"] = []
            context[namespace]["total_pending"] = 0
            context[namespace]["total_closed"] = 0
            context[namespace]["start"] = i*2
            context[namespace]["end"] = (i+1)*2

        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        for namespace in context.keys():
            context[namespace]['pending'] = self._generate_table('pending', str(request.user), namespace)
            context[namespace]['closed'] = self._generate_table('closed', str(request.user), namespace)
            context[namespace]['total_closed'] = len(context[namespace]['closed'])
            context[namespace]['total_pending'] = len(context[namespace]['pending'])
        
        return render(request, "tasks.html", {'data':context})

    def _generate_table(self, table, username, namespace):
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
