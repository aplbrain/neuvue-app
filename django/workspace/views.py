from django.shortcuts import render
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
            'n_tasks_complete': 0
        }
        
        if not request.is_authenticated:
            #TODO: Create Modal that lets the user know to log in first. 
            return render(request, "workspace.html", context)
        
        # Check if the user has an open task 
        open_tasks = self.client.get_tasks(sieve={
            "assignee": request.user,
            "status": "open"
            "namespace"
            })
        
        return render(request, "workspace.html", args)

    def post(self, request, *args, **kwargs):

        if 'restart' in request.POST:
            print("restart")
            task = self.client.get_next_task("andy", "neuvue")
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])
            link = get_NG_link(coordinates)

        
        if 'submit' in request.POST:
            print("submit")
            task = self.client.get_next_task("andy", "neuvue")
            self.client.patch_task(task["_id"], status = "complete")
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])
            link = get_NG_link(coordinates)
        
        if 'flag' in request.POST:
            # Create a modal that will say "Flagging Task {task_ID}. Please write reason for flag below"
            # Input box in the modal that will user input for flag reason
            # Cancel/Flag 

            print("flag")
            task = self.client.get_next_task("andy", "neuvue")
            self.client.patch_task(task["_id"], status = "errored", metadata = {"flag_reason": "flag reason"})
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])

            args = {
                'ng_url': settings.NG_CLIENT
            }

        return render(request, "workspace.html", args)


class TaskView(View):
    def get(self, request, *args, **kwargs):
        # logic/API calls go here 
        # Make a call to neuvue-queue using neuvue-client to get_tasks()
        # tasks = get_tasks(sieve={"assignee": username, "status": "pending|closed|open|erorred")

        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")