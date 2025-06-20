from django.shortcuts import render
from stations.models import Station, Sensor, ParameterType, SensorSeries
from stations.serializers import StationSerializer, SensorSerializer, ParameterTypeSerializer, SensorSeriesSerializer
from django.template import loader
from django.http import HttpResponse

# рендерим таблицу, параллельно передаем в контекст инфу по станциям
def table_dud(request):
    data = Station.objects.all().values('station_id', 'name')  # получаем поля id и name всех станций из таблицы
    return render(request, 'stations/table_test.html', {'stations': data})