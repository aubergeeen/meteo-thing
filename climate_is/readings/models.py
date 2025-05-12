from django.db import models
from stations.models import Sensor  # импортируем модель Датчик из модуля stations

class Reading(models.Model):
    timestamp = models.DateTimeField(help_text="Дата и время наблюдения")
    sensor = models.ForeignKey(
        Sensor, 
        on_delete=models.PROTECT, 
        related_name='readings', 
        help_text="ID Датчика")
    value = models.FloatField(help_text="Значение")
    
    class Meta:
        db_table = "Readings"
        verbose_name = "Наблюдение"
        verbose_name_plural = "Наблюдения"
    def __str__(self):
        return f"{self.sensor.station_id}\t{self.sensor.sensor_model.param_type}\t{self.timestamp}:\t{self.value}"