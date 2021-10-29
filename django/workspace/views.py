from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
import colocarpy
import numpy as np

from .neuroglancer import construct_proofreading_url

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)

class WorkspaceView(View):

    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            'ng_url': settings.NG_CLIENT,
            'pcg_url': settings.PROD_PCG_SOURCE,
            'task_id': '',
            'seg_id': '',
            'is_open': True,
            'tasks_available': True
        }

        if not request.user.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)

        # Get the next task. If its open already display immediately.
        # TODO: Save current task to session.
        task_df = self.client.get_next_task(str(request.user), "path-split")
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
            context['ng_url'] = construct_proofreading_url([task_df['seg_id']], path_coordinates[0], path_coordinates)

        logging.debug(context)
        return render(request, "workspace.html", context)
    

    def post(self, request, *args, **kwargs):

        if 'restart' in request.POST:
            logger.debug('Restarting task')
        
        if 'submit' in request.POST:
            logger.debug('Submitting task')
            task_df = self.client.get_next_task(str(request.user), "path-split")
            self.client.patch_task(task_df["_id"], status="closed")
        
        if 'flag' in request.POST:
            logger.debug('Flagging task')
            if request.POST['flag'] == 'other':
                flag = request.POST['flag-other']
            else:
                flag = request.POST['flag']
            task_df = self.client.get_next_task(str(request.user), "path-split")
            self.client.patch_task(task_df["_id"], status="errored", metadata=flag)
        
        if 'start' in request.POST:
            logger.debug('Starting new task')
            task_df = self.client.get_next_task(str(request.user), "path-split")
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
    def get(self, request, *args, **kwargs):
        # logic/API calls go here 
        # Make a call to neuvue-queue using neuvue-client to get_tasks()
        # tasks = get_tasks(sieve={"assignee": username, "status": "pending|closed|open|erorred")

        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")
'''
[{"active":true,
"closed":null,
"metadata":{},
"opened":null,
"status":"pending",
"seg_id":null,
"points":["61608a4cd6e3a922fa87b23b"],
"_id":"61608d56d6e3a922fa87b26d",
"neuron_status":"incomplete",
"priority":1,
"author":"diego",
"assignee":"oscar",
"namespace":"neuvue",
"instructions":{"prompt":"Follow the path trace and identify any visible merge errors."},
"created":1633717590700,"__v":0}
'''