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
    path('weather/timeseries/', api_views.TimeSeriesAPIView.as_view(), name='timeseries'),
    path('weather/seasonal/', api_views.SeasonalAPIView.as_view(), name='seasonal'),
    path('weather/indexes/', api_views.IndexesAPIView.as_view(), name='indexes'),
    path('weather/dashboard/', api_views.DashboardAPIView.as_view(), name='dash-info'),
]