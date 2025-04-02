from django.db import models
from django.utils.translation import gettext_lazy as _
from colorfield.fields import ColorField
from django.contrib.auth.models import User, Group
from django.contrib import admin
from .validators import validate_submission_value, no_whitespace

# Create your models here.


class NeuroglancerLinkType(models.TextChoices):
    """Enum for neuroglancer link types. Currently supported:

    path -> expects a list of coordinates (metadata) and two soma points (points).
    Draws a path between all coordinates.

    point -> expects a list of coordinates (metadata), description (metadata), and
    group (metadata). Needs at least one seed point (points). Places dot points for
    all coordinates listed.

    pregenerated -> neuroglancer state already added to task. Useful for external
    outputs like CV or automated proofreading.
    """

    PATH = "path", _("Path Layer")
    POINT = "point", _("Annotation Layer")
    PREGENERATED = "pregen", _("Pregenerated")


class NeuroglancerHost(models.TextChoices):
    """Enum for neuroglancer hosts

    neuroglancer.neuvue.io (default) -> built-in neuroglancer forked from seung-lab
    neuroglancer

    neuroglancer.bossdb.io -> embedded-neuroglancer used by BossDB. Uses latest google
    fork

    spelunker.cave-explorer.org -> embedded neuroglancer developed by AIBS.
    """

    NEUVUE = "neuvue", _("NeuVue Legacy")
    SPELUNKER = "spelunker", _("Spelunker Native")
    BOSSDB = "https://neuroglancer.bossdb.io", _("neuroglancer.bossdb.io")
    SPELUNKER_URL = "https://spelunker.cave-explorer.org/", _(
        "spelunker.cave-explorer.org"
    )


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
    MINNIE_PUBLIC = ("https://minnie.microns-daf.com/segmentation/table/minnie65_public",
        _("Minnie65 Public (read-only)")
    )
    OTHER = "N/A", _("Other")


class ImageChoices(models.TextChoices):
    MINNIE = (
        "https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em",
        _("Minnie65"),
    )
    PINKY = (
        "gs://microns_public_datasets/pinky100_v0/son_of_alignment_v15_rechunked",
        _("Pinky"),
    )
    OTHER = "N/A", _("Other")

class TaskBucketActions(models.TextChoices):
    PUSH = (
        "push",
        _("Push Tasks to"),
    )
    PULL = (
        "pull",
        _("Pull tasks from"),
    )

class TaskBucket(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    bucket_assignee = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Assignee string to in the queue for this task bucket",
        validators=[no_whitespace]
    )
    def __str__(self):
        return self.name

class Namespace(models.Model):
    namespace_enabled = models.BooleanField(default=True)
    namespace = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    ng_link_type = models.CharField(
        max_length=50,
        choices=NeuroglancerLinkType.choices,
        default=NeuroglancerLinkType.PREGENERATED,
    )
    ng_host = models.CharField(
        max_length=100,
        choices=NeuroglancerHost.choices,
        default=NeuroglancerHost.NEUVUE,
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
    decrement_priority = models.IntegerField(
        default=100, verbose_name="When skipped, decrement priority by"
    )
    is_demo = models.BooleanField(default=False, verbose_name="Demonstration only? (Submitting does not patch task)")

    default_push_rule = models.ForeignKey(
        "NamespaceRule",
        on_delete=models.SET_NULL,
        related_name="default_push_for_namespace",
        null=True,
        blank=True,
        help_text="Select the default push rule for this namespace. Must be set after the namespace is created.",
    )
    default_pull_rule = models.ForeignKey(
        "NamespaceRule",
        on_delete=models.SET_NULL,
        related_name="default_pull_for_namespace",
        null=True,
        blank=True,
        help_text="Select the default pull rule for this namespace. Must be set after the namespace is created.",
    )

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.namespace


class NamespaceRule(models.Model):
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, 
                              choices=TaskBucketActions.choices, 
                              default=TaskBucketActions.PULL, 
                              help_text="Determines if this rule provides a source or sink for tasks in the queue")
    task_bucket = models.ForeignKey(TaskBucket, on_delete=models.CASCADE)
    class Meta:
        unique_together = ("namespace", "action", "task_bucket")

    def __str__(self):
        return f"{self.namespace.display_name}: {self.action} -> {self.task_bucket.bucket_assignee}"


# Janky way to extend the default User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    namespace_rule = models.ManyToManyField(NamespaceRule, blank=True)
    
    # @property
    # def inherited_namespace_rules(self):
    #     """Get all namespace rules inherited from the user's groups."""
    #     group_rules = NamespaceRule.objects.filter(
    #         groupprofile__group__in=self.user.groups.all()
    #     )
    #     return group_rules.distinct()

# Janky way to extend the default Group model
class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    namespace_rule = models.ManyToManyField(NamespaceRule, blank=True)