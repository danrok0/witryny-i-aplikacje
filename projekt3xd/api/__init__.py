"""
MODUŁ INICJALIZACYJNY PAKIETU API
=================================

Ten plik służy jako punkt wejścia do pakietu api, który zawiera klasy
odpowiedzialne za pobieranie danych z zewnętrznych źródeł w systemie
rekomendacji tras turystycznych.

STRUKTURA PAKIETU:
- trails_api.py: Klasa TrailsAPI do pobierania danych o szlakach z Overpass API
- weather_api.py: Klasa WeatherAPI do pobierania danych pogodowych z Open-Meteo API

FUNKCJONALNOŚĆ:
Pakiet umożliwia:
1. Pobieranie danych o szlakach turystycznych z OpenStreetMap (Overpass API)
2. Pobieranie prognoz pogody i danych historycznych (Open-Meteo API)
3. Przetwarzanie i standaryzację danych z różnych źródeł
4. Cache'owanie danych w plikach JSON

UŻYCIE:
from api import TrailsAPI, WeatherAPI

trails_api = TrailsAPI()
weather_api = WeatherAPI()
"""

# ============================================================================
# IMPORTY KLAS Z MODUŁÓW PAKIETU
# ============================================================================

# Import klasy TrailsAPI z modułu trails_api
# Klasa odpowiedzialna za pobieranie i przetwarzanie danych o szlakach turystycznych
from .trails_api import TrailsAPI

# Import klasy WeatherAPI z modułu weather_api
# Klasa odpowiedzialna za pobieranie danych pogodowych i prognoz
from .weather_api import WeatherAPI

# ============================================================================
# DEFINICJA PUBLICZNEGO API PAKIETU
# ============================================================================

# Lista __all__ definiuje, które klasy będą dostępne przy imporcie z gwiazdką
# Przykład: from api import *
# Dzięki temu tylko te klasy będą zaimportowane, co zapewnia czystość namespace
__all__ = ['TrailsAPI', 'WeatherAPI'] 