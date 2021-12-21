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

class DashboardView(View, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR)
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
            })
            user_tasks = task_df.drop(columns=[
                    'active',
                    'points',
                    'assignee',
                    'namespace',
                    'instructions',
                    '__v'
                ])
            user_tasks['task_id'] = user_tasks.index

            # Append row info 
            row = {
                'username': user,
                'pending': self._get_status_count(task_df, 'pending'),
                'open': self._get_status_count(task_df, 'open'),
                'closed': self._get_status_count(task_df, 'closed'),
                'errored': self._get_status_count(task_df, 'errored'),
                'last_closed': self._get_latest_closed_time(task_df),
                'user_tasks': user_tasks.to_dict('records')
            }

            table_rows.append(row)
            tc += int(row['closed'])
            tp += int(row['pending'])
            to += int(row['open'])
            te += int(row['errored'])

            
        return table_rows, (tc, tp, to, te)
    
    def _get_status_count(self, task_df, status):
        return task_df['status'].value_counts().get(status, 0)

    def _get_latest_closed_time(self, task_df):
        try:
            return task_df['closed'].max().strftime('%Y-%m-%d %H:%M:%S')
        except:
            return 'N/A'

    def post(self, request, *args, **kwargs):
        Namespaces = apps.get_model('workspace', 'Namespace')
        display_name = request.POST.get("namespace")
        group = request.POST.get("group")
        namespace = Namespaces.objects.get(display_name = display_name).namespace 
        return redirect(reverse('dashboard', kwargs={"namespace":namespace, "group": group}))