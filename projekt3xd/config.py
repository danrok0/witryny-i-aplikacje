"""
PLIK KONFIGURACYJNY SYSTEMU REKOMENDACJI TRAS TURYSTYCZNYCH
==========================================================

Ten plik zawiera wszystkie stałe konfiguracyjne używane w całym systemie.
Centralizuje ustawienia API, współrzędne miast i szablony zapytań.

ZAWARTOŚĆ:
- Adresy URL do zewnętrznych API (pogoda, mapy)
- Współrzędne geograficzne głównych miast Polski
- Szablony zapytań do API OpenStreetMap/Overpass
- Parametry konfiguracyjne systemu

UŻYCIE: 
    from config import CITY_COORDINATES, OPEN_METEO_API
    weather_url = f"{OPEN_METEO_API}/forecast"
    city_coords = CITY_COORDINATES["Kraków"]

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY TYPÓW
# ============================================================================
from typing import Dict  # Podpowiedzi typów dla słowników

# ============================================================================
# ADRESY URL ZEWNĘTRZNYCH API
# ============================================================================
# API pogodowe Open-Meteo - darmowe dane meteorologiczne
OPEN_METEO_API = "https://api.open-meteo.com/v1"

# API Overpass - zapytania do bazy danych OpenStreetMap
OVERPASS_API = "https://overpass-api.de/api/interpreter"

# ============================================================================
# WSPÓŁRZĘDNE GEOGRAFICZNE GŁÓWNYCH MIAST POLSKI
# ============================================================================
# Słownik zawierający precyzyjne współrzędne GPS głównych miast
# Używane do pobierania danych pogodowych i wyszukiwania tras w okolicy
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "Gdańsk": {
        "lat": 54.3520,    # Szerokość geograficzna północna
        "lon": 18.6466     # Długość geograficzna wschodnia
    },
    "Warszawa": {
        "lat": 52.2297,    # Stolica Polski - centrum geograficzne
        "lon": 21.0122
    },
    "Kraków": {
        "lat": 50.0647,    # Historyczna stolica - południe Polski
        "lon": 19.9450
    },
    "Wrocław": {
        "lat": 51.1079,    # Stolica Dolnego Śląska - zachód Polski  
        "lon": 17.0385
    }
}

# ============================================================================
# SZABLON ZAPYTANIA OVERPASS API
# ============================================================================
# Zapytanie w języku Overpass QL do pobierania tras turystycznych
# z bazy danych OpenStreetMap dla określonego miasta
OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:25];
area["name"="{city}"]["boundary"="administrative"]->.searchArea;
relation["type"="route"]["route"="hiking"](area.searchArea);
out body;
>;
out skel qt;
""" 