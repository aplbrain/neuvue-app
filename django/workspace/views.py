from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.urls import path
import colocarpy
import numpy as np
import pandas as pd


from .neuroglancer import construct_proofreading_url,create_base_state

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)

class WorkspaceView(View):

    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.NEUVUE_QUEUE_ADDR)
        self.namespace = settings.NAMESPACES[0]
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            'ng_url': settings.NG_CLIENT,
            'pcg_url': settings.PROD_PCG_SOURCE,
            'task_id': '',
            'seg_id': '',
            'is_open': False,
            'tasks_available': True
        }

        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        # Get the next task. If its open already display immediately.
        # TODO: Save current task to session.
        task_df = self.client.get_next_task(str(request.user), self.namespace)
        if not task_df:
            context['tasks_available'] = False
            pass

        elif task_df['status'] == 'open':
            # Update Context
            context['is_open'] = True
            context['task_id'] = task_df['_id']
            context['seg_id'] = task_df['seg_id']


            # Manually get the points for now, populate in client later.
            points = [self.client.get_point(x)['coordinate'] for x in task_df['points']]
            path_coordinates = task_df['metadata'].get('path_coordinates', [])
            path_coordinates.insert(0 ,points[0])
            path_coordinates.append(points[-1])
            path_coordinates = np.array(path_coordinates)
            # Construct NG URL from points
            
            ng_state = construct_proofreading_url([task_df['seg_id']], path_coordinates[0], path_coordinates, prefix=request.get_full_path(), return_as='json')
                
            context['ng_state'] = ng_state
            
            
        logging.debug(context)
        return render(request, "workspace.html", context)

    def post(self, request, *args, **kwargs):

        if 'restart' in request.POST:
            logger.debug('Restarting task')
        
        if 'submit' in request.POST:
            logger.debug('Submitting task')
            task_df = self.client.get_next_task(str(request.user), self.namespace)
            self.client.patch_task(task_df["_id"], status="closed")
        
        if 'flag' in request.POST:
            # Create a modal that will say "Flagging Task {task_ID}. Please write reason for flag below"
            # Input box in the modal that will user input for flag reason
            # Cancel/Flag 

            logger.debug('Flagging task')
            task_df = self.client.get_next_task(str(request.user), self.namespace)
            self.client.patch_task(task_df["_id"], status="errored")
        
        if 'start' in request.POST:
            logger.debug('Starting new task')
            task_df = self.client.get_next_task(str(request.user), self.namespace)
            if not task_df:
                logging.warning('Cannot start task, no tasks available.')
            else:
                self.client.patch_task(task_df["_id"], status="open")
        
        if 'stop' in request.POST:
            logger.debug('Stopping proofreading app')
            # Check if there is an open task in session
            # Confirm exit and save time point
            return redirect(reverse('tasks'))

        return redirect(reverse('workspace'))


class TaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        
        namespaces = settings.NAMESPACES
        context = {}

        for namespace in namespaces:
            context[namespace] = {
                    "pending": [],
                    "closed": [],
                    "total_pending": 0,
                    "total_closed": 0
                }
        # context['ng_uri'] = create_base_state(return_as='url', url_prefix=path('workspace'))
        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        for namespace in namespaces:
            context[namespace]['pending'] = self._generate_table('pending', str(request.user), namespace)
            context[namespace]['closed'] = self._generate_table('closed', str(request.user), namespace)
            context[namespace]['total_closed'] = len(context[namespace]['closed'])
            context[namespace]['total_pending'] = len(context[namespace]['pending'])
        
        return render(request, "tasks.html", context)

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