from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.thingy, name='mega-thingy'),
    path("maps/", views.choropleth, name='choropleth'),
    path("graph/", views.graph, name='graph')
    #path("table/", views.table_thing, name='table_thing'),
]

