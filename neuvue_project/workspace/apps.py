from django.apps import AppConfig


class WorkspaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "workspace"


# test
class TestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests"
