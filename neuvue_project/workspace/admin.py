from django.contrib import admin
from .models import ForcedChoiceButtonGroup, ForcedChoiceButton, Namespace, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.unregister(User)

class ButtonsInline(admin.TabularInline):
    model = ForcedChoiceButton
    verbose_name = "forced choice button"
    verbose_name_plural = "forced choice buttons"
    extra = 1
    max_num = 8

@admin.register(ForcedChoiceButtonGroup)
class ForcedChoiceAdmin(admin.ModelAdmin):
    inlines = (ButtonsInline, )    

class NamespaceAdmin(admin.ModelAdmin):
    list_display = ('namespace', 'namespace_enabled')
    fieldsets = [
        ('Namespace Information',               {'fields': ['namespace_enabled', 'namespace', 'display_name', 'ng_link_type', 'submission_method', 'pcg_source',
                                                'img_source', 'track_operation_ids', 'refresh_selected_root_ids', 'number_of_tasks_users_can_self_assign', 'max_number_of_pending_tasks_per_user']}),
        ('Novice Fields', {'fields': ['novice_pull_from', 'novice_push_to']}),
        ('Intermediate Fields', {'fields': ['intermediate_pull_from', 'intermediate_push_to']}),
        ('Expert Fields', {'fields': ['expert_pull_from', 'expert_push_to']}),
    ]

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    filter_horizontal = ('intermediate_namespaces', 'expert_namespaces')

class CustomUserAdmin(UserAdmin):
    #filter_horizontal = ('user_permissions', 'groups', 'ope')
    save_on_top = True
    fieldsets = [('User Information', {'fields': ['username', 'password']}),
        ('Personal Info', {'fields': ['first_name', 'last_name', 'email']}),
        ('Important Dates', {'fields': ['last_login', 'date_joined']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser','groups', 'user_permissions']}),
    ]
    inlines = [UserProfileInline]

    

# Register your models here.
admin.site.register(Namespace, NamespaceAdmin)
admin.site.register(User, CustomUserAdmin)