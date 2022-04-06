from cProfile import label
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
from datetime import datetime 
import plotly.graph_objects as go

# import the logging library
import logging
import pandas as pd
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)

# Convienence function
def _get_users_from_group(group:str): 
    users = Group.objects.get(name=group).user_set.all() 
    return [x.username for x in users]

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
        
        users = _get_users_from_group(group)
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
            new_assignee = request.POST.get("assignee_input")
            selected_tasks = request.POST.getlist("selected_tasks")
            
            try:
                new_priority = int(request.POST.get("priority_input"))
            except:
                new_priority = 0

            for task in selected_tasks:
                if selected_action == 'delete':
                    logging.debug(f"Delete task: {task}")
                    self.client.delete_task(task)
                elif selected_action == "assignee":
                    self.client.patch_task(task,assignee=new_assignee)
                    logging.debug(f"Resassigning task {task} to {new_assignee}")
                elif selected_action == "priority":
                    self.client.patch_task(task, priority=new_priority)
                    logging.debug(f"Reprioritizing task {task} to {new_priority}")
        return redirect(reverse('dashboard', kwargs={"namespace":namespace, "group": group}))


class ReportView(View, LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect(reverse('index'))
        
        Namespaces = apps.get_model('workspace', 'Namespace')
        context = {}
        context['all_groups'] = [x.name for x in Group.objects.all()]
        context['all_namespaces'] = [x.display_name for x in Namespaces.objects.all()]
        return render(request, "report.html", context)

    def _format_time(self, x):
        try:
            return x.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return 'N/A'

    def _get_status_count(self, task_df, status):
        return task_df['status'].value_counts().get(status, 0)

    def post(self, request, *args, **kwargs):
        
        Namespaces = apps.get_model('workspace', 'Namespace')
        
        # Access POST fields
        display_name = request.POST.get('namespace')
        group = request.POST.get('group')
        start_field = request.POST.get('start_field')
        start_date = request.POST.get('start_date')
        end_field = request.POST.get('end_field')
        end_date = request.POST.get('end_date')
        
        # Convert to datetime Objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # Retrieve valid tasks
        namespace = Namespaces.objects.get(display_name = display_name).namespace
        users = _get_users_from_group(group)

        # add bar chart
        decision_namespaces = [x.namespace for x in Namespaces.objects.filter(submission_method__in=['forced_choice','decide_and_submit']).all()]
        if namespace in decision_namespaces:
            import plotly.express as px
            from plotly.subplots import make_subplots
            task_df = self.client.get_tasks(sieve={
                'assignee': users,
                'namespace': namespace,
                start_field: {
                    "$gt": start_dt
                }, 
                end_field: {
                    '$lt': end_dt
                }
            }, select=['assignee', 'status', 'duration','metadata','closed','opened'])
            task_df['decision'] = task_df['metadata'].apply(lambda x: x.get('decision'))
                        
            users=task_df['assignee'].unique()
            fig_decision = make_subplots(rows=1, cols=2, column_widths=[0.12, 0.85], shared_yaxes=True,horizontal_spacing = 0.02)
            color_count = 0
            for decision_type in task_df['decision'].unique():
                if decision_type:
                    decision_counts = dict(task_df[task_df['decision']==decision_type].value_counts('assignee'))
                    x = list(decision_counts.keys())
                    y = list(decision_counts.values())
                    fig_decision.add_trace(
                        go.Bar(name=decision_type, x=x, y=y,marker_color=px.colors.qualitative.Plotly[color_count]),
                        row=1, col=2
                    )
                    fig_decision.add_trace(
                        go.Bar(name=decision_type, x=['total'], y=[sum(y)],marker_color=px.colors.qualitative.Plotly[color_count],showlegend=False),
                        row=1, col=1
                    )
                    color_count +=1
            fig_decision.update_layout(
                title="Decisions for " + namespace + " by " + group,
                yaxis_title="# of responses",
                legend_title="Decision Type",
            )
            fig_decision.update_xaxes(title_text="assignees", row=1, col=2)
        else:
            task_df = self.client.get_tasks(sieve={
                'assignee': users,
                'namespace': namespace,
                start_field: {
                    "$gt": start_dt
                }, 
                end_field: {
                    '$lt': end_dt
                }
            }, select=['assignee', 'status', 'duration','closed','opened'])

        columns = ['Username', 'Total Duration (h)', 'Avg Closed Duration (m)' , 'Avg Duration (m)']
        status_states = ['pending','open','closed','errored']
        columns.extend(status_states)
        table_rows = []
        fig_time = go.Figure()
        for assignee, assignee_df in task_df.groupby('assignee'):
            total_duration = str(round(assignee_df['duration'].sum()/3600,2))
            avg_closed_duration = str(round(assignee_df[assignee_df['status']=='closed']['duration'].mean()/60,2))
            avg_duration = str(round(assignee_df['duration'].mean()/60,2))
            user_metrics = [assignee, total_duration, avg_closed_duration, avg_duration]
            for status in status_states:
                number_of_tasks = len(assignee_df[assignee_df['status']==status])
                user_metrics.append(number_of_tasks)
            table_rows.append(user_metrics)
            assignee_df['last_interaction'] = assignee_df.apply(lambda x: max(x.opened, x.closed).floor('d'), axis=1)
            daily_totals = assignee_df.groupby('last_interaction')['duration'].sum()/3600
            x = daily_totals.index
            y = daily_totals.values
            fig_time.add_trace(go.Scatter(x=x,y=y,name=assignee))
        fig_time.update_layout(showlegend=True,
                                title="Platform Time per User Grouped by Date of Last Interaction",
                                yaxis_title="Duration (h)",
                                xaxis_title="Date of Last Interaction")

        fields = {"created":"Created By",
                    "opened": "Opened By",
                    "closed": "Closed By"}

        context = {"display_name":display_name,
                    "namespace":namespace,
                    "group":group,
                    "start_field":start_field,
                    "start_date":start_date,
                    "end_field":end_field,
                    "end_date":end_date,
                    "table_columns":columns,
                    "table_rows":table_rows,
                    "fields":fields,
                    "all_groups": [x.name for x in Group.objects.all()],
                    "all_namespaces": [x.display_name for x in Namespaces.objects.all()],
                    "fig_time":fig_time.to_html(),
                }
        if namespace in decision_namespaces:
            context["fig_decision"] = fig_decision.to_html()

        return render(request,'report.html',context)
