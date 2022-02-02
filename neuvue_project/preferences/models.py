from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.

class Config(models.Model):
    user = models.CharField(max_length=50, default = None)
    alpha_selected= models.CharField(max_length=10, default="0.6")
    alpha_3d= models.CharField(max_length=10, default="0.3")
    layout = models.CharField(max_length=10, default="3d-xy")

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.user
