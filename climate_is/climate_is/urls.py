from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    #path('', include('api.urls')),
    path('api/', include('stations.urls')),
    path('api/', include('readings.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('accounts/logout/', auth_views.LogoutView.as_view()),  
]
