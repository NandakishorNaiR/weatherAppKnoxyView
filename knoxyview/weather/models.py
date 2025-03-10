from django.db import models
from django.contrib.auth.models import User


class Weather(models.Model):
    city = models.CharField(max_length=100)  # City name
    temperature = models.FloatField()  # Temperature in Celsius
    description = models.CharField(max_length=255)  # Weather description (e.g., "Sunny")
    humidity = models.FloatField(default=0.0)  # Humidity as a percentage, with a default value
    pressure = models.FloatField()  # Atmospheric pressure in hPa
    real_feel = models.FloatField()  # Real feel temperature in Celsius
    wind_direction = models.CharField(max_length=50)  # Wind direction (e.g., "North")
    sunrise = models.CharField(max_length=50)  # Sunrise time as a string (e.g., "06:30 AM")
    is_daytime = models.BooleanField()  # Whether it is daytime
    date = models.DateTimeField(auto_now_add=True)  # Timestamp when the record was created

    class Meta:
        indexes = [
            models.Index(fields=['city', 'date']),  # Index for faster queries
        ]

    def __str__(self):
        return f"{self.city} - {self.temperature}°C - {self.description}"


class SavedLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who saved the location
    name = models.CharField(max_length=100)  # City or custom name for the location
    latitude = models.FloatField()  # Latitude of the location
    longitude = models.FloatField()  # Longitude of the location
    added_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the location was saved

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"