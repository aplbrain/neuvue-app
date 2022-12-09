from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name="in_group")
def in_group(user, group_name):
    try:
        Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False

    return user.groups.filter(name=group_name).exists()
