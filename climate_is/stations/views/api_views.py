#from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from stations.serializers import StationSerializer, SensorSerializer, ParameterTypeSerializer, SensorSeriesSerializer, DashboardSerializer, \
    SeasonalResponseSerializer, SeasonalSerializer, TimeSeriesResponseSerializer, TimeSeriesSerializer, IndexesResponseSerializer, IndexesSerializer, DashboardResponseSerializer
from stations.models import Station, Sensor, ParameterType, SensorSeries
from readings.models import Reading

import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL

class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['name', 'station_id', ]          # поля сортировки
    search_fields = ['name', 'description',]  #поля поиска
    filterset_fields = ['station_id', 'name']

class SensorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

class ParameterTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParameterType.objects.all()
    serializer_class = ParameterTypeSerializer

class SensorSeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SensorSeries.objects.all()
    serializer_class = SensorSeriesSerializer

# ЭТА ШТУКА СЧИТАЕТ ДАННЫЕ ДЛЯ ТАБЛИЦЫ ЕСЛИ ЧЁ
@api_view(['GET'])
def get_stats_per_station(request):
    station_id = request.GET.get('station_id', '1')
    period = request.GET.get('period', 'day')
    aggregate_func = request.GET.get('agg', 'avg') 

    # Проверка допустимых функций агрегации
    valid_aggregates = {'avg', 'min', 'max'}
    if aggregate_func.lower() not in valid_aggregates:
        return JsonResponse({'error': f'Invalid aggregate function: {aggregate_func}. Must be one of {valid_aggregates}'}, status=400)

    try:
        # Получаем станцию и датчики
        station = Station.objects.get(pk=station_id)
        sensor_ids = station.sensors.values_list('sensor_id', flat=True)

        # Получаем агрегированные данные и индексы
        data = Reading.objects.aggregate_with_indices(sensor_ids, period=period, aggregate_func=aggregate_func)
        return JsonResponse(data, safe=False)
    except Station.DoesNotExist:
        return JsonResponse({'error': f'Station {station_id} not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Возвращает запрашиваемые поля по станциям (ПОМЕНЯТЬ НАЗВАНИЕ???)
@api_view(['GET'])
def list_station_locations(request):
    fields_param = request.GET.get('fields')
    if fields_param:
        fields = fields_param.split(',')
    else:
        fields = ['station_id']
    data = Station.objects.all().values(*fields)  # получаем поля id и name всех станций из таблицы
    return Response(list(data))


# ПРИНИМАЕТ МАССИВ НАБЛЮДЕНИЙ ОТ СТАНЦИИ
class StationParamReadingsAPIView(APIView):
    def post(self, request, station_id):
        try:
            station = Station.objects.get(pk=station_id)
        except Station.DoesNotExist:
            return Response(
                {"error": f"Станция с ID {station_id} не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"error": "Ожидается массив наблюдений"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        successful_readings = []
        errors = []
        
        for reading_data in data:
            try:
                param_type_id = reading_data.get('param_type_id')
                value = reading_data.get('value')
                timestamp = reading_data.get('timestamp')
                
                if None in (param_type_id, value):
                    errors.append({
                        'input': reading_data,
                        'error': "Отсутствует param_type_id или value"
                    })
                    continue
                
                if timestamp:
                    try:
                        timestamp = timezone.datetime.fromisoformat(timestamp)
                    except ValueError:
                        errors.append({
                            'input': reading_data,
                            'error': "Неверный формат timestamp"
                        })
                        continue
                
                reading, error = Reading.create_validated_reading_by_param_type(
                    station_id=station_id,
                    param_type_id=param_type_id,
                    value=value,
                    timestamp=timestamp
                )
                
                if error:
                    errors.append({
                        'input': reading_data,
                        'error': error
                    })
                else:
                    successful_readings.append({
                        'id': reading.id,
                        'param_type_id': param_type_id,
                        'timestamp': reading.timestamp.isoformat(),
                        'value': value
                    })
                    
            except Exception as e:
                #logger.error(f"Ошибка обработки наблюдения: {str(e)}", exc_info=True)
                errors.append({
                    'input': reading_data,
                    'error': f"Ошибка обработки: {str(e)}"
                })
        
        response_data = {
            'station_id': station_id,
            'successful': len(successful_readings),
            'failed': len(errors),
            'successful_readings': successful_readings,
            'errors': errors
        }
        
        if errors:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        return Response(response_data, status=status.HTTP_201_CREATED)
    
class TimeSeriesAPIView(APIView):
    def get(self, request):
        serializer = TimeSeriesSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # sensor_ids = Sensor.objects.filter(
        #     station__station_id=data['station_id'] if data['station_id'] else Station.objects.values('station_id')
        # ).values_list('sensor_id', flat=True)

        if data['station_id']:
            sensor_ids = Sensor.objects.filter(
                station__station_id=data['station_id']
            ).values_list('sensor_id', flat=True)
        else:
            sensor_ids = Sensor.objects.filter(
                station__station_id__in=Station.objects.values_list('station_id', flat=True)
            ).values_list('sensor_id', flat=True)

        if not sensor_ids:
            return Response({"error": "No sensors found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qs = Reading.objects.time_aggregates_by_code(
                sensor_ids=sensor_ids,
                param_code=data['parameter'],
                aggregate_func=data['aggregate'],
                period=data['period']#.replace('1', '')
            ).filter(
                period__year__gte=data['year_start'],  # gte = greater than or equal
                period__year__lte=data['year_end']      # lte = less than or equal
            )

            result = [{'date': item['period'], 'value': item['value']} for item in qs] 

            if data['show_norm']:
                norm_period = 'daily' if data['period'] == 'day' else 'monthly'
                normals = Reading.objects.climate_normals(
                    sensor_ids=sensor_ids,
                    param_code=data['parameter'],
                    period=norm_period,
                    baseline_start=2015,
                    baseline_end=2025
                )

                normal_map = {
                    (item['month'], item.get('day', None)): item['normal_value']
                    for item in normals
                }

                for item in result:
                    date = pd.to_datetime(item['date'])
                    key = (date.month, date.day if norm_period == 'daily' else None)
                    item['normal_value'] = normal_map.get(key, None)

            if data['show_stl']:
                df = pd.DataFrame(result)
                df.set_index('date', inplace=True)
                freq_map = {'day': 'D', 'week': 'W', 'month': 'M', 'year': 'Y'}
                df = df.asfreq(freq_map[data['period']]).fillna(method='ffill')
                period_map = {'day': 365, 'week': 52, 'month': 12, 'year': 1}
                stl = STL(df['value'], period=period_map[data['period']], robust=True)
                stl_result = stl.fit()

                for i, item in enumerate(result):
                    if i < len(stl_result.seasonal):
                        item['seasonal'] = stl_result.seasonal.iloc[i]
                        item['trend'] = stl_result.trend.iloc[i]
                        item['residual'] = stl_result.resid.iloc[i]

            response_serializer = TimeSeriesResponseSerializer(result, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SeasonalAPIView(APIView):
    def get(self, request):
        serializer = SeasonalSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # sensor_ids = Sensor.objects.filter(
        #     station__station_id=data['station_id'] if data['station_id'] else Station.objects.values('station_id')
        # ).values_list('sensor_id', flat=True)

        if data['station_id']:
            sensor_ids = Sensor.objects.filter(
                station__station_id=data['station_id']
            ).values_list('sensor_id', flat=True)
        else:
            sensor_ids = Sensor.objects.filter(
                station__station_id__in=Station.objects.values_list('station_id', flat=True)
            ).values_list('sensor_id', flat=True)

        if not sensor_ids:
            return Response({"error": "No sensors found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qs = Reading.objects.seasonal_aggregates(
                sensor_ids=sensor_ids,
                param_code=data['parameter'],
                cycle=data['cycle'],
                year_start=data['year_start'],
                year_end=data['year_end']
            )

            result = [{'date': item['cycle_label'], 'value': item['value']} for item in qs]

            if data['show_trend'] or data['show_anomalies']:
                df = pd.DataFrame(result)
                df['value'] = df['value'].fillna(df['value'].mean())
                
                if data['show_trend']:
                    df['trend'] = df['value'].rolling(window=3, center=True).mean()
                    df['trend'] = df['trend'].where(df['trend'].notna(), None)

                if data['show_anomalies']:
                    mean = df['value'].mean()
                    std = df['value'].std()
                    df['anomaly'] = df['value'].apply(lambda x: abs(x - mean) > 1.5 * std)
            
                # лол
                df = df.apply(lambda x: x.replace([np.nan, np.inf, -np.inf], None))
                result = df.to_dict('records')

            response_serializer = SeasonalResponseSerializer(result, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IndexesAPIView(APIView):
    def get(self, request):
        serializer = IndexesSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # sensor_ids = Sensor.objects.filter(
        #     station__station_id=data['station_id'] if data['station_id'] else Station.objects.values('station_id')
        # ).values_list('sensor_id', flat=True)

        if data['station_id']:
            sensor_ids = Sensor.objects.filter(
                station__station_id=data['station_id']
            ).values_list('sensor_id', flat=True)
        else:
            sensor_ids = Sensor.objects.filter(
                station__station_id__in=Station.objects.values_list('station_id', flat=True)
            ).values_list('sensor_id', flat=True)

        if not sensor_ids:
            return Response({"error": "No sensors found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qs = Reading.objects.aggregate_with_selected_index(
                sensor_ids=sensor_ids,
                index_name=data['index'],
                period=data['period'].replace('1', ''),
                year_start=data['year_start'],
                year_end=data['year_end'],
                aggregate_func='avg'
            )

            response_serializer = IndexesResponseSerializer(qs, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)       


class DashboardAPIView(APIView):
    def get(self, request):
        serializer = DashboardSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Получаем список sensor_ids в зависимости от наличия station_id
        if data['station_id']:
            sensor_ids = Sensor.objects.filter(
                station__station_id=data['station_id']
            ).values_list('sensor_id', flat=True)
        else:
            sensor_ids = Sensor.objects.filter(
                station__station_id__in=Station.objects.values_list('station_id', flat=True)
            ).values_list('sensor_id', flat=True)

        if not sensor_ids:
            return Response({"error": "No sensors found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Основной запрос с фильтрацией по датам
            qs = Reading.objects.time_aggregates_by_code(
                sensor_ids=sensor_ids,
                param_code=data['parameter'],
                aggregate_func=data['aggregate'],
                period=data['period']
            ).filter(
                timestamp__gte=data['date_start'],  # Фильтр по начальной дате
                timestamp__lte=data['date_end']     # Фильтр по конечной дате
            )

            result = [{'date': item['period'], 'value': item['value']} for item in qs]

            # Добавление климатических норм (если требуется)
            if data['show_norm']:
                norm_period = 'daily' if data['period'] == 'day' else 'monthly'
                normals = Reading.objects.climate_normals(
                    sensor_ids=sensor_ids,
                    param_code=data['parameter'],
                    period=norm_period,
                    baseline_start=2015,
                    baseline_end=2025
                )

                normal_map = {
                    (item['month'], item.get('day', None)): item['normal_value']
                    for item in normals
                }

                for item in result:
                    date = pd.to_datetime(item['date'])
                    key = (date.month, date.day if norm_period == 'daily' else None)
                    item['normal_value'] = normal_map.get(key, None)

            response_serializer = DashboardResponseSerializer(result, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# '''
# Возвращает статистику (сред, мин, макс)
# по интервалу (день, неделя, месяц, год)
# для выбранного параметра (по полю param id)
# агрегировано по станции??
# '''
# @api_view(['GET'])
# def aggregate_param_interval(request):
#     field = request.query_params.get('field', '1')
#     interval = request.query_params.get('interval', 'day')
    
# #def time_aggregates(queryset, param_type, aggregate_func='avg', period='week'):


#вспомогательная ф-я, получает ДЛИТЕЛЬНУЮ АГРЕГИРОВАННУЮ статистику выбранного метеопараметра для конкретного датчика
# def fetch_param_stat(sensor_ids, param_name, trunc_func):
#     param_type = ParameterType.objects.get(name=param_name)     # получаем ORM метеопараметра по названию
#     sensors_specific = Sensor.objects.filter(sensor_id__in=sensor_ids, sensor_model__param_type=param_type).select_related('param_type')
#     # наблюдения, отфильтрованные по станции и типу датчика
#     readings = (
#         Reading.objects.filter(sensor__in=sensors_specific.values_list('sensor_id', flat=True))
#         .annotate(period=trunc_func('timestamp'))   # обрезаем время => period
#         .values('period')                           # группируем по period
#         .annotate(avg_value=Avg('value'))           # вычисляем avg 
#     )
#     result = {}
#     for r in readings:
#         result[r['period'].isoformat()] = r['avg_value']
#     return result


# @api_view(['GET'])
# def get_stats_over_time(request):
#     picked_station = request.GET.get('station')
#     step_str = request.GET.get('step', '1d')    # шаг передается как 1d - день, 1w - неделя, 1m - месяц

#     the_station = Station.objects.get(pk=picked_station)        # получаем ORM выбранной станцию
#     sensor_qs = the_station.sensors.all()                       # queryset множества датчиков станции (через related_name)
#     sensor_ids = sensor_qs.values_list('sensor_id', flat=True)  # список id датчиков - для передачи в ф-ю

#     trunc_map = {'1d': TruncDay, '1w': TruncWeek, '1m': TruncMonth}     
#     trunc_func = trunc_map.get(step_str, TruncDay)                          # получаем функцию для обрезки timestamp
    
#     temp_data = fetch_param_stat(sensor_ids, 'Температура воздуха', trunc_func)     # статистика для температуры     
#     humidity_data = fetch_param_stat(sensor_ids, 'Относительная влажность', trunc_func)    # статистика для влажности

#     # Объединяем результаты
#     all_periods = set(temp_data.keys()) | set(humidity_data.keys()) # собираем темп и влаж по одному периоду в один ряд
#     data = []
#     for period in sorted(all_periods):
#         data.append({
#             'date': period,
#             'avg_t': temp_data.get(period),
#             'avg_h': humidity_data.get(period),
#         })

#     return JsonResponse(data, safe=False)