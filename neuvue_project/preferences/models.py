from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.

class Config(models.Model):
    user = models.CharField(max_length=50, default = None)
    enabled = models.BooleanField(default=False)
    alpha_selected= models.CharField(max_length=10, default="0.85")
    alpha_3d= models.CharField(max_length=10, default="0.5")
    gpu_limit=models.CharField(max_length=10, default="1.0")
    sys_limit=models.CharField(max_length=10, default="2.0")
    chunk_requests=models.CharField(max_length=10, default="32")
    layout = models.CharField(max_length=10, default="xy-3d")

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.user
