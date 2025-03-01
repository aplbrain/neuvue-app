# Generated by Django 3.2.7 on 2022-06-11 17:00

import colorfield.fields
from django.db import migrations, models
import django.db.models.deletion
import workspace.validators


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0012_alter_namespace_submission_method"),
    ]

    operations = [
        migrations.CreateModel(
            name="ForcedChoiceButtonGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "group_name",
                    models.CharField(
                        help_text="(snake case)", max_length=100, unique=True
                    ),
                ),
                ("submit_task_button", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Forced Choice Button Group",
                "verbose_name_plural": "Forced Choice Button Groups",
            },
        ),
        migrations.CreateModel(
            name="ForcedChoiceButton",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("display_name", models.CharField(max_length=100)),
                (
                    "submission_value",
                    models.CharField(
                        max_length=100,
                        validators=[workspace.validators.validate_submission_value],
                    ),
                ),
                (
                    "button_color",
                    colorfield.fields.ColorField(
                        default="#FFFFFFFF",
                        image_field=None,
                        max_length=18,
                        samples=None,
                    ),
                ),
                (
                    "button_color_active",
                    colorfield.fields.ColorField(
                        default="#FFFFFFFF",
                        image_field=None,
                        max_length=18,
                        samples=None,
                    ),
                ),
                (
                    "set_name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="workspace.forcedchoicebuttongroup",
                        to_field="group_name",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="namespace",
            name="submission_method",
            field=models.ForeignKey(
                blank=True,
                db_column="submission_method",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="workspace.forcedchoicebuttongroup",
                to_field="group_name",
            ),
        ),
    ]
