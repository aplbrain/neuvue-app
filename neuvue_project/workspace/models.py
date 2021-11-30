from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.

class NeuroglancerLinkType(models.TextChoices):
    """Enum for neuroglancer link types. Currently supported:

    path -> expects a list of coordinates (metadata) and two soma points (points). 
    Draws a path between all coordinates.
    
    point -> expects a list of coordinates (metadata), description (metadata), and 
    group (metadata). Needs atleast one seed point (points). Places dot points for 
    all coordinates listed.

    pregenerated -> neuroglancer state already added to task. Useful for external
    outputs like CV or automated proofreading.
    """
    PATH = 'path', _('Path Layer')
    POINT = 'point', _('Annotation Layer')
    PREGENERATED = 'pregen', _('Pregenerated')


class Namespace(models.Model):
    submission_method_choices = [
        ('submit', 'Submit Button'),
        ('forced_choice', 'Yes/No/Maybe Button'),
    ]

    class PcgChoices(models.TextChoices):
        MINNIE = 'https://minnie.microns-daf.com/segmentation/table/minnie3_v1', _('Minnie')
        PINKY = 'https://global.daf-apis.com/info/datastack/pinky_sandbox', _('Pinky')

    class ImgChoices(models.TextChoices):
        MINNIE = 'https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em', _('Minnie')
        PINKY = 'gs://microns_public_datasets/pinky100_v0/son_of_alignment_v15_rechunked', _('Pinky')


    namespace = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    ng_link_type = models.CharField(max_length=50, choices = NeuroglancerLinkType.choices, default= NeuroglancerLinkType.POINT)
    submission_method = models.CharField(max_length=50, choices=submission_method_choices, default="submit")
    pcg_source = models.CharField(max_length=300, choices=PcgChoices.choices, default=PcgChoices.MINNIE)
    img_source = models.CharField(max_length=300, choices=ImgChoices.choices, default=ImgChoices.MINNIE)
    
    
    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.namespace



