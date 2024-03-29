# Generated by Django 3.2.7 on 2021-11-19 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Namespace",
            fields=[
                (
                    "namespace",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("display_name", models.CharField(max_length=100)),
                (
                    "ng_link_type",
                    models.CharField(
                        choices=[
                            ("path", "Path Layer"),
                            ("point", "Annotation Layer"),
                            ("pregen", "Pregenerated"),
                        ],
                        default="point",
                        max_length=50,
                    ),
                ),
                (
                    "submission_method",
                    models.CharField(
                        choices=[
                            ("submit", "Submit Button"),
                            ("forced_choice", "Yes/No/Maybe Button"),
                        ],
                        default="submit",
                        max_length=50,
                    ),
                ),
            ],
        ),
    ]
