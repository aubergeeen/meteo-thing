#from django.shortcuts import render
from rest_framework import viewsets
from stations.models import Station, Sensor, ParameterType, SensorSeries
from stations.serializers import StationSerializer, SensorSerializer, ParameterTypeSerializer, SensorSeriesSerializer
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models.functions import TruncWeek, TruncDay, TruncMonth
from django.db.models import Avg, Case, When, FloatField, Value
from django.http import JsonResponse
from stations.models import Station, ParameterType, Sensor, SensorSeries
from readings.models import Reading
from rest_framework.decorators import action

"""
This viewset automatically provides `list` and `retrieve` actions.
"""
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


'''
    вспомогательная функция, получает статистику выбранного метеопараметра
    для перечня датчиков
'''
def fetch_param_stat(sensor_ids, param_name, trunc_func):
    param_type = ParameterType.objects.get(name=param_name)     # получаем ORM метеопараметра по названию
    sensors_specific = Sensor.objects.filter(sensor_id__in=sensor_ids, sensor_model__param_type=param_type).select_related('param_type')
    # наблюдения, отфильтрованные по станции и типу датчика
    readings = (
        Reading.objects.filter(sensor__in=sensors_specific.values_list('sensor_id', flat=True))
        .annotate(period=trunc_func('timestamp'))   # обрезаем время => period
        .values('period')                           # группируем по period
        .annotate(avg_value=Avg('value'))           # вычисляем avg 
    )
    result = {}
    for r in readings:
        result[r['period'].isoformat()] = r['avg_value']
    return result

'''
    получение усредненной статистики (по периоду) по метеопараметрам станции
    (агрегированной по периоду step)
'''
                        # TO-DO: передавать агрегирующую ф-ю параметром (AVG, MAX, etc)
@api_view(['GET'])
def get_stats_over_time(request):
    picked_station = request.GET.get('station')
    step_str = request.GET.get('step', '1d')    # шаг передается как 1d - день, 1w - неделя, 1m - месяц

    the_station = Station.objects.get(pk=picked_station)        # получаем ORM выбранной станцию
    sensor_qs = the_station.sensors.all()                       # queryset множества датчиков станции (через related_name)
    sensor_ids = sensor_qs.values_list('sensor_id', flat=True)  # список id датчиков - для передачи в ф-ю

    trunc_map = {'1d': TruncDay, '1w': TruncWeek, '1m': TruncMonth}     
    trunc_func = trunc_map.get(step_str, TruncDay)                          # получаем функцию для обрезки timestamp
    
    temp_data = fetch_param_stat(sensor_ids, 'Температура воздуха', trunc_func)     # статистика для температуры     
    humidity_data = fetch_param_stat(sensor_ids, 'Относительная влажность', trunc_func)    # статистика для влажности

    # Объединяем результаты
    all_periods = set(temp_data.keys()) | set(humidity_data.keys()) # собираем темп и влаж по одному периоду в один ряд
    data = []
    for period in sorted(all_periods):
        data.append({
            'date': period,
            'avg_t': temp_data.get(period),
            'avg_h': humidity_data.get(period),
        })

    return JsonResponse(data, safe=False)

@api_view(['GET'])
def list_station_locations(request):
    fields_param = request.GET.get('fields')
    if fields_param:
        fields = fields_param.split(',')
    else:
        # по умолчанию возвращаем эти поля
        fields = ['station_id']
    data = Station.objects.all().values(*fields)  # получаем поля id и name всех станций из таблицы
    return Response(list(data))