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


class PreferencesView(View):
    def get(self, request, *args, **kwargs):

        if Config.objects.filter(user=str(request.user)).count() == 0:
            logging.debug(f"New Config for {request.user}.")
            config = Config.objects.create(user=str(request.user))
            config.save()

        else:
            logging.debug(f"Getting Config for {request.user}.")
            config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]  # latest
        
        context = {
            'enabled': config.enabled,
            'alphaSelected': config.alpha_selected,
            'alpha3D': config.alpha_3d,
            'layout': config.layout
        }

        return render(request, "preferences.html", context)

    def post(self, request, *args, **kwargs):
        logging.debug(f"Update Config for {request.user}.")
        config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]

        if request.POST.get('enabled') == 'true':
            config.enabled = True
        else:
            config.enabled = False

        config.alpha_selected = request.POST.get('alphaSelected')
        config.alpha_3d = request.POST.get('alpha3D')
        config.layout = request.POST.get('layout')
        config.save()
        return redirect(reverse('preferences'))