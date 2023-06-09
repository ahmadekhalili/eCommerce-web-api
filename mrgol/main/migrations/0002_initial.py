# Generated by Django 4.0.3 on 2023-06-03 14:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='written_posts', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='post',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.category', verbose_name='category'),
        ),
        migrations.AddField(
            model_name='post',
            name='image_icon',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.image_icon', verbose_name='image icon'),
        ),
        migrations.AddField(
            model_name='image',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.product', verbose_name='product'),
        ),
        migrations.AddField(
            model_name='filter_attribute',
            name='filterr',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filter_attributes', to='main.filter', verbose_name='filter'),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='written_comments', related_query_name='comments_author', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.post', verbose_name='post'),
        ),
        migrations.AddField(
            model_name='comment',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.product', verbose_name='product'),
        ),
        migrations.AddField(
            model_name='comment',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_comments', related_query_name='comments_reviewer', to=settings.AUTH_USER_MODEL, verbose_name='reviewer'),
        ),
        migrations.AddField(
            model_name='category',
            name='brands',
            field=models.ManyToManyField(blank=True, to='main.brand', verbose_name='brands'),
        ),
        migrations.AddField(
            model_name='category',
            name='father_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_categories', related_query_name='childs', to='main.category', verbose_name='father category'),
        ),
        migrations.AddField(
            model_name='category',
            name='filters',
            field=models.ManyToManyField(blank=True, to='main.filter', verbose_name='filters'),
        ),
    ]
