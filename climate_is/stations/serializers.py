from rest_framework import serializers
from .models import Station, Sensor, ParameterType, SensorSeries
from readings.models import Reading

class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = '__all__'

class SensorSerializer(serializers.ModelSerializer):
    station = StationSerializer(read_only=True)
    sensor_model = serializers.StringRelatedField()

    class Meta:
        model = Sensor
        fields = '__all__'

class ParameterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterType
        fields = '__all__'

class SensorSeriesSerializer(serializers.ModelSerializer):
    param_type = ParameterTypeSerializer()

    class Meta:
        model = SensorSeries
        fields = '__all__'        


class TimeSeriesSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=False, allow_null=True)
    parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS'])
    aggregate = serializers.ChoiceField(choices=['avg', 'min', 'max', 'sum'], default='avg')
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year'], default='day')
    year_start = serializers.IntegerField(min_value=1995)
    year_end = serializers.IntegerField(min_value=1995)
    show_stl = serializers.BooleanField(default=False)
    show_norm = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['year_start'] > data['year_end']:
            raise serializers.ValidationError("year_start must be less than or equal to year_end")
        if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
            raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
        return data

class TimeSeriesResponseSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    value = serializers.FloatField()
    seasonal = serializers.FloatField(required=False)
    trend = serializers.FloatField(required=False)
    residual = serializers.FloatField(required=False)
    normal_value = serializers.FloatField(required=False)

class SeasonalSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=False, allow_null=True)
    parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS'])
    cycle = serializers.ChoiceField(choices=['daily', 'monthly', 'yearly'])
    year_start = serializers.IntegerField(min_value=1995)
    year_end = serializers.IntegerField(min_value=1995)
    show_trend = serializers.BooleanField(default=False)
    show_anomalies = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['year_start'] > data['year_end']:
            raise serializers.ValidationError("year_start must be less than or equal to year_end")
        if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
            raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
        return data

class SeasonalResponseSerializer(serializers.Serializer):
    date = serializers.CharField()
    value = serializers.FloatField()
    trend = serializers.FloatField(required=False)
    anomaly = serializers.BooleanField(required=False)

class IndexesSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=False, allow_null=True)
    index = serializers.ChoiceField(choices=['utci', 'wbgt', 'cwsi', 'heat_index'])
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year'], default='day')
    year_start = serializers.IntegerField(min_value=1995)
    year_end = serializers.IntegerField(min_value=1995)
    vis_type = serializers.ChoiceField(choices=['line', 'heatmap'], default='line')

    def validate(self, data):
        if data['year_start'] > data['year_end']:
            raise serializers.ValidationError("year_start must be less than or equal to year_end")
        if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
            raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
        return data

class IndexesResponseSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    value = serializers.FloatField()
    date_range = serializers.CharField(required=False)

class DashboardSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=False, allow_null=True)
    parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS'])
    aggregate = serializers.ChoiceField(choices=['avg', 'min', 'max', 'sum'], default='avg')
    period = serializers.ChoiceField(choices=['day', 'week', 'month', 'year'], default='day')
    date_start = serializers.DateField()  # Начальная дата периода
    date_end = serializers.DateField()    # Конечная дата периода
    show_norm = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['date_start'] > data['date_end']:
            raise serializers.ValidationError("date_start must be less than or equal to date_end")
        if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
            raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
        return data

class DashboardResponseSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    value = serializers.FloatField()
    normal_value = serializers.FloatField(required=False)