from django import forms
from .models import Namespace, NamespaceRule, TaskBucketActions
import json
import pandas as pd
import io


class NamespaceAdminForm(forms.ModelForm):
    class Meta:
        model = Namespace
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If we are editing an existing Namespace (i.e., it has a primary key)
        if self.instance and self.instance.pk:
            # Only show NamespaceRules that match this Namespace AND have action = "push"
            self.fields["default_push_rule"].queryset = NamespaceRule.objects.filter(
                namespace=self.instance,
                action=TaskBucketActions.PUSH,
            )

            # Only show NamespaceRules that match this Namespace AND have action = "pull"
            self.fields["default_pull_rule"].queryset = NamespaceRule.objects.filter(
                namespace=self.instance,
                action=TaskBucketActions.PULL,
            )
        else:
            # For a new Namespace (not yet saved), it has no PK.
            # You have a few choices here:
            #
            # 1. Show an empty list (so the admin must save once to create the namespace,
            #    then create or assign rules, and then choose the defaults).
            self.fields["default_push_rule"].queryset = NamespaceRule.objects.none()
            self.fields["default_pull_rule"].queryset = NamespaceRule.objects.none()

            # 2. OR, show *all* push or pull rules, so that an admin might
            #    pick from them before the namespace is actually saved.
            #
            #    self.fields["default_push_rule"].queryset = NamespaceRule.objects.filter(
            #        action=TaskBucketActions.PUSH
            #    )
            #    self.fields["default_pull_rule"].queryset = NamespaceRule.objects.filter(
            #        action=TaskBucketActions.PULL
            #    )
            #
            # Usually, option #1 is cleaner, because you generally need
            # the Namespace to exist before you can create rules for it.

        # Pre-populate the plugin_params field with default parameters
        if (
            self.instance
            and self.instance.ng_state_plugin
            and not self.instance.plugin_params
        ):
            default_params = self.instance.ng_state_plugin.default_plugin_params
            if default_params:
                self.initial["plugin_params"] = default_params


class TaskGenerationForm(forms.ModelForm):

    seg_table_csv = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6, "cols": 40}),
        help_text="Enter CSV-formatted rows of segmentation data: seg_id,x,y,z",
    )

    segmentation_layers = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Optional JSON list of layers with keys: name, source, fixed_ids, active",
    )

    em_zoom = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        initial=4.0,
        widget=forms.NumberInput(attrs={"step": 0.05}),
        help_text="Zoom level",
    )

    # resolution = forms.CharField(
    #     required=False,
    #     initial="8,8,33",
    #     help_text="Comma-separated voxel resolution, e.g. 8,8,33"
    # )

    alpha_selected = forms.FloatField(
        required=False,
        min_value=0,
        max_value=1,
        initial=0.6,
        widget=forms.NumberInput(attrs={"step": 0.05}),
        help_text="Opacity for selected layers",
    )

    alpha_3d = forms.FloatField(
        required=False,
        min_value=0,
        max_value=1,
        initial=0.3,
        widget=forms.NumberInput(attrs={"step": 0.05}),
        help_text="Opacity for 3D display",
    )

    img_source_other_name = forms.CharField(
        required=False, label="Custom Image Source Name"
    )

    img_source_other_url = forms.CharField(
        required=False, label="Custom Image Source URL"
    )

    pcg_source_other_name = forms.CharField(
        required=False, label="Custom PCG Source Name"
    )

    pcg_source_other_url = forms.CharField(
        required=False, label="Custom PCG Source URL"
    )

    class Meta:
        model = Namespace
        exclude = [
            "ng_state_plugin",
            "default_push_rule",
            "default_pull_rule",
            "plugin_params",
            "namespace_enabled",
        ]

    def clean_seg_table_csv(self):
        raw = (self.cleaned_data["seg_table_csv"] or "").strip()
        if not raw:
            raise forms.ValidationError(
                "Please enter CSV-formatted seg_ids and coordinates"
            )
        try:
            df = pd.read_csv(
                io.StringIO(raw),
                header=None,
                names=["seg_id", "x", "y", "z"],
                on_bad_lines="error",
                skip_blank_lines=True,
                skipinitialspace=True,
                dtype=str,
            )
        except Exception as e:
            raise forms.ValidationError(f"Invalid CSV: {e}")
        try:
            for c in ["seg_id", "x", "y", "z"]:
                df[c] = df[c].str.strip().astype("int64")
        except Exception:
            raise forms.ValidationError(
                "Please enter CSV-formatted seg_ids and coordinates"
            )

        self.cleaned_data["seg_table_df"] = df
        self.cleaned_data["seg_id_list"] = df["seg_id"].astype(int).tolist()
        return raw

    def clean_segmentation_layers(self):
        raw = (self.cleaned_data.get("segmentation_layers") or "").strip()
        if not raw:
            self.cleaned_data["segmentation_layers_list"] = []
            return "[]"
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise forms.ValidationError("Must be a list of layer configs.")
            for item in data:
                if not isinstance(item, dict):
                    raise forms.ValidationError("Each item must be a JSON object.")
                required_keys = {"name", "source", "fixed_ids", "active"}
                if not required_keys.issubset(item):
                    raise forms.ValidationError(
                        f"Each item must include: {', '.join(required_keys)}"
                    )
            self.cleaned_data["segmentation_layers_list"] = data
            return raw  # keep original JSON string for the model field if needed
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format.")
