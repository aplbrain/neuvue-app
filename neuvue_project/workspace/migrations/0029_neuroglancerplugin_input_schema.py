from django.db import migrations, models


NEURD_SEGMENT_ID_INPUT_SCHEMA = [
    {
        "name": "segment_id",
        "label": "Segment ID",
        "type": "text",
        "placeholder": "Paste segment ID",
        "required": True,
    }
]


def add_neurd_segment_id_input(apps, schema_editor):
    NeuroglancerPlugin = apps.get_model("workspace", "NeuroglancerPlugin")
    NeuroglancerPlugin.objects.filter(name="Neurd Skeleton Points").update(
        input_schema=NEURD_SEGMENT_ID_INPUT_SCHEMA
    )


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0028_alter_datastack_source_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="neuroglancerplugin",
            name="input_schema",
            field=models.JSONField(
                blank=True,
                help_text=(
                    "List of workspace input definitions for this plugin. Each "
                    "item can include name, label, type, placeholder, default, "
                    "and required."
                ),
                null=True,
            ),
        ),
        migrations.RunPython(
            add_neurd_segment_id_input,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
