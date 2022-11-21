import json
import markdown
import logging

from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.staticfiles.storage import staticfiles_storage

# import the logging library
logging.basicConfig(level=logging.INFO)
# Get an instance of a logger
logger = logging.getLogger(__name__)

class IndexView(View):
    def get(self, request, *args, **kwargs):

        recent_updates = True
        try:
            p = staticfiles_storage.path('updates.json')
            with open(p) as update_json:
                updates = json.load(update_json)
                recent_updates = updates['recent_updates']
        except:
            recent_updates = False

        ## Get updates from local updates.json
        context = {
            "recent_updates": recent_updates
        }
        return render(request, "index.html", context)

class AuthView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "auth_redirect.html")

class AboutView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "about.html")

class TokenView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "token.html", context={'code': request.GET.get('code')})

class GettingStartedView(View):
    def get(self, request, *args, **kwargs):
        try:
            p = staticfiles_storage.path('getting_started.md')
            with open(p, 'r') as f:
                text = f.read()
                html = markdown.markdown(text)
        except:
            html = "Error Rendering Text"

        ## Get updates from local updates.json
        context = {
            "getting_started_text": html
        }
        return render(request, "getting-started.html",context)