from django import forms
from .models import Namespace, NamespaceRule, TaskBucketActions


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
