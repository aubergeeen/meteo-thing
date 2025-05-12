# A model class represents a database table, and an instance of that class represents a particular record in the database table.
# To create an object, instantiate it using keyword arguments to the model class, then call save() to save it to the database.
from django.db import migrations
from django.utils import timezone
import datetime
import random

def paste_dummy_temps(apps, schema_editor): # We can't import the model directly as it may be a newer version => use historical
    Reading = apps.get_model("readings", "Reading")  # получаем модель датчика
    Sensor = apps.get_model("stations", "Sensor")  # получаем модель датчика   
    temp_sens = Sensor.objects.filter(sensor_model_id__param_type__name="Температура воздуха") # получили все датчики температуры
    
    start = datetime.datetime(2024, 3, 1, 12, 0) # задаем дату начала
    values = [ 3 + x*0.3 + random.uniform(-3, 3) for x in range (0, 30)]
    timestamps = [ start + datetime.timedelta(days=x) for x in range(0, 30)]
    readings_to_make = []

    for i in range(0, 30):
        for cur_sensor in temp_sens:
            readings_to_make.append(
                Reading(
                    timestamp = timestamps[i],
                    sensor = cur_sensor,
                    value = values[i]
                ))
    Reading.objects.bulk_create(readings_to_make)

    print("Данные успешно созданы")


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0002_alter_reading_options'),
        ('stations', '0003_sensorseries_param_type')
    ]

    operations = [
        migrations.RunPython(paste_dummy_temps),
    ]
