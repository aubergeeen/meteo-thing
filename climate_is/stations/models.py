from django.contrib.postgres.fields import IntegerRangeField, DecimalRangeField
from django.db import models
# ORM 
# модели = таблицы в БД 

class SoilTypes(models.TextChoices):
    PEAT = 'PT', 'Торфяные'                       
    PODZOL = 'PD', 'Подзолистые'               
    GRAY_FOREST = 'GF', 'Серые лесные'     
    CLAY_LOAM = 'CL', 'Глинистые/суглинки'   
    SANDY_LOAM = 'SL', 'Песчаные/супеси'    
    URBAN = 'UR', 'Урбанизированные'             
    MOUNTAIN = 'MT', 'Горные'                 
    FLOODPLAIN = 'FP', 'Пойменные'          

#  метеостанция
class Station(models.Model):
    # ENUM для типов подстилающей поверхности
    station_id = models.AutoField(
        primary_key=True,
        help_text="ID станции"
    )
    name = models.CharField(
        max_length=255,
        help_text="Название станции"
    )
    description = models.TextField(
        help_text="Описание",
        blank=True
    )    
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Координаты: Широта"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Координаты: Долгота"
    )
    elevation = models.FloatField(
        help_text="Высота над уровнем моря"
    )
    soil_type = models.CharField(
        max_length=10,
        choices=SoilTypes.choices,
        default=SoilTypes.PODZOL
    )
    class Meta:
        db_table = "Stations"
        verbose_name = "Метеостанция"
        verbose_name_plural = "Метеостанции"
        indexes = [
            models.Index(fields=['latitude', 'longitude'], name='stations_lat_lon_idx'),
            models.Index(fields=['name'], name='stations_name_idx'),
        ]
    def __str__(self):
        return f"({self.station_id}) {self.name}"

# метеопараметр
class ParameterType(models.Model):
    param_id = models.AutoField(
        primary_key=True,
        help_text="ID метеопараметра"
    )
    name = models.CharField(
        max_length=50,
        help_text="Название метеопараметра"
    )
    unit = models.CharField(
        max_length=20,
        help_text="Ед. измерения"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Аббревиация"
    )
    class Meta:
        db_table = "Parameters"
        verbose_name = "Тип метеопараметра"
        verbose_name_plural = "Типы метеопараметров"
    def __str__(self):
        return f"{self.name} ({self.unit})"
        
# модель(серия) датчика 
class SensorSeries(models.Model):
    series_id = models.AutoField(
        primary_key=True,
        help_text="ID модели датчика"
    )
    series_name = models.CharField(
        max_length=255,
        help_text="Название модели датчика"
    )
    manufacturer = models.CharField(
        max_length=255,
        help_text="Название производителя"
    )
    precision = models.DecimalField(
        decimal_places=8,
        max_digits=10,
        help_text="Погрешность измерения"
    )
    # min_max = IntegerRangeField()   # диапазон значений
    value_range = DecimalRangeField()   
    param_type = models.ForeignKey(
        ParameterType,
        related_name="models",  # имя обратной связи от модели Метеопараметр к Моделям датчиков.
        on_delete=models.PROTECT
    )
    class Meta:
        db_table = "Sensor_Series"
        verbose_name = "Модель датчика"
        verbose_name_plural = "Модели датчиков"
        indexes = [
            models.Index(fields=['param_type_id'], name='sensor_series_param_type_idx'),
        ]
    def __str__(self):
        return f"{self.series_name} - {self.param_type})"

#  датчик
class Sensor(models.Model):
    sensor_id = models.AutoField(
        primary_key=True,
        help_text="ID датчика"
    )
    last_spoke = models.DateTimeField(
        help_text="Дата и время последнего показания"
    )
    # внешний ключ -> станция(id)
    station = models.ForeignKey(
        Station,
        related_name="sensors", 
        on_delete=models.PROTECT
    )
    sensor_model = models.ForeignKey(
        SensorSeries,
        related_name="sensors",
        on_delete=models.PROTECT
    )
    class Meta:
        db_table = "Sensors"
        verbose_name = "Датчик"
        verbose_name_plural = "Датчики"
        indexes = [
            models.Index(fields=['station_id'], name='sensors_station_id_idx'),
            models.Index(fields=['sensor_model_id'], name='sensors_model_id_idx'),
            models.Index(fields=['station_id', 'sensor_model_id'], name='sensors_station_model_idx'),
        ]
    
    def __str__(self):
        return f"{self.sensor_id}"
