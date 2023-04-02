# Generated by Django 4.0.3 on 2023-02-28 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_brand_name_en_brand_name_fa_brand_slug_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='alt_en',
            field=models.CharField(default='', max_length=55, null=True, unique=True, verbose_name='alt'),
        ),
        migrations.AddField(
            model_name='image',
            name='alt_fa',
            field=models.CharField(default='', max_length=55, null=True, unique=True, verbose_name='alt'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='available_en',
            field=models.BooleanField(db_index=True, default=False, verbose_name='available'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='available_fa',
            field=models.BooleanField(db_index=True, default=False, verbose_name='available'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='previous_stock_en',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='previous_stock_fa',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='price_en',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='price'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='price_fa',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='price'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='stock_en',
            field=models.PositiveIntegerField(null=True, verbose_name='stock'),
        ),
        migrations.AddField(
            model_name='shopfilteritem',
            name='stock_fa',
            field=models.PositiveIntegerField(null=True, verbose_name='stock'),
        ),
        migrations.AddField(
            model_name='smallimage',
            name='alt_en',
            field=models.CharField(blank=True, default='', max_length=55, null=True, verbose_name='alt'),
        ),
        migrations.AddField(
            model_name='smallimage',
            name='alt_fa',
            field=models.CharField(blank=True, default='', max_length=55, null=True, verbose_name='alt'),
        ),
        migrations.AddField(
            model_name='state',
            name='name_en',
            field=models.CharField(max_length=30, null=True, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='state',
            name='name_fa',
            field=models.CharField(max_length=30, null=True, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='town',
            name='name_en',
            field=models.CharField(max_length=30, null=True, verbose_name='name'),
        ),
        migrations.AddField(
            model_name='town',
            name='name_fa',
            field=models.CharField(max_length=30, null=True, verbose_name='name'),
        ),
    ]
