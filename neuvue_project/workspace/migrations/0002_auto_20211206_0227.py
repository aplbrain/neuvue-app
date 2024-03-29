# Generated by Django 3.2.7 on 2021-12-06 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="namespace",
            name="img_source",
            field=models.CharField(
                choices=[
                    (
                        "https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em",
                        "Minnie65",
                    ),
                    (
                        "gs://microns_public_datasets/pinky100_v0/son_of_alignment_v15_rechunked",
                        "Pinky",
                    ),
                ],
                default="https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/minnie65/em",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="namespace",
            name="pcg_source",
            field=models.CharField(
                choices=[
                    (
                        "https://minnie.microns-daf.com/segmentation/table/minnie3_v1",
                        "Minnie65",
                    ),
                    (
                        "https://minnie.microns-daf.com/segmentation/table/pinky_nf_v2",
                        "Pinky",
                    ),
                ],
                default="https://minnie.microns-daf.com/segmentation/table/minnie3_v1",
                max_length=300,
            ),
        ),
    ]
