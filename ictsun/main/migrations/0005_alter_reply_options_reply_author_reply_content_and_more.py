# Generated by Django 5.0.6 on 2024-05-25 09:28

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_remove_brand_name_en_remove_brand_name_fa_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reply',
            options={'verbose_name': 'Reply', 'verbose_name_plural': 'Replies'},
        ),
        migrations.AddField(
            model_name='reply',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='written_replies', related_query_name='reply_author', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='reply',
            name='content',
            field=models.TextField(default='', validators=[django.core.validators.MaxLengthValidator(500)], verbose_name='content'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reply',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='reply',
            name='name',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='reply',
            name='published_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='published date'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reply',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_replies', related_query_name='reply_reviewer', to=settings.AUTH_USER_MODEL, verbose_name='reviewer'),
        ),
        migrations.AddField(
            model_name='reply',
            name='status',
            field=models.CharField(choices=[('1', 'not checked'), ('2', 'confirmed'), ('3', 'not confirmed'), ('4', 'deleted')], default='1', max_length=1, verbose_name='status'),
        ),
    ]