from django.db import models
from django.utils import timezone
from stations.models import Sensor  
from django.db.models import Avg, Max, Min, Sum, Count, F
from django.db.models.functions import TruncWeek, TruncDay, TruncMonth, TruncYear, Coalesce, Concat
from django.db.models.expressions import ExpressionWrapper, Case, When, Value, Subquery
from django.db.models import FloatField, CharField
from datetime import timedelta

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
    
    def time_aggregates_by_code(self, sensor_ids, param_code, aggregate_func='avg', period='day'):
        # Агрегация данных по коду параметра для списка датчиков
        aggregates = {'avg': Avg, 'min': Min, 'max': Max}
        period_functions = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear}
        
        if aggregate_func.lower() not in aggregates:
            raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
        if period.lower() not in period_functions:
            raise ValueError(f"Unsupported time period: {period}")
        
        trunc_func = period_functions[period.lower()]
        aggregation = aggregates[aggregate_func.lower()]
        
        return (
            self
            .filter(
                sensor__sensor_id__in=sensor_ids,
                sensor__sensor_model__param_type__code=param_code
            )
            .annotate(period=trunc_func('timestamp'))
            .values('period')
            .annotate(value=aggregation('value'))
            .order_by('period')
        )

    # Вычисляет UTCI на основе агрегированного QuerySet
    def get_utci(self, qs):
        return qs.annotate(
            utci=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) +
                0.1 * Coalesce(F('humidity'), Value(0.0)) - Value(5.0),
                output_field=FloatField()
            )
        )
    
    # Вычисляет WBGT на основе агрегированного QuerySet
    def get_wbgt(self, qs):
        return qs.annotate(
            wbgt=ExpressionWrapper(
                0.7 * Coalesce(F('temperature'), Value(0.0)) +
                0.3 * Coalesce(F('humidity'), Value(0.0)) / 100.0,
                output_field=FloatField()
            )
        )

    def get_cwsi(self, qs):
        return qs.annotate(
            cwsi=ExpressionWrapper(
                Case(
                    When(humidity__lt=100, then=(
                        Coalesce(F('temperature'), Value(0.0)) - Value(20.0)
                    ) / (
                        Value(100.0) - Coalesce(F('humidity'), Value(0.0))
                    )),
                    default=Value(0.5),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        )

    def get_heat_index(self, qs):
        return qs.annotate(
            heat_index=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) +
                0.5 * (
                    Coalesce(F('humidity'), Value(0.0)) / 100.0
                ) * (
                    Coalesce(F('temperature'), Value(0.0)) - Value(26.0)
                ),
                output_field=FloatField()
            )
        )

    def aggregate_with_indices(self, sensor_ids, period='day', aggregate_func='avg'):
        # 1. Проверка и подготовка параметров
        if not sensor_ids:
            return []

        aggregates = {'avg': Avg, 'min': Min, 'max': Max}
        period_functions = {
            'day': TruncDay,
            'week': TruncWeek, 
            'month': TruncMonth,
            'year': TruncYear
        }

        try:
            trunc_func = period_functions[period.lower()]
            agg_func = aggregates[aggregate_func.lower()]
        except KeyError as e:
            raise ValueError(f"Неподдерживаемый параметр: {str(e)}")

        # 2. Базовый запрос с фильтрацией и группировкой по времени
        base_qs = (
            self.filter(sensor__sensor_id__in=sensor_ids)
            .annotate(period=trunc_func('timestamp'))
        )

        # 3. Аннотации для каждого параметра
        param_annotations = {
            'temperature': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='TEMP', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0)
            ),
            'humidity': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='HUM', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0)
            ),
            'precipitation': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='PRECIP', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0)
            ),
            'wind_speed': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='WS', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0)
            )
        }

        # 4. Применяем аннотации и группируем
        aggregated_qs = (
            base_qs.values('period')
            .annotate(**param_annotations)
            .order_by('period')
        )

        # 5. Вычисляем индексы
        qs_with_indices = self.get_utci(aggregated_qs)
        qs_with_indices = self.get_wbgt(qs_with_indices)
        qs_with_indices = self.get_cwsi(qs_with_indices)
        qs_with_indices = self.get_heat_index(qs_with_indices)

        # 6. Форматируем результат
        result = []
        for item in qs_with_indices:
            formatted_item = {
                'date': item['period'].strftime('%Y-%m-%d'),
                'temperature': round(float(item['temperature']), 1),
                'humidity': round(float(item['humidity']), 1),
                'precipitation': round(float(item['precipitation']), 2),
                'wind_speed': round(float(item['wind_speed']), 1),
                'utci': round(float(item['utci']), 1),
                'wbgt': round(float(item['wbgt']), 1),
                'cwsi': round(float(item['cwsi']), 2),
                'heat_index': round(float(item['heat_index']), 1),
            }

            # Добавляем диапазон дат для недельного периода
            if period == 'week':
                start_date = item['period']
                end_date = start_date + timedelta(days=6)
                formatted_item['date_range'] = (
                    f"{start_date.strftime('%Y-%m-%d')} - "
                    f"{end_date.strftime('%Y-%m-%d')}"
                )

            result.append(formatted_item)

        return result


class ReadingManager(models.Manager):
    def get_queryset(self):
        return ReadingQuerySet(self.model, using=self._db)

    def time_aggregates(self, *args, **kwargs):
        return self.get_queryset().time_aggregates(*args, **kwargs)
    
    def time_aggregates_by_code(self, *args, **kwargs):
        return self.get_queryset().time_aggregates_by_code(*args, **kwargs)

    def aggregate_with_indices(self, *args, **kwargs):
        return self.get_queryset().aggregate_with_indices(*args, **kwargs)

    def get_utci(self, *args, **kwargs):
        return self.get_queryset().get_utci(*args, **kwargs)

    def get_wbgt(self, *args, **kwargs):
        return self.get_queryset().get_wbgt(*args, **kwargs)

    def get_cwsi(self, *args, **kwargs):
        return self.get_queryset().get_cwsi(*args, **kwargs)

    def get_heat_index(self, *args, **kwargs):
        return self.get_queryset().get_heat_index(*args, **kwargs)

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