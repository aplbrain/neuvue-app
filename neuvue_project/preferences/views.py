from .models import Config
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin


class PreferencesView(View):
    def get(self, request, *args, **kwargs):

        settings.USER = request.user
        alpha_selected = request.GET.get('alphaSelected', '0.6')
        #alpha_3d = request.GET.get('alpha3D', '0.3')

        #new config
        if Config.objects.filter(user=str(request.user)).count() == 0:
            print("NEW?")
            alpha_selected = request.GET.get('alphaSelected', '0.6')
            #alpha_3d = request.GET.get('alpha3D', '0.3')
            config = Config.objects.create(alpha_selected=alpha_selected, user=str(request.user))
            config.save()

         #update existing config
        elif 'alphaSelected' in request.GET and 'alpha3D' in request.GET:
            print("UPDATE?")
            config = Config.objects.filter(
                user=str(request.user)).order_by('-id')[0]  # latest
            config.alpha_selected = request.GET.get('alphaSelected')
            #config.alpha_3d = request.GET.get('alpha3D')
            config.save()
         #use previous config
        else:
            print("USE?")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest

        return render(request, "preferences.html")
