from django.shortcuts import render
from django.views.generic.base import View

class WorkspaceView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "workspace.html")

class TaskView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "tasks.html")

class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")