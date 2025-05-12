from rest_framework import serializers
from .models import Reading
from stations.models import Sensor

class ReadingSerializer(serializers.ModelSerializer):
    sensor = serializers.PrimaryKeyRelatedField(queryset=Sensor.objects.all())

    class Meta:
        model = Reading
        fields = '__all__'