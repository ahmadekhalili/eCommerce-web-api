# Generated by Django 4.0.3 on 2022-04-06 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_brand_options_alter_product_brand'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='group',
            field=models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], default=1, verbose_name='group'),
            preserve_default=False,
        ),
    ]