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
            'is_open': False,
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
            points = np.array(points)
            
            # Construct NG URL from points
            context['ng_url'] = construct_proofreading_url([task_df['seg_id']], points[0], points)

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
            # Create a modal that will say "Flagging Task {task_ID}. Please write reason for flag below"
            # Input box in the modal that will user input for flag reason
            # Cancel/Flag 

            logger.debug('Flagging task')
            task_df = self.client.get_next_task(str(request.user), "path-split")
            self.client.patch_task(task_df["_id"], status="errored", metadata={"flag_reason": "flag reason"})
        
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
            redirect(reverse('tasks'))

        return redirect(reverse('workspace'))


class TaskView(View):
    def dispatch(self, request, *args, **kwargs):
        self.client = colocarpy.Colocard(settings.NEUVUE_QUEUE_ADDR)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # logic/API calls go here 
        # Make a call to neuvue-queue using neuvue-client to get_tasks()
        if (request.user.is_authenticated):
            username = str(request.user)
        else:
            # just for local testing
            username = 'michael'
            namespace = "path-split" # need to modify for other tables when we have more than just split tasks


        def PendingTable(username, namespace):
            tasks = self.client.get_tasks(sieve={"assignee": username, 
                            "namespace": namespace,
                            "active": True}).sort_values('created')
            render_info = tasks[['seg_id','priority','created']].copy()
            render_info['id'] = render_info.index
            render_info.columns = ['Task ID','Seg ID', 'Priority', 'Created Time']
            # for the pending table this highlights the first row
            html_render = render_info.to_html().replace('tbody', 'tbody class="pending"', 1) 
            
            return html_render
        try:
            pending_split_table = PendingTable(username,namespace)
        except:
            pending_split_table = '<table border="1" class="dataframe">\n  <thead>\n    <tr style="text-align: right;">\n      <th></th>\n      <th>Task ID</th>\n      <th>Seg ID</th>\n      <th>Priority</th>\n      <th>Created Time</th>\n    </tr>\n    <tr>\n      <th>_id</th>\n      <th></th>\n      <th></th>\n      <th></th>\n      <th></th>\n    </tr>\n  </thead>\n  <tbody class="pending">\n    <tr>\n      <th>616fab36cf9e1d89e5d0d12f</th>\n      <td>864691135212669056</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:58.860</td>\n      <td>616fab36cf9e1d89e5d0d12f</td>\n    </tr>\n    <tr>\n      <th>616fab36cf9e1d89e5d0d131</th>\n      <td>864691135373649737</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:59.130</td>\n      <td>616fab36cf9e1d89e5d0d131</td>\n    </tr>\n    <tr>\n      <th>616fab37cf9e1d89e5d0d133</th>\n      <td>864691135939307009</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:59.400</td>\n      <td>616fab37cf9e1d89e5d0d133</td>\n    </tr>\n    <tr>\n      <th>616fab37cf9e1d89e5d0d134</th>\n      <td>864691135212740992</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:59.535</td>\n      <td>616fab37cf9e1d89e5d0d134</td>\n    </tr>\n    <tr>\n      <th>616fab37cf9e1d89e5d0d135</th>\n      <td>864691136577786132</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:59.672</td>\n      <td>616fab37cf9e1d89e5d0d135</td>\n    </tr>\n    <tr>\n      <th>616fab37cf9e1d89e5d0d136</th>\n      <td>864691136436389022</td>\n      <td>1</td>\n      <td>2021-10-20 05:37:59.803</td>\n      <td>616fab37cf9e1d89e5d0d136</td>\n    </tr>\n    <tr>\n      <th>616fab38cf9e1d89e5d0d139</th>\n      <td>864691135736906116</td>\n      <td>1</td>\n      <td>2021-10-20 05:38:00.227</td>\n      <td>616fab38cf9e1d89e5d0d139</td>\n    </tr>\n    <tr>\n      <th>616fab3bcf9e1d89e5d0d153</th>\n      <td>864691135864740060</td>\n      <td>1</td>\n      <td>2021-10-20 05:38:03.729</td>\n      <td>616fab3bcf9e1d89e5d0d153</td>\n    </tr>\n    <tr>\n      <th>616fab3ccf9e1d89e5d0d159</th>\n      <td>864691135449505522</td>\n      <td>1</td>\n      <td>2021-10-20 05:38:04.540</td>\n      <td>616fab3ccf9e1d89e5d0d159</td>\n    </tr>\n    <tr>\n      <th>6170700ccf9e1d89e5d0d3ec</th>\n      <td>864691135926330580</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:48.837</td>\n      <td>6170700ccf9e1d89e5d0d3ec</td>\n    </tr>\n    <tr>\n      <th>6170700ecf9e1d89e5d0d3f7</th>\n      <td>864691136056415192</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:50.326</td>\n      <td>6170700ecf9e1d89e5d0d3f7</td>\n    </tr>\n    <tr>\n      <th>6170700ecf9e1d89e5d0d3fa</th>\n      <td>864691136370810248</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:50.745</td>\n      <td>6170700ecf9e1d89e5d0d3fa</td>\n    </tr>\n    <tr>\n      <th>61707010cf9e1d89e5d0d405</th>\n      <td>864691135584436210</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:52.231</td>\n      <td>61707010cf9e1d89e5d0d405</td>\n    </tr>\n    <tr>\n      <th>61707011cf9e1d89e5d0d40c</th>\n      <td>864691135937387061</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:53.141</td>\n      <td>61707011cf9e1d89e5d0d40c</td>\n    </tr>\n    <tr>\n      <th>61707011cf9e1d89e5d0d40e</th>\n      <td>864691135918354096</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:53.431</td>\n      <td>61707011cf9e1d89e5d0d40e</td>\n    </tr>\n    <tr>\n      <th>61707011cf9e1d89e5d0d410</th>\n      <td>864691136194057942</td>\n      <td>1</td>\n      <td>2021-10-20 19:37:53.705</td>\n      <td>61707011cf9e1d89e5d0d410</td>\n    </tr>\n  </tbody>\n</table>'

        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")