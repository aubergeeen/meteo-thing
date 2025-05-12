from rest_framework import viewsets
from .models import Reading
from .serializers import ReadingSerializer
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend


class ReadingViewSet(viewsets.ModelViewSet):
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp']
    search_fields = ['value', 'sensor__station__name', 'sensor__sensor_model__series_name']
    filterset_fields = ['value', 'sensor', 'sensor__station__name', 'sensor__sensor_model__param_type']