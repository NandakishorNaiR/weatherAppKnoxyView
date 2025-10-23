from django.contrib import admin
from django.urls import path
from weather.views import (
    HomeView,
    FetchWeatherView,  # Keep only the necessary views
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('', HomeView.as_view(), name='home'),  # Home page
    path('weather/', FetchWeatherView.as_view(), name='fetch_weather'),  # Fetch weather data
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)