import logging
import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime, timedelta
import os
from .models import Weather  # Keep only the Weather model
from django.views import View

# Initialize logger
logger = logging.getLogger(__name__)


class HomeView(View):
    """
    Displays the home page.
    """
    def get(self, request):
        city = request.GET.get('city', None)
        if city:
            return redirect(f'/weather/?city={city}')
        return render(request, 'weather/home.html')


class FetchWeatherView(View):
    """
    Fetches weather data for a given city or coordinates.
    """
    def get(self, request):
        city = request.GET.get('city')  # Get city from user input
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        weather_api_key = os.getenv("OPENWEATHER_API_KEY", "4eec84c7df1d83299a99be451295358c")
        aqi_api_key = os.getenv("WAQI_API_KEY", "fa36e54e9ca3f6389b07754649bd057229cf2374")

        context = self.initialize_context(city)

        if not (lat and lon) and city:
            lat, lon = self.get_coordinates(city, weather_api_key, context)

        if lat and lon:
            self.fetch_weather_data(lat, lon, weather_api_key, context)
            self.fetch_forecast_data(lat, lon, weather_api_key, context)
            self.fetch_air_quality_data(lat, lon, aqi_api_key, context)

            # Store the fetched weather data in MySQL
            if context.get('current_weather'):
                self.store_weather_data(city, context['current_weather'])

        return render(request, 'weather/home.html', context)

    @staticmethod
    def initialize_context(city):
        now = datetime.now()
        return {
            'city': city,
            'current_weather': None,
            'forecast': [],
            'air_quality': None,
            'error': None,
            'date': now.strftime("%B %d, %Y"),
            'day': now.strftime("%A"),
            'is_daytime': True,
        }

    def get_coordinates(self, city, weather_api_key, context):
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={weather_api_key}"
        try:
            response = requests.get(geocode_url)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]['lat'], data[0]['lon']
            else:
                context['error'] = "City not found."
        except Exception as e:
            logger.error(f"Error fetching coordinates: {e}")
            context['error'] = "Failed to fetch coordinates."
        return None, None

    def fetch_weather_data(self, lat, lon, api_key, context):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            context['current_weather'] = {
                'temperature': round(data['main']['temp'], 0),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'real_feel': round(data['main']['feels_like'], 0),
                'wind_direction': self.get_wind_direction(data['wind']['deg']),
                'sunrise': self.get_local_time(data['sys']['sunrise'], data['timezone']),
                'is_daytime': self.is_daytime(data['timezone']),
            }
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            context['error'] = "Failed to fetch weather data."

    def fetch_forecast_data(self, lat, lon, api_key, context):
        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            context['forecast'] = [
                {
                    'date': datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%A, %b %d"),
                    'time': datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p"),
                    'temp': round(item['main']['temp'], 0),
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                }
                for item in data['list'] if '12:00:00' in item['dt_txt']
            ]
        except Exception as e:
            logger.error(f"Error fetching forecast data: {e}")
            context['error'] = "Failed to fetch forecast data."

    def fetch_air_quality_data(self, lat, lon, api_key, context):
        try:
            url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == 'ok':
                context['air_quality'] = {
                    'aqi': data['data']['aqi'],
                    'pollutants': {key: val['v'] for key, val in data['data'].get('iaqi', {}).items()},
                }
            else:
                context['error'] = "Failed to fetch air quality data."
        except Exception as e:
            logger.error(f"Error fetching air quality data: {e}")
            context['error'] = "Failed to fetch air quality data."

    def store_weather_data(self, city, weather_data):
        """
        Stores weather data in the MySQL database using Django's ORM.
        """
        try:
            Weather.objects.create(
                city=city,
                temperature=weather_data['temperature'],
                description=weather_data['description'],
                humidity=weather_data['humidity'],
                pressure=weather_data['pressure'],
                real_feel=weather_data['real_feel'],
                wind_direction=weather_data['wind_direction'],
                sunrise=weather_data['sunrise'],
                is_daytime=weather_data['is_daytime'],
            )
            logger.info(f"Weather data for {city} saved to MySQL.")
        except Exception as e:
            logger.error(f"Error saving weather data to MySQL: {e}")

    @staticmethod
    def get_wind_direction(degree):
        directions = ["North", "NorthEast", "East", "SouthEast", "South", "SouthWest", "West", "NorthWest"]
        return directions[int((degree / 45) + 0.5) % 8]

    @staticmethod
    def get_local_time(timestamp, timezone_offset):
        local_time = datetime.utcfromtimestamp(timestamp + timezone_offset)
        return local_time.strftime("%I:%M %p")

    @staticmethod
    def is_daytime(timezone_offset):
        local_time = datetime.utcnow() + timedelta(seconds=timezone_offset)
        return 6 <= local_time.hour < 18