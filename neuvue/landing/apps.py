from django.apps import AppConfig


class LandingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'landing'

#test
class TestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'
