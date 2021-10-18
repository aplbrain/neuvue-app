from django.shortcuts import render
from django.views.generic.base import View
from django.conf import settings

import colocarpy
import pandas as pd
import numpy as np

class WorkspaceView(View):

    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        #restart begins as start
        #if open display task
        #this part not done
        args = {
            'ng_url': settings.NG_CLIENT,
            'pcg_url': settings.PROD_PCG_SOURCE,
            'task_id': "N/A"
        }
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
        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")