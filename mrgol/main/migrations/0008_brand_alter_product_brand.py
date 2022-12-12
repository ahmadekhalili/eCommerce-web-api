# Generated by Django 4.0.3 on 2022-03-23 23:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_product_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=25, null=True, verbose_name='name')),
                ('slug', models.SlugField(allow_unicode=True, db_index=False, verbose_name='slug')),
            ],
        ),
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(blank=True, max_length=25, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.brand', verbose_name='brand'),
        ),
    ]
