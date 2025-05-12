from django.contrib import admin
from .models import Sensor, SensorSeries, Station, ParameterType

# Register your models here.
admin.site.register(Sensor)
admin.site.register(SensorSeries)
admin.site.register(Station)
admin.site.register(ParameterType)