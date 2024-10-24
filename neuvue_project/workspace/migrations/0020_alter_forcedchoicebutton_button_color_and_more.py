# Generated by Django 4.2.11 on 2024-03-19 13:55

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0019_auto_20230328_0926"),
    ]

    operations = [
        migrations.AlterField(
            model_name="forcedchoicebutton",
            name="button_color",
            field=colorfield.fields.ColorField(
                default="#FFFFFFFF", image_field=None, max_length=25, samples=None
            ),
        ),
        migrations.AlterField(
            model_name="forcedchoicebutton",
            name="button_color_active",
            field=colorfield.fields.ColorField(
                default="#FFFFFFFF", image_field=None, max_length=25, samples=None
            ),
        ),
    ]
