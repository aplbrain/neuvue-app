from django.db import migrations, models


IMAGE_SOURCE_PREFIXES = ("precomputed://",)
SEGMENTATION_SOURCE_PREFIXES = ("graphene://", "precomputed://")


def add_explicit_layer_source_prefixes(apps, schema_editor):
    Datastack = apps.get_model("workspace", "Datastack")
    for datastack in Datastack.objects.all():
        changed = False
        if datastack.image_source and not datastack.image_source.startswith(
            IMAGE_SOURCE_PREFIXES
        ):
            datastack.image_source = f"precomputed://{datastack.image_source}"
            changed = True

        if (
            datastack.segmentation_source
            and not datastack.segmentation_source.startswith(
                SEGMENTATION_SOURCE_PREFIXES
            )
        ):
            datastack.segmentation_source = (
                f"graphene://{datastack.segmentation_source}"
            )
            changed = True

        if changed:
            datastack.save(update_fields=["image_source", "segmentation_source"])


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0027_datastack_namespace_datastack"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datastack",
            name="image_source",
            field=models.CharField(
                help_text=(
                    "Full Neuroglancer image layer source, including the layer type "
                    "(e.g., precomputed://s3://bucket/path/to/layer)"
                ),
                max_length=1000,
            ),
        ),
        migrations.AlterField(
            model_name="datastack",
            name="segmentation_source",
            field=models.CharField(
                help_text=(
                    "Full Neuroglancer segmentation layer source, including the "
                    "layer type (e.g., graphene://https://... or "
                    "precomputed://s3://bucket/path/to/layer)"
                ),
                max_length=1000,
            ),
        ),
        migrations.RunPython(
            add_explicit_layer_source_prefixes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
