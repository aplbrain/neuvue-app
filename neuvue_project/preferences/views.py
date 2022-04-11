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
            'annotationColor': config.annotation_color,
            'annotationColorSwitch': config.annotation_color_switch,
            'showSlices':config.show_slices,
            'showSlicesSwitch':config.show_slices_switch,
            'alphaSelected': config.alpha_selected,
            'alphaSelectedSwitch': config.alpha_selected_switch,
            'alpha3D': config.alpha_3d,
            'alpha3DSwitch': config.alpha_3d_switch,
            'gpuLimit': config.gpu_limit,
            'gpuLimitSwitch': config.gpu_limit_switch,
            'sysLimit': config.sys_limit,
            'sysLimitSwitch': config.sys_limit_switch,
            'chunkReq': config.chunk_requests,
            'chunkReqSwitch': config.chunk_requests_switch,
            'layout': config.layout,
            'layoutSwitch': config.layout_switch
        }

        return render(request, "preferences.html", context)

    def post(self, request, *args, **kwargs):
        print(request.POST)
        logging.debug(f"Update Config for {request.user}.")
        config = Config.objects.filter(user=str(request.user)).order_by('-id')[0]

        config.enabled = request.POST.get('enabled') == 'true'

        config.annotation_color = request.POST.get('annotationColor')
        config.annotation_color_switch = request.POST.get('annotationColorSwitch') == 'true'

        config.show_slices = request.POST.get('showSlices') == 'true'
        config.show_slices_switch = request.POST.get('showSlicesSwitch') == 'true'

        config.alpha_selected = request.POST.get('alphaSelected')
        config.alpha_selected_switch = request.POST.get('alphaSelectedSwitch') == 'true'

        config.alpha_3d = request.POST.get('alpha3D')
        config.alpha_3d_switch = request.POST.get('alpha3DSwitch') == 'true'

        config.gpu_limit = request.POST.get('gpuLimit')
        config.gpu_limit_switch = request.POST.get('gpuLimitSwitch') == 'true'

        config.sys_limit = request.POST.get('sysLimit')
        config.sys_limit_switch = request.POST.get('sysLimitSwitch') == 'true'

        config.chunk_requests = request.POST.get('chunkReq')
        config.chunk_requests_switch = request.POST.get('chunkReqSwitch') == 'true'

        config.layout = request.POST.get('layout')
        config.layout_switch = request.POST.get('layoutSwitch') == 'true'

        config.save()
        return redirect(reverse('preferences'))