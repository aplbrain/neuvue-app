from django.shortcuts import render
from django.views.generic.base import View
import colocarpy
from django.conf import settings
import pandas as pd
import os

class WorkspaceView(View):


    def get(self, request, *args, **kwargs):
        return render(request, "workspace.html")

    def post(self, request, *args, **kwargs):

        df = pd.read_pickle(os.path.join(settings.STATICFILES_DIRS[1], "two_soma_df_private_data_10_05_2021.pkl"))


        try:
            client = colocarpy.Colocard("http://3.92.233.204:9005")
        except Exception as e:
            print("could not connect")
        
        # Map point by their root ID, 
        point_map = create_point_map(df.iloc[:50])

        # Post points and save the IDs of each posted point to reference to a task
        id_map = post_points_from_map(client, point_map)

        # Post tasks from the id map
        posted_tasks = post_tasks_from_map(client, id_map)

        if 'restart' in request.POST:
            #client.get_task() need a get current task
            #Gets the coordinates of the current task. Sets neuroglancer state to go to those coordinates.
            client.get_current_task('andy', 'neuvue')
            #get_points
            #feed to neuroglancer and gen link
            #pass link into context
            #show on iframe
            print("restart")
        if 'next' in request.POST:
            #this will submit change status of curr task - clear workspace - display new button that loads next task, change to open, gen link and dispaly
            client.get_next_task('andy', 'neuvue')
            #Updates the current task status from "open" to "closed". Gets the next task. Sets neuroglancer state to go to those coordinates.
            print("next")
        if 'flag' in request.POST:
            #Updates the current task status from "open" to "errored".  Updates the current task metadata with new key:value containing "flag-reason": `message`. Gets the next task (NextTaskView)
            print("flag")

        return render(request, "workspace.html")



class TaskView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")