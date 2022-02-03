from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Config

# import the logging library
import logging
logging.basicConfig(level=logging.DEBUG)
# Get an instance of a logger
logger = logging.getLogger(__name__)


def convert_for_context(var):
    #slider input needs to be 1 to 100 so I divide the og value by 100 for the display to show 0 to 1 in the js
    pref = float(var)
    pref = pref * 100
    return str(pref)

class PreferencesView(View):
    def get(self, request, *args, **kwargs):
        num_of_params = len(Config._meta.get_fields()) - 2

        # new config
        if Config.objects.filter(user=str(request.user)).count() == 0:
            logging.debug(f"New Config for {request.user}.")
            alpha_selected = request.GET.get('alphaSelected', '0.6')
            alpha_3d = request.GET.get('alpha3D', '0.3')
            layout = request.GET.get('layout', '4panel')
            config = Config.objects.create(alpha_selected=alpha_selected, user=str(request.user))
            config.save()

        # update existing config
        elif len(request.GET) == num_of_params:
            logging.debug(f"Update Config for {request.user}.")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest
            config.alpha_selected = request.GET.get('alphaSelected')
            config.alpha_3d = request.GET.get('alpha3D')
            config.layout = request.GET.get('layout')
            config.save()
        # use previous config
        else:
            logging.debug(f"Getting Config for {request.user}.")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest

        #redefine incase we are using previous configs variables
        alpha_selected = config.alpha_selected
        alpha_3d = config.alpha_3d
        layout = config.layout

        #divide by 100
        alpha_selected = convert_for_context(alpha_selected)
        alpha_3d = convert_for_context(alpha_3d)

        context = {
            'alphaSelected': str(alpha_selected),
            'alpha3D': str(alpha_3d),
            'layout': str(layout)
        }

        return render(request, "preferences.html", context)
