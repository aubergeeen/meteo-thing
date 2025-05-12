from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.getReading),
    path('add/', views.addReading),
]