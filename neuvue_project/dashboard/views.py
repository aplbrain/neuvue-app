from django.shortcuts import render
from django.views.generic.base import View
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from neuvueclient import NeuvueQueue

class DashboardView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "dashboard.html")