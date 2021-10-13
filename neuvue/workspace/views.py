from django.shortcuts import render
from django.views.generic.base import View
import colocarpy
from django.conf import settings
import pandas as pd
import os

import pickle
import colocarpy
import random
from tqdm.notebook import tqdm

PROOFREADERS = [
    "michael",
    "andy",
    "jim",
    "pam",
    "kevin",
    "oscar",
    "dwight"
]

AUTHOR = "danny"
NAMESPACE = "neuvue"
TYPE = "soma-center"
INSTRUCTIONS = {"prompt": "Follow the path trace and identify any visible merge errors."}

#neuvue-client utilty functions
def create_point_map(df):
    point_map = {}
    for root_id in df['pt_root_id'].unique():
        point_map[root_id] = df[df['pt_root_id'] == root_id]['pt_position'].values.tolist()
    return point_map

def post_points_from_map(client, point_map, **kwargs):
    id_map = {}
    for root_id, points in tqdm(point_map.items()):
        posted_ids = []
        for point in points:
            # Convert from 4x4x40 to 8x8x40
            point = point // [2,2,1]
            resp = client.post_point(
                coordinate=point.tolist(), 
                author=AUTHOR, 
                namespace=NAMESPACE, 
                type=TYPE
            )
            posted_ids.append(resp[0]['_id'])
        id_map[root_id] = posted_ids
    return id_map

def post_tasks_from_map(client, id_map, **kwargs):
    posted_task_ids = []
    for root_id, point_ids in tqdm(id_map.items()):
        resp = client.post_task(
            points=point_ids,
            author=AUTHOR,
            assignee=random.choice(PROOFREADERS),
            priority=1,
            namespace=NAMESPACE,
            instructions=INSTRUCTIONS
        )
        posted_task_ids.append(resp[0]['_id'])
    return posted_task_ids

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
