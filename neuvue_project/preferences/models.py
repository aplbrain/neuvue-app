from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.

class Config(models.Model):
    user = models.CharField(max_length=50, default = None)
    enabled = models.BooleanField(default=False)
    
    # Annotation Color Palette
    annotation_color_palette = models.CharField(max_length=10, default='palette1', null=True, blank=True)
    annotation_color_palette_switch = models.BooleanField(default=False)

    # 2D Show Slices
    show_slices=models.BooleanField(default=False)
    show_slices_switch = models.BooleanField(default=False)

   # Zoom Level
    zoom_level= models.CharField(max_length=10, default="20")
    zoom_level_switch = models.BooleanField(default=False)

    # 2D Segmentation Opacity 
    alpha_selected= models.CharField(max_length=10, default="0.85")
    alpha_selected_switch = models.BooleanField(default=False)

    # 3D Segmentation Opacity 
    alpha_3d= models.CharField(max_length=10, default="0.5")
    alpha_3d_switch = models.BooleanField(default=False)

    # GPU Memory Limit
    gpu_limit=models.CharField(max_length=10, default="1.0")
    gpu_limit_switch = models.BooleanField(default=False)

    # CPU Memory Limit
    sys_limit=models.CharField(max_length=10, default="2.0")
    sys_limit_switch = models.BooleanField(default=False)

    # Concurrent Chunk Requests
    chunk_requests=models.CharField(max_length=10, default="32")
    chunk_requests_switch = models.BooleanField(default=False)

    # NG Layout
    layout = models.CharField(max_length=10, default="xy-3d")
    layout_switch = models.BooleanField(default=False)

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.user
