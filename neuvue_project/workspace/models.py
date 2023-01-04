from django.db import models
from django.utils.translation import gettext_lazy as _
from colorfield.fields import ColorField
from django.contrib.auth.models import User
from django.contrib import admin
from .validators import validate_submission_value

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

    PATH = "path", _("Path Layer")
    POINT = "point", _("Annotation Layer")
    PREGENERATED = "pregen", _("Pregenerated")


class ForcedChoiceButtonGroup(models.Model):
    group_name = models.CharField(max_length=100, unique=True, help_text="(snake case)")
    submit_task_button = models.BooleanField(default=True)
    number_of_selected_segments_expected = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = "Forced Choice Button Group"
        verbose_name_plural = "Forced Choice Button Groups"


class HotkeyChoices(models.TextChoices):
    C = "c"
    D = "d"
    J = "j"
    M = "m"
    Q = "q"
    R = "r"
    T = "t"
    V = "v"
    W = "w"
    Y = "y"
    Z = "z"


class ForcedChoiceButton(models.Model):
    set_name = models.ForeignKey(
        ForcedChoiceButtonGroup, to_field="group_name", on_delete=models.CASCADE
    )
    display_name = models.CharField(max_length=100)
    submission_value = models.CharField(
        max_length=100, validators=[validate_submission_value]
    )
    button_color = ColorField(format="hexa")
    button_color_active = ColorField(format="hexa")
    hotkey = models.CharField(
        max_length=300, choices=HotkeyChoices.choices, blank=True, null=True
    )

    def __str__(self):
        return str(self.set_name)


class PcgChoices(models.TextChoices):
    MINNIE = "https://minnie.microns-daf.com/segmentation/table/minnie3_v1", _(
        "Minnie65"
    )
    PINKY = (
        "https://minnie.microns-daf.com/segmentation/table/pinky_v2_microns_sandbox",
        _("Pinky"),
    )


class ImageChoices(models.TextChoices):
    MINNIE = (
        "https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em",
        _("Minnie65"),
    )
    PINKY = (
        "gs://microns_public_datasets/pinky100_v0/son_of_alignment_v15_rechunked",
        _("Pinky"),
    )


class PushToChoices(models.TextChoices):
    NULL = "Queue Tasks Not Allowed"
    NOVICE = "unassigned_novice"
    INTERMEDIATE = "unassigned_intermediate"
    EXPERT = "unassigned_expert"


class PullFromChoices(models.TextChoices):
    NULL = "Reassign Tasks Not Allowed"
    NOVICE = "unassigned_novice"
    INTERMEDIATE = "unassigned_intermediate"
    EXPERT = "unassigned_expert"


class Namespace(models.Model):
    namespace_enabled = models.BooleanField(default=True)
    namespace = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    ng_link_type = models.CharField(
        max_length=50,
        choices=NeuroglancerLinkType.choices,
        default=NeuroglancerLinkType.PREGENERATED,
    )
    submission_method = models.ForeignKey(
        ForcedChoiceButtonGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        to_field="group_name",
        db_column="submission_method",
    )
    pcg_source = models.CharField(
        max_length=300, choices=PcgChoices.choices, default=PcgChoices.MINNIE
    )
    img_source = models.CharField(
        max_length=300, choices=ImageChoices.choices, default=ImageChoices.MINNIE
    )
    track_operation_ids = models.BooleanField(default=True)
    refresh_selected_root_ids = models.BooleanField(default=False)
    number_of_tasks_users_can_self_assign = models.IntegerField(default=10)
    max_number_of_pending_tasks_per_user = models.IntegerField(default=200)
    track_selected_segments = models.BooleanField(default=False)
    allow_users_to_skip_tasks = models.BooleanField(default=True)

    """Pull From Push To Novice"""
    novice_pull_from = models.CharField(
        max_length=50, choices=PullFromChoices.choices, default=PullFromChoices.NULL
    )
    novice_push_to = models.CharField(
        max_length=50, choices=PushToChoices.choices, default=PushToChoices.NULL
    )

    """Pull From Push To Intermediate"""
    intermediate_pull_from = models.CharField(
        max_length=50, choices=PullFromChoices.choices, default=PullFromChoices.NULL
    )
    intermediate_push_to = models.CharField(
        max_length=50, choices=PushToChoices.choices, default=PushToChoices.NULL
    )

    """Pull From Push To Expert"""
    expert_pull_from = models.CharField(
        max_length=50, choices=PullFromChoices.choices, default=PullFromChoices.NULL
    )
    expert_push_to = models.CharField(
        max_length=50, choices=PushToChoices.choices, default=PushToChoices.NULL
    )

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.namespace


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    intermediate_namespaces = models.ManyToManyField(
        Namespace, related_name="intermediate_namespaces", blank=True
    )
    expert_namespaces = models.ManyToManyField(
        Namespace, related_name="expert_namespaces", blank=True
    )
