# Generated by Django 3.2.7 on 2022-08-12 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0015_namespace_track_selected_segments"),
    ]

    operations = [
        migrations.AddField(
            model_name="forcedchoicebuttongroup",
            name="number_of_selected_segments_expected",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
