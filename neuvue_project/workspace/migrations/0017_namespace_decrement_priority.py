# Generated by Django 3.2.7 on 2023-01-16 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "workspace",
            "0016_forcedchoicebuttongroup_number_of_selected_segments_expected",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="namespace",
            name="decrement_priority",
            field=models.IntegerField(
                default=100, verbose_name="When skipped, decrement priority by"
            ),
        ),
    ]
