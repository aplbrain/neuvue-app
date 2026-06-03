from django.db import migrations, models


PALETTE = {
    "blue": "#2563eb",
    "cyan": "#0891b2",
    "emerald": "#059669",
    "lime": "#65a30d",
    "amber": "#ca8a04",
    "orange": "#ea580c",
    "red": "#dc2626",
    "pink": "#db2777",
    "purple": "#9333ea",
    "indigo": "#4f46e5",
    "teal": "#0f766e",
    "green": "#15803d",
    "ochre": "#a16207",
    "rose": "#be123c",
    "slate": "#475569",
}


def hex_to_rgb(value):
    if not value:
        return None

    value = str(value).strip().lstrip("#")
    if len(value) == 8:
        value = value[:6]
    if len(value) != 6:
        return None

    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def nearest_palette_color(value):
    source_rgb = hex_to_rgb(value)
    if source_rgb is None:
        return "blue"

    best_key = "blue"
    best_distance = None
    for key, palette_value in PALETTE.items():
        palette_rgb = hex_to_rgb(palette_value)
        distance = sum((source - target) ** 2 for source, target in zip(source_rgb, palette_rgb))
        if best_distance is None or distance < best_distance:
            best_key = key
            best_distance = distance

    return best_key


def migrate_button_colors(apps, schema_editor):
    ForcedChoiceButton = apps.get_model("workspace", "ForcedChoiceButton")
    for button in ForcedChoiceButton.objects.all():
        button.palette_color = nearest_palette_color(getattr(button, "button_color", None))
        button.save(update_fields=["palette_color"])


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0029_neuroglancerplugin_input_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="recent_tags",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="forcedchoicebutton",
            name="palette_color",
            field=models.CharField(
                choices=[
                    ("blue", "Blue"),
                    ("cyan", "Cyan"),
                    ("emerald", "Emerald"),
                    ("lime", "Lime"),
                    ("amber", "Amber"),
                    ("orange", "Orange"),
                    ("red", "Red"),
                    ("pink", "Pink"),
                    ("purple", "Purple"),
                    ("indigo", "Indigo"),
                    ("teal", "Teal"),
                    ("green", "Green"),
                    ("ochre", "Ochre"),
                    ("rose", "Rose"),
                    ("slate", "Slate"),
                ],
                default="blue",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_button_colors, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="forcedchoicebutton",
            name="button_color",
        ),
        migrations.RemoveField(
            model_name="forcedchoicebutton",
            name="button_color_active",
        ),
    ]
