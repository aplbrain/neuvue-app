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

class SubmissionMethod(models.TextChoices):
    SUBMIT = 'submit', _('Submit Button')
    FORCED_CHOICE = 'forced_choice', _('Yes/No/Maybe Button')
    DECIDE_AND_SUBMIT = 'decide_and_submit', _('Decide and Submit Button')

class PcgChoices(models.TextChoices):
    MINNIE = 'https://minnie.microns-daf.com/segmentation/table/minnie3_v1', _('Minnie65')
    PINKY = 'https://minnie.microns-daf.com/segmentation/table/pinky_v2_microns_sandbox', _('Pinky')

class ImageChoices(models.TextChoices):
    MINNIE = 'https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em', _('Minnie65')
    PINKY = 'gs://microns_public_datasets/pinky100_v0/son_of_alignment_v15_rechunked', _('Pinky')

class Namespace(models.Model):
    namespace = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    ng_link_type = models.CharField(max_length=50, choices = NeuroglancerLinkType.choices, default= NeuroglancerLinkType.PREGENERATED)
    submission_method = models.CharField(max_length=50, choices=SubmissionMethod.choices, default=SubmissionMethod.SUBMIT)
    pcg_source = models.CharField(max_length=300, choices=PcgChoices.choices, default=PcgChoices.MINNIE)
    img_source = models.CharField(max_length=300, choices=ImageChoices.choices, default=ImageChoices.MINNIE)
    track_operation_ids = models.BooleanField(default=True)
    
    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.namespace



