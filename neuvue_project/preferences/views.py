from .models import Config
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

def convert_for_context(var):
    #slider input needs to be 1 to 100 so I divide the og value by 100 for the display to show 0 to 1 in the js
    pref = float(var)
    pref = pref * 100
    return str(pref)

class PreferencesView(View):
    def get(self, request, *args, **kwargs):
        num_of_params = 3
        settings.USER = request.user
        

        print(len(request.GET))

        #new config
        if Config.objects.filter(user=str(request.user)).count() == 0:
            print("NEW?")
            alpha_selected = request.GET.get('alphaSelected', '0.6')
            alpha_3d = request.GET.get('alpha3D', '0.3')
            config = Config.objects.create(alpha_selected=alpha_selected, user=str(request.user))
            config.save()

         #update existing config
        elif len(request.GET) == num_of_params:
            print("UPDATE?")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest
            config.alpha_selected = request.GET.get('alphaSelected')
            config.alpha_3d = request.GET.get('alpha3D')
            config.save()
         #use previous config
        else:
            print("USE?")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest

        #redefine incase we are using previous configs variables
        alpha_selected = config.alpha_selected
        alpha_3d = config.alpha_3d

        alpha_selected = convert_for_context(alpha_selected)
        alpha_3d = convert_for_context(alpha_3d)
        #not in models yet V, still testing
        layout = request.GET.get('layout')
        context = {
            'alphaSelected': str(alpha_selected),
            'alpha3D': str(alpha_3d),
            'layout': layout
        }

        return render(request, "preferences.html", context)
