from django.conf import settings


def app_metadata(request):
    return {
        "neuvue_app_version": settings.NEUVUE_APP_VERSION,
    }
