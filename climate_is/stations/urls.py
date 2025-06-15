from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import web_views, api_views

router = DefaultRouter()
router.register(r'stations', api_views.StationViewSet)
router.register(r'sensors', api_views.SensorViewSet)
router.register(r'parameters', api_views.ParameterTypeViewSet)
router.register(r'sensor_series', api_views.SensorSeriesViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("table/", web_views.list_of_stations, name='table_thing'),
    path("aggregate/", api_views.get_stats_per_station, name='api_stat_test'),
    path("locate/", api_views.list_station_locations, name='api_all_loc'),
    path("table_dud/", web_views.table_dud, name='table_dud'),
]