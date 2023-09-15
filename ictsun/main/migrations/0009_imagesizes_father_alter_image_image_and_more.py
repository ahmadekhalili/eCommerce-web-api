# Generated by Django 4.0.3 on 2023-07-09 04:02

from django.db import migrations, models
import django.db.models.deletion
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_image_path_image_post_imagesizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagesizes',
            name='father',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='imagesizes', to='main.image', verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=main.models.image_path_selector, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='imagesizes',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=main.models.image_path_selector, verbose_name='image'),
        ),
    ]