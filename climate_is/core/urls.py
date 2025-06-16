from django.urls import path
from . import views
#from .views import ClimateDataView, MeasurementListView, WeatherDataView, GraphDataView

urlpatterns = [
    #path("home/", views.thingy, name='mega-thingy'),
    #path("maps/", views.choropleth, name='choropleth'),
    path("graph/", views.graphs_view, name='graph'),
    path("", views.dud, name='dud'),
    path("map_dud/", views.choropleth_ver2, name='map_dud'),
    # path('api/climate-data/', ClimateDataView.as_view(), name='climate-data'),
    # path('api/measurements/', MeasurementListView.as_view(), name='measurement-list'),
    # path('api/weather/', WeatherDataView.as_view(), name='weather'),
    # path('api/graph-data/', GraphDataView.as_view(), name='graph-data'),
    #path("table/", views.table_thing, name='table_thing'),
]

