from django.contrib import admin
from .models import ForcedChoiceButtonGroup, ForcedChoiceButton, Namespace, UserProfile
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django import forms
from django.contrib import messages

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


class NamespaceAdmin(admin.ModelAdmin):
    list_display = ("namespace", "namespace_enabled")
    fieldsets = [
        (
            "Namespace Information",
            {
                "fields": [
                    "namespace_enabled",
                    "namespace",
                    "display_name",
                    "ng_link_type",
                    "submission_method",
                    "pcg_source",
                    "img_source",
                    "track_operation_ids",
                    "refresh_selected_root_ids",
                    "number_of_tasks_users_can_self_assign",
                    "max_number_of_pending_tasks_per_user",
                    "track_selected_segments",
                    "decrement_priority"
                ]
            },
        ),
        ("Novice Fields", {"fields": ["novice_pull_from", "novice_push_to"]}),
        (
            "Intermediate Fields",
            {"fields": ["intermediate_pull_from", "intermediate_push_to"]},
        ),
        ("Expert Fields", {"fields": ["expert_pull_from", "expert_push_to"]}),
    ]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    filter_horizontal = ("intermediate_namespaces", "expert_namespaces")


class CustomUserAdmin(UserAdmin):
    # filter_horizontal = ('user_permissions', 'groups', 'ope')
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


NOVICE = "novice"
INTERMEDIATE = "intermediate"
EXPERT = "expert"


class SetExpertiseLevelForNamespaceForm(admin.helpers.ActionForm):
    namespace = forms.ModelChoiceField(
        Namespace.objects,
        label=False,
        empty_label="Namespace",
        widget=forms.Select(attrs={"class": "mb-1"}),
        required=False,
    )


class CustomGroupAdmin(GroupAdmin):
    action_form = SetExpertiseLevelForNamespaceForm
    actions = [
        "set_expertise_level_for_namespace_novice",
        "set_expertise_level_for_namespace_intermediate",
        "set_expertise_level_for_namespace_expert",
    ]

    def set_expertise_level_for_namespace_novice(self, request, queryset):
        self.set_expertise_level_for_namespace(NOVICE, request, queryset)

    def set_expertise_level_for_namespace_intermediate(self, request, queryset):
        self.set_expertise_level_for_namespace(INTERMEDIATE, request, queryset)

    def set_expertise_level_for_namespace_expert(self, request, queryset):
        self.set_expertise_level_for_namespace(EXPERT, request, queryset)

    def set_expertise_level_for_namespace(self, level, request, queryset):

        namespace = ""
        try:
            namespace = Namespace.objects.get(namespace=request.POST["namespace"])
        except:
            messages.error(request, "Please select a namespace.")
            return

        for group in queryset:
            users = Group.objects.get(name=group).user_set.all()
            for user in users:
                userProfile, _ = UserProfile.objects.get_or_create(user=user)
                if level == NOVICE:
                    userProfile.intermediate_namespaces.remove(namespace)
                    userProfile.expert_namespaces.remove(namespace)
                if level == INTERMEDIATE:
                    userProfile.intermediate_namespaces.add(namespace)
                    userProfile.expert_namespaces.remove(namespace)
                if level == EXPERT:
                    userProfile.intermediate_namespaces.remove(namespace)
                    userProfile.expert_namespaces.add(namespace)
        messages.success(
            request,
            "Designated all members of {} as {} for {}".format(
                ", ".join([q.name for q in queryset]), level, namespace
            ),
        )

    set_expertise_level_for_namespace_novice.short_description = (
        "Assign all members of group as novice for namespace"
    )
    set_expertise_level_for_namespace_intermediate.short_description = (
        "Assign all members of group as intermediate for namespace"
    )
    set_expertise_level_for_namespace_expert.short_description = (
        "Assign all members of group as expert for namespace"
    )


# Register your models here.
admin.site.register(Namespace, NamespaceAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)
