# Generated by Django 3.2.7 on 2022-06-17 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preferences', '0007_auto_20220603_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='enable_sound',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='config',
            name='enable_sound_switch',
            field=models.BooleanField(default=False),
        ),
    ]