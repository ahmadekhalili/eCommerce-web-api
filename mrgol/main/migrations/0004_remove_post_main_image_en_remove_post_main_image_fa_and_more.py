# Generated by Django 4.0.3 on 2023-06-08 15:33

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_post_image_icon_post_main_image_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='main_image_en',
        ),
        migrations.RemoveField(
            model_name='post',
            name='main_image_fa',
        ),
        migrations.RemoveField(
            model_name='post',
            name='tags_en',
        ),
        migrations.RemoveField(
            model_name='post',
            name='tags_fa',
        ),
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=30), size=None),
        ),
    ]
