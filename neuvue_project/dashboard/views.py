import json
from django.shortcuts import render
from django.views.generic.base import View
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.apps import apps

from neuvueclient import NeuvueQueue
from typing import List

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)
class DashboardView(View, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, namespace=None, group=None, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(reverse('index'))
        
        Namespaces = apps.get_model('workspace', 'Namespace')
        
        context = {}
        context['all_groups'] = [x.name for x in Group.objects.all()]
        context['all_namespaces'] = [x.display_name for x in Namespaces.objects.all()]
        
        if not group or not namespace: 
            return render(request, "dashboard.html", context)
        
        users = self._get_users_from_group(group)
        table, counts = self._generate_table_and_counts(namespace, users)
        
        context['group'] = group
        context['namespace'] = namespace
        context['display_name'] = Namespaces.objects.get(namespace = namespace).display_name
        context['table'] = table
        context['total_closed'] = counts[0]
        context['total_pending'] = counts[1]
        context['total_open'] = counts[2]
        context['total_errored'] = counts[3]


        return render(request, "dashboard.html", context)

    def _get_users_from_group(self, group:str): 
        users = Group.objects.get(name=group).user_set.all() 
        return [x.username for x in users]
    
    def _generate_table_and_counts(self, namespace: str, users: List):
        table_rows = []
        # Counts
        tc = tp = to = te = 0
        for user in users:
            task_df = self.client.get_tasks(sieve={
                'assignee': user,
                'namespace': namespace
            }, return_states=False, return_metadata=False)
            task_df= task_df.sort_values('created', ascending=False)
            last_closed = self._format_time(task_df['closed'].max())
            task_df['task_id'] = task_df.index
            task_df['opened'] = task_df['opened'].apply(self._format_time)
            task_df['closed'] = task_df['closed'].apply(self._format_time)
            task_df['created'] = task_df['created'].apply(self._format_time)
            task_df['duration'] = (task_df['duration']/60).round(1)
            # Append row info 
            row = {
                'username': user,
                'pending': self._get_status_count(task_df, 'pending'),
                'open': self._get_status_count(task_df, 'open'),
                'closed': self._get_status_count(task_df, 'closed'),
                'errored': self._get_status_count(task_df, 'errored'),
                'last_closed': last_closed,
                'user_tasks': task_df.to_dict('records')
            }

            table_rows.append(row)
            tc += int(row['closed'])
            tp += int(row['pending'])
            to += int(row['open'])
            te += int(row['errored'])

            
        return table_rows, (tc, tp, to, te)

    def _format_time(self, x):
        try:
            return x.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return 'N/A'

    def _get_status_count(self, task_df, status):
        return task_df['status'].value_counts().get(status, 0)

    def post(self, request, *args, **kwargs):
        Namespaces = apps.get_model('workspace', 'Namespace')
        # Refresh request
        display_name = request.POST.get("namespace")
        group = request.POST.get("group")
        namespace = Namespaces.objects.get(display_name = display_name).namespace

        if "selected_tasks" in request.POST:
            selected_action = request.POST.get("selected_action")
            reassigned_user = request.POST.get("reassign_user")
            selected_tasks = request.POST.getlist("selected_tasks")
            
            for task in selected_tasks:
                if selected_action == 'delete':
                    logging.debug(f"Delete task: {task}")
                    self.client.delete_task(task)
                elif selected_action == "reassign":
                    self.client.patch_task(task,assignee=reassigned_user)
                    logging.debug(f"Resassigning task {task} to {reassigned_user}")
        return redirect(reverse('dashboard', kwargs={"namespace":namespace, "group": group}))