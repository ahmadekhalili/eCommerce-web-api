# Generated by Django 4.0.3 on 2022-04-27 03:25

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_alter_product_detailed_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='detailed_description',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='detailed description'),
        ),
    ]
