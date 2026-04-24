from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0027_forcedchoicebutton_selection_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="forcedchoicebuttongroup",
            name="require_all_selection_groups",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "When enabled, one button must be selected in every "
                    "selection group before the task can be submitted."
                ),
            ),
        ),
    ]
