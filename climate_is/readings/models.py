from django.db import models
from django.utils import timezone
from stations.models import Sensor  # импортируем модель Датчик из модуля stations
from django.db.models import Avg, Max, Min, Sum, Count, F
from django.db.models.functions import TruncWeek, TruncDay, TruncMonth, TruncYear

class ReadingQuerySet(models.QuerySet):
    # TOTAL !! все станции в кучу, группировка по интервалу времени
    def time_aggregates(self, param_type, aggregate_func='avg', period='week', group_by_station=False):
        # получаем Trunc и агрегат. ф-ии в соответсвии с переданым параметром
        aggregates = { 'avg': Avg, 'min': Min, 'max': Max, }
        period_functions = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear, }
        
        # валидация 
        if aggregate_func.lower() not in aggregates:
            raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
        if period.lower() not in period_functions:
            raise ValueError(f"Unsupported time period: {period}")
        
        trunc_func = period_functions[period.lower()]
        aggregation = aggregates[aggregate_func.lower()]
        
        group_fields = ['time_period']
        if group_by_station==True:
            group_fields += ['station_id']  # lol this goes nowhere
        # собираем запрос
        return (
            self                                                
            .filter(sensor__sensor_model__param_type=param_type)    # where и inner join'ы
            .annotate(time_period=trunc_func('timestamp'), station_id=F('sensor__station__station_id'),)               # date_trunc('time) as time_period
            .values('time_period')                                  # group by time_period (returns a QuerySet that returns dictionaries
            .annotate(value=aggregation('value'))                   # avg('value') as 'value'                 
            .order_by('time_period')                                # сортировка
        )

class ReadingManager(models.Manager):
    def get_queryset(self):
        return ReadingQuerySet(self.model, using=self._db)

    def time_aggregates(self, *args, **kwargs):
        return self.get_queryset().time_aggregates(*args, **kwargs)

class Reading(models.Model):
    objects = ReadingManager()
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
    
    # возвращает tuple (is_valid, error_message, sensor)
    @classmethod
    def validate_reading_by_param_type(cls, station_id, param_type_id, value, timestamp=None):
        try:
            # Находим датчик этого типа параметра на указанной станции
            sensor = Sensor.objects.select_related('sensor_model').get(
                station_id=station_id,
                sensor_model__param_type_id=param_type_id
            )
            sensor_model = sensor.sensor_model
            
            # Проверка диапазона значений
            value_range = sensor_model.value_range
            if value_range.lower is not None and value < value_range.lower:
                return False, f"Значение {value} ниже минимального {value_range.lower}", None
            if value_range.upper is not None and value > value_range.upper:
                return False, f"Значение {value} выше максимального {value_range.upper}", None
            
            # Проверка времени (если передано)
            if timestamp:
                if sensor.last_spoke and timestamp < sensor.last_spoke:
                    return False, f"Время показания {timestamp} раньше последнего {sensor.last_spoke}", None
            
            return True, None, sensor
        except Sensor.DoesNotExist:
            return False, f"На станции {station_id} не найден датчик для параметра {param_type_id}", None
        except Exception as e:
            return False, f"Ошибка валидации: {str(e)}", None
    
    # создает показание (после валидации)
    @classmethod
    def create_validated_reading_by_param_type(cls, station_id, param_type_id, value, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()
        
        is_valid, error, sensor = cls.validate_reading_by_param_type(
            station_id=station_id,
            param_type_id=param_type_id,
            value=value,
            timestamp=timestamp
        )
        if not is_valid:
            return None, error
        try:
            reading = cls.objects.create(
                sensor=sensor,
                value=value,
                timestamp=timestamp
            )
            # Обновляем время последнего показания датчика
            sensor.last_spoke = timestamp
            sensor.save()
            
            return reading, None
        except Exception as e:
            return None, f"Ошибка при сохранении: {str(e)}"