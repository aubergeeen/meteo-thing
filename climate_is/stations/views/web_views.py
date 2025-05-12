from django.shortcuts import render
from stations.models import Station, Sensor, ParameterType, SensorSeries
from stations.serializers import StationSerializer, SensorSerializer, ParameterTypeSerializer, SensorSeriesSerializer

def list_of_stations(request):
    data = Station.objects.all().values('station_id', 'name')  # получаем поля id и name всех станций из таблицы
    return render(request, 'stations/temp_table.html', {'stations': data})