# Generated by Django 3.2.7 on 2022-02-24 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0006_namespace_namespace_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="namespace",
            name="refresh_selected_root_ids",
            field=models.BooleanField(default=False),
        ),
    ]
