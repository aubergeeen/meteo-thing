# Generated by Django 4.2.21 on 2025-06-14 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0008_parametertype_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parametertype',
            name='code',
            field=models.CharField(help_text='Аббревиация', max_length=20, unique=True),
        ),
    ]
