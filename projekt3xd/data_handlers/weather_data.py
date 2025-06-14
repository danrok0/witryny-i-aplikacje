import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

# Dodaj katalog projektu do ścieżki Pythona
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from api.weather_api import WeatherAPI
from config import CITY_COORDINATES

class WeatherDataHandler:
    def __init__(self):
        self.api = WeatherAPI()

    def _validate_weather(self, weather: Any) -> Dict[str, Any]:
        """Waliduje i formatuje dane pogodowe."""
        if not isinstance(weather, dict):
            return None
            
        # Wymagane pola z domyślnymi wartościami
        default_weather = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "city": "nieznane",
            "temperature": 0.0,
            "temperature_min": 0.0,
            "temperature_max": 0.0,
            "precipitation": 0.0,
            "wind_speed": 0.0,
            "cloud_cover": 0,
            "sunshine_hours": 0.0,
            "conditions": "nieznane"
        }
        
        # Aktualizuj wartości domyślne rzeczywistymi danymi, jeśli są poprawne
        if isinstance(weather, dict):
            for key in default_weather:
                if key in weather and weather[key] is not None:
                    default_weather[key] = weather[key]
                    
            # Ensure numeric fields are correct type
            try:
                default_weather["temperature"] = float(default_weather["temperature"])
                default_weather["precipitation"] = float(default_weather["precipitation"])
                default_weather["wind_speed"] = float(default_weather["wind_speed"])
            except (ValueError, TypeError):
                default_weather["temperature"] = 0.0
                default_weather["precipitation"] = 0.0
                default_weather["wind_speed"] = 0.0
                
        return default_weather

    def get_weather(self, city: str, date: str = None) -> Dict[str, Any]:
        """Get weather for a specific city and date, always fetching from API."""
        print(f"Pobieranie prognozy pogody dla miasta {city} z API...")
        weather = self.api.get_weather_forecast(city, date)
        return self._validate_weather(weather)

    def get_weather_for_region(self, region: str, date: str = None) -> List[Dict[str, Any]]:
        """Get weather for all cities in a region."""
        weather_data = []
        for city in CITY_COORDINATES.keys():
            if city.lower() == region.lower():
                weather = self.get_weather(city, date)
                if weather:
                    weather_data.append(weather)
        return weather_data

    def get_weather_for_date_range(self, city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get weather for a date range."""
        weather_data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_date:
            weather = self.get_weather(city, current_date.strftime("%Y-%m-%d"))
            if weather:
                weather_data.append(weather)
            current_date += timedelta(days=1)
            
        return weather_data

    def get_average_temperature(self, city: str, date: str = None) -> float:
        """Calculate average temperature for a city."""
        weather = self.get_weather(city, date)
        return weather.get('temperature', 0.0) if weather else 0.0

    def get_precipitation_probability(self, city: str, date: str = None) -> float:
        """Get precipitation probability for a city."""
        weather = self.get_weather(city, date)
        return weather.get('precipitation', 0.0) if weather else 0.0

    def get_weather_forecast(self, city: str, date: str) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a specific date."""
        try:
            # Convert date string to datetime
            target_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().date()
            
            # Choose appropriate API endpoint based on date
            if target_date.date() < today:
                print(f"Pobieranie historycznych danych pogodowych dla {city} na dzień {date}...")
                weather_data = self.api._get_historical_weather(city, date)
            else:
                print(f"Pobieranie prognozy pogody dla {city} na dzień {date}...")
                weather_data = self.api._get_future_weather(city, date)
            
            if weather_data:
                return weather_data
            else:
                print("Nie udało się pobrać danych pogodowych")
                return None
                
        except Exception as e:
            print(f"Błąd podczas pobierania danych pogodowych: {e}")
            return None 