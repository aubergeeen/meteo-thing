# Generated by Django 4.2.21 on 2025-05-09 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0003_sensorseries_param_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensor',
            name='sensor_model_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sensors', to='stations.sensorseries'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='station_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sensors', to='stations.station'),
        ),
        migrations.AlterField(
            model_name='sensorseries',
            name='param_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='models', to='stations.parametertype'),
        ),
    ]
