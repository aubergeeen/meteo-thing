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