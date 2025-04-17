from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import ForcedChoiceButtonGroup, ForcedChoiceButton, Namespace, UserProfile, GroupProfile, TaskBucket, NamespaceRule
from .forms import NamespaceAdminForm
admin.site.unregister(User)
admin.site.unregister(Group)


class ButtonsInline(admin.TabularInline):
    model = ForcedChoiceButton
    verbose_name = "forced choice button"
    verbose_name_plural = "forced choice buttons"
    extra = 1
    max_num = 8


@admin.register(ForcedChoiceButtonGroup)
class ForcedChoiceAdmin(admin.ModelAdmin):
    inlines = (ButtonsInline,)


@admin.register(TaskBucket)
class TaskBucketAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)

@admin.register(NamespaceRule)
class NamespaceRuleAdmin(admin.ModelAdmin):
    list_display = ("namespace", "action", "task_bucket" )
    search_fields = ("namespace__namespace", "task_bucket__name")
    list_filter = ("namespace", "task_bucket",)


@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    form = NamespaceAdminForm
    list_display = ("namespace", "display_name", "namespace_enabled")
    search_fields = ("namespace", "display_name")
    list_filter = ("namespace_enabled",)
    fieldsets = [
        (
            "Namespace Information",
            {
                "fields": [
                    "namespace_enabled",
                    "namespace",
                    "display_name",
                    "ng_link_type",
                    "ng_host",
                    "submission_method",
                    "pcg_source",
                    "img_source",
                    "track_operation_ids",
                    "refresh_selected_root_ids",
                    "number_of_tasks_users_can_self_assign",
                    "max_number_of_pending_tasks_per_user",
                    "track_selected_segments",
                    "decrement_priority",
                    "is_demo",
                    "ng_state_plugin"
                ]
            },
        ),
        (
            "Default Rules",
            {
                "fields": ["default_push_rule", "default_pull_rule"],
            },
        ),
    ]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    filter_horizontal = ("namespace_rule",)

    # readonly_fields = ("inherited_namespace_rules_display",)
    # def inherited_namespace_rules_display(self, obj):
    #     if obj and obj.userprofile.inherited_namespace_rules.exists():
    #         rules = obj.userprofile.inherited_namespace_rules
    #         return ", ".join([str(rule) for rule in rules])
    #     return "None"
    # inherited_namespace_rules_display.short_description = "Inherited Namespace Rules"

class GroupProfileInline(admin.StackedInline):
    model = GroupProfile
    filter_horizontal = ("namespace_rule",)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    save_on_top = True
    fieldsets = [
        ("User Information", {"fields": ["username", "password"]}),
        ("Personal Info", {"fields": ["first_name", "last_name", "email"]}),
        ("Important Dates", {"fields": ["last_login", "date_joined"]}),
        (
            "Permissions",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
    ]
    inlines = [UserProfileInline]

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    inlines = [GroupProfileInline]

