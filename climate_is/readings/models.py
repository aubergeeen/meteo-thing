from django.db import models
from django.utils import timezone
from stations.models import Sensor, Station  
from django.db.models import Avg, Max, Min, Sum, Count, F
from django.db.models.functions import ExtractMonth, ExtractDay, ExtractYear, Trunc, TruncWeek, TruncDay, TruncMonth, TruncYear, Coalesce, Concat, NullIf
from django.db.models.expressions import ExpressionWrapper, Case, When, Value, Subquery
from django.db.models import FloatField, CharField
from datetime import timedelta, datetime

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
        # Let's assume что данные об осадках в мм даются каждые 12 ч (иначе думать про кумулятивность(( )
        aggregates = {'avg': Avg, 'min': Min, 'max': Max, 'sum': Sum}
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
    
    # def seasonal_aggregates(self, sensor_ids, param_code, cycle, year_start, year_end):
    #     if cycle not in ['daily', 'monthly', 'yearly']:
    #         raise ValueError(f"Unsupported cycle: {cycle}")

    #     annotations = {}
    #     group_fields = []
    #     cycle_label = None

    #     if cycle == 'daily':
    #         annotations['month'] = ExtractMonth('timestamp')
    #         annotations['day'] = ExtractDay('timestamp')
    #         group_fields = ['month', 'day']
    #         cycle_label = Concat(
    #             #LPad(ExtractMonth('timestamp'), 2, Value('0')),
    #             ExtractMonth('timestamp'),
    #             Value('-'),
    #             #LPad(ExtractDay('timestamp'), 2, Value('0')),
    #             ExtractDay('timestamp'),
    #             output_field=CharField()
    #         )
    #     elif cycle == 'monthly':
    #         annotations['month'] = ExtractMonth('timestamp')
    #         group_fields = ['month']
    #         # тупо лол 
    #         cycle_label = Case(
    #             When(month=1, then=Value('Январь')),
    #             When(month=2, then=Value('Февраль')),
    #             When(month=3, then=Value('Март')),
    #             When(month=4, then=Value('Апрель')),
    #             When(month=5, then=Value('Май')),
    #             When(month=6, then=Value('Июнь')),
    #             When(month=7, then=Value('Июль')),
    #             When(month=8, then=Value('Август')),
    #             When(month=9, then=Value('Сентябрь')),
    #             When(month=10, then=Value('Октябрь')),
    #             When(month=11, then=Value('Ноябрь')),
    #             When(month=12, then=Value('Декабрь')),
    #             output_field=CharField()
    #         )
    #     else:  # yearly
    #         annotations['year'] = ExtractYear('timestamp')
    #         group_fields = ['year']
    #         cycle_label = Concat(
    #             ExtractYear('timestamp'),
    #             output_field=CharField()
    #         )

    #     return (
    #         self.filter(
    #             sensor__sensor_id__in=sensor_ids,
    #             sensor__sensor_model__param_type__code=param_code,
    #             timestamp__year__gte=year_start,
    #             timestamp__year__lte=year_end
    #         )
    #         .annotate(**annotations)
    #         .annotate(cycle_label=cycle_label)
    #         .values('cycle_label', *group_fields)
    #         .annotate(value=Avg('value'))
    #         .order_by(*group_fields)
    #     )
    
    def climate_normals(self, sensor_ids, param_code, period='monthly', baseline_start=2005, baseline_end=2025):
        if period.lower() not in ['monthly', 'daily']:
            raise ValueError(f"Unsupported period for normals: {period}")

        annotations = {}
        group_fields = []

        if period.lower() == 'monthly':
            annotations['month'] = ExtractMonth('timestamp')
            group_fields = ['month']
        else:  # daily
            annotations['month'] = ExtractMonth('timestamp')
            annotations['day'] = ExtractDay('timestamp')
            group_fields = ['month', 'day']

        return (
            self.filter(
                sensor__sensor_id__in=sensor_ids,
                sensor__sensor_model__param_type__code=param_code,
                timestamp__year__gte=baseline_start,
                timestamp__year__lte=baseline_end
            )
            .annotate(**annotations)
            .values(*group_fields)
            .annotate(normal_value=Avg('value'))
            .order_by(*group_fields)
        )

    # Вычисляет UTCI на основе агрегированного QuerySet
    # def get_utci(self, qs):
    #     return qs.annotate(
    #         utci=ExpressionWrapper(
    #             Coalesce(F('temperature'), Value(0.0)) +
    #             0.1 * Coalesce(F('humidity'), Value(0.0)) - Value(5.0),
    #             output_field=FloatField()
    #         )
    #     )

    # Вычисляет UTCI на основе агрегированного QuerySet   (АППРОКСИМАЦИЯ - НУЖНА РАДИАЦИОННАЯ ТЕМПЕРАТУРА)
    def get_utci(self, qs):
        return qs.annotate(
            utci=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) + 
                (Value(0.3) * Coalesce(F('humidity'), Value(0.0)) / Value(100.0) * Coalesce(F('temperature'), Value(0.0))) -
                (Value(1.5) * Coalesce(F('wind_speed'), Value(0.0))),
                output_field=FloatField()
            )
        )
    # # Вычисляет WBGT на основе агрегированного QuerySet
    # def get_wbgt(self, qs):
    #     return qs.annotate(
    #         wbgt=ExpressionWrapper(
    #             0.7 * Coalesce(F('temperature'), Value(0.0)) +
    #             0.3 * Coalesce(F('humidity'), Value(0.0)) / 100.0,
    #             output_field=FloatField()
    #         )
    #     )

    # def get_cwsi(self, qs):
    #     return qs.annotate(
    #         cwsi=ExpressionWrapper(
    #             Case(
    #                 When(humidity__lt=100, then=(
    #                     Coalesce(F('temperature'), Value(0.0)) - Value(20.0)
    #                 ) / (
    #                     Value(100.0) - Coalesce(F('humidity'), Value(0.0))
    #                 )),
    #                 default=Value(0.5),
    #                 output_field=FloatField()
    #             ),
    #             output_field=FloatField()
    #         )
    #     )

    def get_cwsi(self, qs):
        return qs.annotate(
            # Упрощенная аппроксимация T_wet (как в WBGT)
            wet_bulb_temp_approx=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) - 
                (Value(100.0) - Coalesce(F('humidity'), Value(0.0))) / Value(5.0),
                output_field=FloatField()
            ),
            # Аппроксимация T_leaf (+3°C к температуре воздуха)
            leaf_temp_approx=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) + Value(3.0),
                output_field=FloatField()
            ),
            # Расчет CWSI с защитой от деления на 0
            cwsi=ExpressionWrapper(
                (F('leaf_temp_approx') - F('wet_bulb_temp_approx')) / 
                NullIf(
                    F('temperature') - 
                    F('wet_bulb_temp_approx'),
                    Value(0.0)
                ),
                output_field=FloatField()
            )
        )
    
    def get_wbgt(self, qs):
        return qs.annotate(
            # аппроксимация T_wet 
            wet_bulb_temp_approx=ExpressionWrapper(
                Coalesce(F('temperature'), Value(0.0)) - 
                (Value(100.0) - Coalesce(F('humidity'), Value(0.0))) / Value(5.0),
                output_field=FloatField()
            ),
            # Расчет WBGT
            wbgt=ExpressionWrapper(
                Value(0.7) * F('wet_bulb_temp_approx') +
                Value(0.2) * F('temperature') +
                Value(0.1) * Coalesce(F('temperature'), Value(0.0)),
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
    
    def get_hdd(self, qs):
        # Heating Degree Days: sum(max(18 - T_avg, 0)) per day
        return qs.annotate(
            hdd=ExpressionWrapper(
                Case(
                    When(temperature__lt=18.0, then=Value(18.0) - Coalesce(F('temperature'), Value(0.0))),
                    default=Value(0.0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        )

    def get_cdd(self, qs):
        # Cooling Degree Days: sum(max(T_avg - 24, 0)) per day
        return qs.annotate(
            cdd=ExpressionWrapper(
                Case(
                    When(temperature__gt=24.0, then=Coalesce(F('temperature'), Value(0.0)) - Value(24.0)),
                    default=Value(0.0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        )
    
    def cartogram_aggregates(self, param_code, aggregate_func='avg', month=None, year=None, zero_missing=False):
        aggregates = {'avg': Avg, 'min': Min, 'max': Max, 'sum': Sum}
        index_map = {
            'utci': self.get_utci,
            'wbgt': self.get_wbgt,
            'cwsi': self.get_cwsi,
            'heat_index': self.get_heat_index,
            'hdd': self.get_hdd,
            'cdd': self.get_cdd
        }
        param_key_map = {'TEMP': 'temperature', 
                         'HUM': 'humidity', 
                         'PRECIP': 'precipitation', 
                         'WS': 'wind speed '}
        
        if aggregate_func.lower() not in aggregates and aggregate_func.lower() != 'anom':
            raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
        if year is None:
            year = timezone.now().year        
        
        agg_func = aggregates['avg'] if aggregate_func.lower() == 'anom' else aggregates[aggregate_func.lower()]


        # Базовый QuerySet с фильтрацией по году и месяцу
        base_qs = self.filter(
            timestamp__year=year,
            timestamp__month=month
        ).annotate(
            station_id=F('sensor__station__station_id')
        )

        # Аннотации для параметров
        param_annotations = {
            'temperature': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='TEMP', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0) if zero_missing else Value(None)
            ),
            'humidity': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='HUM', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0) if zero_missing else Value(None)
            ),
            'precipitation': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='PRECIP', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0) if zero_missing else Value(None)
            ),
            'wind_speed': Coalesce(
                agg_func(Case(
                    When(sensor__sensor_model__param_type__code='WS', then='value'),
                    output_field=FloatField()
                )),
                Value(0.0) if zero_missing else Value(None)
            )
        }
        
        # Агрегация для обычных параметров или подготовка для индексов
        if param_code in ['TEMP', 'HUM', 'PRECIP', 'WS']:
            param_key = param_key_map[param_code]
            aggregated_qs = (
                base_qs
                .values('station_id')
                .annotate(**{param_key: param_annotations[param_key]})
                .annotate(value=F(param_key))
            )
        elif param_code in index_map:
            aggregated_qs = (
                base_qs
                .values('station_id')
                .annotate(**param_annotations)
            )
            indexed_qs = index_map[param_code](aggregated_qs)
            aggregated_qs = indexed_qs.annotate(value=F(param_code))
        else:
            raise ValueError(f"Unsupported parameter: {param_code}")

        # Обработка аномалий
        if aggregate_func.lower() == 'anom':
            normal_qs = self.climate_normals(
                sensor_ids=Subquery(Sensor.objects.values('sensor_id')),
                param_code='TEMP' if param_code in index_map else param_code,
                period='monthly'
            ).filter(month=month).values('normal_value')

            aggregated_qs = aggregated_qs.annotate(
                normal_value=Coalesce(
                    Subquery(normal_qs, output_field=FloatField()),
                    Value(0.0)
                ),
                value=ExpressionWrapper(
                    F('value') - F('normal_value'),
                    output_field=FloatField()
                )
            )

        return (
            aggregated_qs
            .values('station_id')
            .annotate(
                station=F('station_id'),
                value=Coalesce(F('value'), Value(None), output_field=FloatField())
            )
            .order_by('station_id')
        )
    
    def aggregate_with_indices(self, sensor_ids, period='day', aggregate_func='avg', start_date=None, end_date=None):
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

        base_qs = (
            self.filter(sensor__sensor_id__in=sensor_ids)
            .annotate(period=trunc_func('timestamp'))
        )

        # фильтруем по датам (optional)
        if start_date and end_date:
            base_qs = base_qs.filter(timestamp__range=(start_date, end_date))
        elif start_date:
            base_qs = base_qs.filter(timestamp__gte=start_date) # greater than or equal 
        elif end_date:
            base_qs = base_qs.filter(timestamp__lte=end_date)

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

        aggregated_qs = (
            base_qs.values('period')
            .annotate(**param_annotations)
            .order_by('period')
        )

        qs_with_indices = self.get_utci(aggregated_qs)
        qs_with_indices = self.get_wbgt(qs_with_indices)
        qs_with_indices = self.get_cwsi(qs_with_indices)
        qs_with_indices = self.get_heat_index(qs_with_indices)

        # Форматируем результат
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

    def aggregate_with_selected_index(self, sensor_ids, index_name, period, year_start, year_end, aggregate_func='avg'):
        if not sensor_ids:
            return []

        aggregates = {'avg': Avg, 'min': Min, 'max': Max}
        period_functions = {
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
            'year': TruncYear
        }

        index_map = {
            'utci': self.get_utci,
            'wbgt': self.get_wbgt,
            'cwsi': self.get_cwsi,
            'heat_index': self.get_heat_index
        }

        try:
            trunc_func = period_functions[period.lower()]
            agg_func = aggregates[aggregate_func.lower()]
            index_func = index_map[index_name.lower()]
        except KeyError as e:
            raise ValueError(f"Неподдерживаемый параметр: {str(e)}")

        base_qs = (
            self.filter(
                sensor__sensor_id__in=sensor_ids,
                timestamp__year__gte=year_start,
                timestamp__year__lte=year_end
            )
            .annotate(period=trunc_func('timestamp'))
        )

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

        aggregated_qs = (
            base_qs.values('period')
            .annotate(**param_annotations)
            .order_by('period')
        )

        qs_with_index = index_func(aggregated_qs)

        result = []
        for item in qs_with_index:
            formatted_item = {
                'date': item['period'],
                'value': round(float(item[index_name]), 2)
            }

            if period != 'day':
                start_date = item['period']  
                if period == 'week':
                    end_date = start_date + timedelta(days=6)
                elif period == 'month':
                    # Переходим к первому дню следующего месяца и отнимаем 1 день
                    next_month = start_date.replace(day=1, month=start_date.month % 12 + 1)
                    if next_month.month == 1:
                        next_month = next_month.replace(year=start_date.year + 1)
                    end_date = next_month - timedelta(days=1)
                else:  # year
                    end_date = datetime(start_date.year, 12, 31)
                
                formatted_item['date_range'] = (
                    f"{start_date.strftime('%Y-%m-%d')} - "
                    f"{end_date.strftime('%Y-%m-%d')}"
                )

            result.append(formatted_item)

        return result
    
    def seasonal_aggregates(self, sensor_ids, param_code, cycle, year_start, year_end, target_month=None, target_day=None):
        if cycle not in ['daily', 'monthly', 'yearly']:
            raise ValueError(f"Unsupported cycle: {cycle}")

        annotations = {}
        group_fields = []
        cycle_label = None

        # Всегда добавляем год для группировки по годам
        annotations['year'] = ExtractYear('timestamp')
        group_fields = ['year']

        if cycle == 'daily':
            if not target_month or not target_day:
                raise ValueError("target_month and target_day are required for daily cycle")
            annotations['month'] = ExtractMonth('timestamp')
            annotations['day'] = ExtractDay('timestamp')
            group_fields.extend(['month', 'day'])
            cycle_label = Concat(
                ExtractYear('timestamp'),
                Value('-'),
                ExtractMonth('timestamp'),
                Value('-'),
                ExtractDay('timestamp'),
                output_field=CharField()
            )

        elif cycle == 'monthly':
            if not target_month:
                raise ValueError("target_month is required for monthly cycle")
            annotations['month'] = ExtractMonth('timestamp')
            group_fields.append('month')
            cycle_label = Concat(
                ExtractYear('timestamp'),
                Value('-'),
                ExtractMonth('timestamp'),
                output_field=CharField()
            )

        # Фильтрация по target_month и target_day, если указаны
        filters = {
            'sensor__sensor_id__in': sensor_ids,
            'sensor__sensor_model__param_type__code': param_code,
            'timestamp__year__gte': year_start,
            'timestamp__year__lte': year_end
        }
        if target_month:
            filters['timestamp__month'] = target_month
        if target_day:
            filters['timestamp__day'] = target_day

        return (
            self.filter(**filters)
            .annotate(**annotations)
            .annotate(cycle_label=cycle_label)
            .values('cycle_label', *group_fields)
            .annotate(value=Avg('value'))
            .order_by('year')
        )

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
    
    def seasonal_aggregates(self, *args, **kwargs):
        return self.get_queryset().seasonal_aggregates(*args, **kwargs)
    
    def aggregate_with_selected_index(self, *args, **kwargs):
        return self.get_queryset().aggregate_with_selected_index(*args, **kwargs)

    def climate_normals(self, *args, **kwargs):
        return self.get_queryset().climate_normals(*args, **kwargs)
    
    def cartogram_aggregates(self, *args, **kwargs):
        return self.get_queryset().cartogram_aggregates(*args, **kwargs)
    
    
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
        indexes = [ # индексация - может так будет быстрее??
            models.Index(fields=['timestamp'], name='readings_timestamp_idx'),
            models.Index(fields=['sensor_id'], name='readings_sensor_id_idx'),
            models.Index(fields=['sensor_id', 'timestamp'], name='readings_sensor_timestamp_idx'),
        ]
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