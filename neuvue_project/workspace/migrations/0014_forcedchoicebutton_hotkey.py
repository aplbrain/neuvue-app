# Generated by Django 3.2.7 on 2022-06-27 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0013_auto_20220611_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='forcedchoicebutton',
            name='hotkey',
            field=models.CharField(blank=True, choices=[('c', 'C'), ('d', 'D'), ('j', 'J'), ('m', 'M'), ('q', 'Q'), ('r', 'R'), ('t', 'T'), ('v', 'V'), ('w', 'W'), ('y', 'Y'), ('z', 'Z')], max_length=300, null=True),
        ),
    ]