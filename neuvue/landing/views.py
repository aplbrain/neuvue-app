from django.shortcuts import render
from django.views.generic.base import View


class LandingView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "landing.html")
