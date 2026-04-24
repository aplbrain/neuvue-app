from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0026_neuroglancerplugin_namespace_plugin_params_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="forcedchoicebutton",
            name="selection_group",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional subgroup name. Buttons in the same subgroup are "
                    "mutually exclusive, while different subgroups can each "
                    "have one selection."
                ),
                max_length=100,
            ),
        ),
    ]
