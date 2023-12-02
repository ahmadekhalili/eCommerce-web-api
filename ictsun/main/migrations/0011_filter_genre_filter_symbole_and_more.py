# Generated by Django 4.0.3 on 2023-12-02 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_imagesizes_alt_en_imagesizes_alt_fa'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='genre',
            field=models.CharField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], default='', max_length=25, verbose_name='genre'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filter',
            name='symbole',
            field=models.CharField(choices=[('None', 'None'), ('icon', 'icon'), ('color', 'color')], default='', max_length=25, verbose_name='symbole'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filter_attribute',
            name='symbole_value',
            field=models.CharField(default='', max_length=255, verbose_name='symbole value'),
            preserve_default=False,
        ),
    ]
