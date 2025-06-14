"""
MODUŁ API POGODY - POBIERANIE DANYCH METEOROLOGICZNYCH
=====================================================

Ten moduł zawiera klasę WeatherAPI, która pobiera dane pogodowe z różnych źródeł
API meteorologicznych. Implementuje funkcjonalność pobierania prognoz pogody
i danych historycznych dla potrzeb systemu rekomendacji tras.

FUNKCJONALNOŚCI:
- Pobieranie prognoz pogody na przyszłe dni (Open-Meteo API)
- Pobieranie danych historycznych z lokalnych plików JSON
- Przetwarzanie danych pogodowych (temperatura, opady, wiatr, nasłonecznienie)
- Obsługa różnych formatów dat i zakresów czasowych
- Mapowanie miast na współrzędne geograficzne

ŹRÓDŁA DANYCH:
- Open-Meteo API (prognozy pogody)
- Visual Crossing API (dane historyczne - wymaga klucza)
- OpenWeatherMap API (dane historyczne - wymaga klucza)
- World Weather Online API (dane historyczne - wymaga klucza)
- Lokalne pliki JSON (cache danych historycznych)

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK
# ============================================================================
import requests                              # Biblioteka do zapytań HTTP
import os                                   # Operacje na systemie plików
import json                                 # Obsługa formatu JSON
from datetime import datetime, timedelta    # Operacje na datach i czasie
from typing import Dict, Any, List, Optional  # Podpowiedzi typów
from functools import reduce                # Funkcje funkcyjne (reduce)
from config import OPEN_METEO_API, CITY_COORDINATES  # Konfiguracja API

# ============================================================================
# GŁÓWNA KLASA API POGODY
# ============================================================================

class WeatherAPI:
    """
    Klasa do pobierania i przetwarzania danych pogodowych z różnych źródeł API.
    
    Ta klasa implementuje kompleksowy system pobierania danych meteorologicznych,
    obsługując zarówno prognozy pogody jak i dane historyczne. Wykorzystuje
    programowanie funkcyjne do przetwarzania danych pogodowych.
    
    Attributes:
        base_url: URL bazowy Open-Meteo API
        forecast_url: URL do prognoz pogody
        history_url: URL do danych historycznych
        weather_data_file: Ścieżka do pliku z danymi pogodowymi
        
    Przykład użycia:
        api = WeatherAPI()
        weather = api.get_weather_forecast("Gdańsk", "2024-06-01")
        print(f"Temperatura: {weather['temperature_avg']}°C")
    """
    
    def __init__(self):
        """
        Inicjalizacja klasy WeatherAPI.
        
        Ustawia URL-e różnych serwisów pogodowych i ścieżki do plików danych.
        Konfiguruje dostęp do wielu API pogodowych (niektóre wymagają kluczy).
        """
        # ====================================================================
        # KONFIGURACJA OPEN-METEO API (darmowe, bez klucza)
        # ====================================================================
        self.base_url = "https://api.open-meteo.com/v1"           # URL bazowy
        self.forecast_url = f"{self.base_url}/forecast"           # Prognozy
        self.history_url = f"{self.base_url}/archive"             # Historia
        
        # ====================================================================
        # KONFIGURACJA DODATKOWYCH API (wymagają kluczy - opcjonalne)
        # ====================================================================
        # Visual Crossing Weather API
        self.visual_crossing_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        self.visual_crossing_api_key = "YOUR_API_KEY"  # Należy zastąpić prawdziwym kluczem API
        
        # OpenWeatherMap API
        self.openweather_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
        self.openweather_api_key = "YOUR_API_KEY"  # Należy zastąpić prawdziwym kluczem API
        
        # World Weather Online API
        self.worldweather_url = "http://api.worldweatheronline.com/premium/v1/past-weather.ashx"
        self.worldweather_api_key = "YOUR_API_KEY"  # Należy zastąpić prawdziwym kluczem API
        
        # ====================================================================
        # KONFIGURACJA PLIKÓW LOKALNYCH
        # ====================================================================
        # Plik z danymi pogodowymi (cache dla danych historycznych)
        self.weather_data_file = "api/weather_data.json"

    def _calculate_average_temperature(self, daily_data: Dict[str, List[float]]) -> float:
        """Calculate average temperature using reduce."""
        temps = [daily_data.get("temperature_2m_max", [0])[0], 
                daily_data.get("temperature_2m_min", [0])[0]]
        return reduce(lambda x, y: x + y, temps) / len(temps)

    def _process_weather_data(self, data: Dict[str, Any], city: str, date: str) -> Dict[str, Any]:
        """Process weather data using dictionary comprehension."""
        daily_data = data.get("daily", {})
        
        # Use dictionary comprehension to create weather data
        weather_data = {
            "date": date,
            "region": city,
            "temperature_min": daily_data.get("temperature_2m_min", [0])[0],
            "temperature_max": daily_data.get("temperature_2m_max", [0])[0],
            "temperature_avg": self._calculate_average_temperature(daily_data),
            "precipitation": daily_data.get("precipitation_sum", [0])[0],
            "cloud_cover": daily_data.get("cloudcover_mean", [0])[0],
            "wind_speed": daily_data.get("windspeed_10m_max", [0])[0],
            "sunshine_hours": daily_data.get("sunshine_duration", [0])[0] / 3600
        }
        
        return weather_data

    def get_weather_forecast(self, city: str, date: str) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a specific date."""
        try:
            # Convert date string to datetime
            target_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().date()
            
            # Choose appropriate API endpoint based on date
            if target_date.date() < today:
                print(f"Pobieranie historycznych danych pogodowych dla {city} na dzień {date}...")
                return self._get_historical_weather(city, date)
            else:
                print(f"Pobieranie prognozy pogody dla {city} na dzień {date}...")
                return self._get_future_weather(city, date)
                
        except Exception as e:
            print(f"Błąd podczas pobierania danych pogodowych: {e}")
            return None

    def _get_future_weather(self, city: str, date: str) -> Optional[Dict[str, Any]]:
        """Get weather forecast for future dates."""
        try:
            # Get coordinates for the city
            coordinates = self._get_city_coordinates(city)
            if not coordinates:
                return None

            # Prepare parameters for the API request
            params = {
                "latitude": coordinates["latitude"],
                "longitude": coordinates["longitude"],
                "start_date": date,
                "end_date": date,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "sunshine_duration",
                    "cloudcover_mean",
                    "windspeed_10m_max",
                    "winddirection_10m_dominant"
                ],
                "timezone": "Europe/Warsaw"
            }

            # Make the API request
            response = requests.get(self.forecast_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract and format the weather data
            daily = data["daily"]
            return {
                "temperature_max": daily["temperature_2m_max"][0],
                "temperature_min": daily["temperature_2m_min"][0],
                "temperature_avg": (daily["temperature_2m_max"][0] + daily["temperature_2m_min"][0]) / 2,
                "precipitation": daily["precipitation_sum"][0],
                "sunshine_hours": daily["sunshine_duration"][0] / 3600,  # Convert seconds to hours
                "cloud_cover": daily["cloudcover_mean"][0],
                "wind_speed": daily["windspeed_10m_max"][0]
            }

        except Exception as e:
            print(f"Błąd podczas pobierania prognozy pogody: {e}")
            return None

    def _get_historical_weather(self, city: str, date: str) -> Optional[Dict[str, Any]]:
        """Get historical weather data from local JSON file."""
        try:
            # Load weather data from file
            with open(self.weather_data_file, 'r', encoding='utf-8') as f:
                weather_data = json.load(f)

            # Check if we have data for this city and date
            if city in weather_data and date in weather_data[city]:
                return weather_data[city][date]
            else:
                # If no exact match, return average values for the city
                if city in weather_data:
                    city_data = weather_data[city]
                    dates = list(city_data.keys())
                    if dates:
                        # Return data from the first available date
                        return city_data[dates[0]]
                
                print(f"Brak danych historycznych dla {city} na dzień {date}")
                return None

        except Exception as e:
            print(f"Błąd podczas pobierania historycznych danych pogodowych: {e}")
            return None

    def _get_city_coordinates(self, city: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a given city."""
        city_coordinates = {
            "Gdańsk": {"latitude": 54.3520, "longitude": 18.6466},
            "Warszawa": {"latitude": 52.2297, "longitude": 21.0122},
            "Kraków": {"latitude": 50.0647, "longitude": 19.9450},
            "Wrocław": {"latitude": 51.1079, "longitude": 17.0385}
        }
        return city_coordinates.get(city)

    def get_weather_for_date_range(self, city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get weather for a date range using map."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Generate list of dates
            date_list = [start + timedelta(days=x) for x in range((end - start).days + 1)]
            
            # Use map to get weather for each date
            weather_data = list(map(
                lambda date: self.get_weather_forecast(city, date.strftime("%Y-%m-%d")),
                date_list
            ))
            
            # Filter out None values
            return list(filter(None, weather_data))
            
        except ValueError as e:
            print(f"Nieprawidłowy format daty: {e}")
            return [] 