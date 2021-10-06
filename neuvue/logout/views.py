from django.shortcuts import render
from django.views.generic.base import View


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "logout.html")
