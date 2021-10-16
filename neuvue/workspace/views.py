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
from caveclient import CAVEclient
from nglui.statebuilder import *
import numpy as np

def get_NG_link(coordinates):
    img_source = 'precomputed://https://storage.googleapis.com/iarpa_microns/minnie/minnie65/em'
    seg_source = 'graphene://https://minnie.microns-daf.com/segmentation/table/minnie3_v1'
    img_layer = ImageLayerConfig(name='em',
                                 source=img_source,
                                 )
    seg_layer = SegmentationLayerConfig(name = 'seg',
                                        source = seg_source,
                                       selected_ids_column='pt_root_id')
    anno_layer = AnnotationLayerConfig(name='annos')
    view_options = {'position': coordinates, 'zoom_image': 20}
    sb = StateBuilder(layers=[img_layer, seg_layer, anno_layer], view_kws=view_options)
    link = sb.render_state(url_prefix='http://neuroglancer.neuvue.io.s3-website-us-east-1.amazonaws.com')
    return link

class WorkspaceView(View):

    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.COLOCARPY_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        #restart begins as start
        #if open display task
        #this part not done
        link = "http://neuroglancer.neuvue.io.s3-website-us-east-1.amazonaws.com/?local_id=6cbc0542207c4996743f4e12bd20f35d#"
        args = {
            'new_link': link
        }
        return render(request, "workspace.html", args)

    def post(self, request, *args, **kwargs):

        if 'restart' in request.POST:
            print("restart")
            task = self.client.get_next_task("andy", "neuvue")
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])
            link = get_NG_link(coordinates)

        if 'next' in request.POST:
            print("next")
            task = self.client.get_next_task("andy", "neuvue")
            self.client.patch_task(task["_id"], status = "complete")
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])
            link = get_NG_link(coordinates)
        if 'flag' in request.POST:
            print("flag")
            task = self.client.get_next_task("andy", "neuvue")
            self.client.patch_task(task["_id"], status = "errored")
            point = self.client.get_point(task['points'][0])
            coordinates = np.array(point['coordinate'])
            link = get_NG_link(coordinates)

        args = {
            'new_link': link
        }

        return render(request, "workspace.html", args)


class TaskView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "tasks.html")
