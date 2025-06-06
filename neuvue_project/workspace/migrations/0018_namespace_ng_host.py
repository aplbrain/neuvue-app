# Generated by Django 3.2.7 on 2023-03-14 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0017_namespace_decrement_priority"),
    ]

    operations = [
        migrations.AddField(
            model_name="namespace",
            name="ng_host",
            field=models.CharField(
                choices=[
                    ("neuvue", "NeuVue Built-in"),
                    ("https://neuroglancer.bossdb.io", "neuroglancer.bossdb.io"),
                    ("https://clio-ng.janelia.org", "clio-ng.janelia.org"),
                ],
                default="neuvue",
                max_length=100,
            ),
        ),
    ]
