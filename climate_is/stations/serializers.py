from rest_framework import serializers
from .models import Station, Sensor, ParameterType, SensorSeries
from readings.models import Reading
from django.utils import timezone

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

# class SeasonalSerializer(serializers.Serializer):
#     station_id = serializers.IntegerField(required=False, allow_null=True)
#     parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS'])
#     cycle = serializers.ChoiceField(choices=['daily', 'monthly', 'yearly'])
#     year_start = serializers.IntegerField(min_value=1995)
#     year_end = serializers.IntegerField(min_value=1995)
#     show_trend = serializers.BooleanField(default=False)
#     show_anomalies = serializers.BooleanField(default=False)

#     def validate(self, data):
#         if data['year_start'] > data['year_end']:
#             raise serializers.ValidationError("year_start must be less than or equal to year_end")
#         if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
#             raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
#         return data

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

class CartogramSerializer(serializers.Serializer):
    parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS', 'utci', 'wbgt', 'cwsi', 'heat_index', 'hdd', 'cdd'])
    aggregate = serializers.ChoiceField(choices=['avg', 'min', 'max', 'sum', 'anom'])
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2005, required=False, allow_null=True)
    zero_missing = serializers.BooleanField(default=False)

    def validate(self, data):
        invalid_sum_params = ['HUM', 'hdd', 'cdd', 'utci', 'wbgt', 'cwsi', 'heat_index']
        if data['parameter'] in invalid_sum_params and data['aggregate'] == 'sum':
            raise serializers.ValidationError(f"Sum aggregation is not supported for {data['parameter']}")
        # if data['parameter'] in ['hdd', 'cdd'] and data['aggregate'] != 'sum':
        #     raise serializers.ValidationError(f"Only sum aggregation is supported for {data['parameter']}")
        if data.get('year') and data['year'] > timezone.now().year:
            raise serializers.ValidationError("Year cannot be in the future")
        return data

class CartogramResponseSerializer(serializers.Serializer):
    station = serializers.IntegerField()
    value = serializers.FloatField(allow_null=True)

class SeasonalSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=False, allow_null=True)
    parameter = serializers.ChoiceField(choices=['TEMP', 'HUM', 'PRECIP', 'WS'])
    cycle = serializers.ChoiceField(choices=['daily', 'monthly'])
    year_start = serializers.IntegerField(min_value=1995)
    year_end = serializers.IntegerField(min_value=1995)
    target_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    target_day = serializers.IntegerField(min_value=1, max_value=31, required=False)
    show_trend = serializers.BooleanField(default=False)
    show_anomalies = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['year_start'] > data['year_end']:
            raise serializers.ValidationError("year_start must be less than or equal to year_end")
        if data['station_id'] and not Station.objects.filter(station_id=data['station_id']).exists():
            raise serializers.ValidationError(f"Station with station_id {data['station_id']} does not exist")
        if data['cycle'] == 'daily' and (not data.get('target_month') or not data.get('target_day')):
            raise serializers.ValidationError("target_month and target_day are required for daily cycle")
        if data['cycle'] == 'monthly' and not data.get('target_month'):
            raise serializers.ValidationError("target_month is required for monthly cycle")
        return data