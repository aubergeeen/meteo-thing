from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.thingy, name='mega-thingy'),
    #path("table/", views.table_thing, name='table_thing'),
]

