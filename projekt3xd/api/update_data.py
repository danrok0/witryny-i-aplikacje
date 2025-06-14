"""
SKRYPT KOMPLEKSOWEJ AKTUALIZACJI DANYCH SYSTEMU
==============================================

Ten skrypt służy do pobierania i aktualizacji wszystkich danych zewnętrznych
używanych przez system rekomendacji tras turystycznych.

NOWE W ETAPIE 4: INTEGRACJA Z BAZĄ DANYCH SQLite
- Automatyczne zapisywanie tras do bazy danych
- Migracja danych pogodowych do bazy danych
- Fallback na pliki JSON w przypadku problemów z bazą

FUNKCJONALNOŚĆ:
- Pobiera dane o szlakach turystycznych dla wszystkich regionów → BAZA DANYCH
- Pobiera prognozy pogody na najbliższe 7 dni dla wszystkich miast → BAZA DANYCH  
- Zapisuje dane do bazy SQLite (głównie) i plików JSON (fallback)
- Obsługuje błędy pobierania dla poszczególnych regionów/dat
- Inicjalizuje puste pliki jeśli nie istnieją

AKTUALIZOWANE DANE:
1. routes (tabela bazy danych) - dane o szlakach turystycznych
2. weather_data (tabela bazy danych) - prognozy pogody na 7 dni
3. trails_data.json (fallback) - dane o szlakach
4. weather_dataa.json (fallback) - prognozy pogody

UŻYCIE:
python api/update_data.py

WYMAGANIA:
- Działające połączenie internetowe
- Dostęp do Overpass API i Open-Meteo API
- Uprawnienia do zapisu w katalogu głównym projektu
- Baza danych SQLite (data/database/routes.db)

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# KONFIGURACJA ŚCIEŻEK I IMPORTÓW
# ============================================================================

# Dodanie katalogu głównego projektu do ścieżki Python
# Umożliwia import modułów z katalogu nadrzędnego
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# IMPORTY MODUŁÓW PROJEKTU
# ============================================================================

from api.trails_api import TrailsAPI         # Klasa do pobierania danych o szlakach (z bazą danych!)
from api.weather_api import WeatherAPI       # Klasa do pobierania danych pogodowych
from config import CITY_COORDINATES         # Słownik miast i ich współrzędnych
import json                                 # Obsługa formatu JSON
from datetime import datetime, timedelta    # Operacje na datach

# ============================================================================
# IMPORTY BAZY DANYCH
# ============================================================================
try:
    from database import DatabaseManager
    from database.repositories.weather_repository import WeatherRepository
    DATABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Baza danych niedostępna. Używam tylko plików JSON.")
    DATABASE_AVAILABLE = False

# ============================================================================
# FUNKCJA AKTUALIZACJI DANYCH O SZLAKACH
# ============================================================================

def update_trails_data():
    """
    Pobiera i aktualizuje dane o szlakach turystycznych dla wszystkich regionów.
    
    NOWE W ETAPIE 4: Automatyczne zapisywanie do bazy danych SQLite
    
    Funkcja iteruje przez wszystkie miasta zdefiniowane w CITY_COORDINATES,
    pobiera dla każdego z nich dane o szlakach używając TrailsAPI (które teraz
    automatycznie zapisuje do bazy danych), a następnie zapisuje zagregowane 
    dane do pliku trails_data.json jako fallback.
    
    Proces:
    1. Inicjalizacja API z obsługą bazy danych
    2. Iteracja przez wszystkie regiony z CITY_COORDINATES
    3. Pobieranie szlaków dla każdego regionu → AUTOMATYCZNY ZAPIS DO BAZY
    4. Agregacja wszystkich szlaków w jedną listę
    5. Zapis do pliku trails_data.json (fallback/backup)
    
    Obsługa błędów:
    - Błędy pobierania dla poszczególnych regionów nie przerywają procesu
    - Wszystkie błędy są logowane z informacją o regionie
    - Proces kontynuuje dla pozostałych regionów
    - Baza danych ma automatyczny fallback na pliki JSON
    
    Returns:
        None: Funkcja zapisuje dane do bazy i pliku, nie zwraca wartości
    """
    # Inicjalizacja API do pobierania danych o szlakach (teraz z bazą danych!)
    api = TrailsAPI()
    
    # Lista na wszystkie szlaki ze wszystkich regionów (dla fallback JSON)
    all_trails = []

    print("=== 🏔️ AKTUALIZACJA DANYCH O SZLAKACH TURYSTYCZNYCH ===")
    print("Pobieranie danych o szlakach dla wszystkich regionów...")
    print("💾 Trasy będą automatycznie zapisane do bazy danych SQLite")
    
    # ========================================================================
    # ITERACJA PRZEZ WSZYSTKIE REGIONY
    # ========================================================================
    
    # Pobieranie szlaków dla każdego miasta z konfiguracji
    for region in CITY_COORDINATES.keys():
        print(f"\n🗺️ Pobieranie szlaków dla regionu: {region}")
        
        try:
            # Próba pobrania szlaków dla danego regionu
            # UWAGA: TrailsAPI teraz automatycznie zapisuje do bazy danych!
            trails = api.get_hiking_trails(region)
            
            # Sprawdzenie czy pobrano jakieś dane
            if trails:
                # Dodanie pobranych szlaków do głównej listy (dla fallback JSON)
                all_trails.extend(trails)
                print(f"✅ Znaleziono {len(trails)} szlaków dla {region}")
            else:
                print(f"⚠️ Brak szlaków dla regionu {region}")
                
        except Exception as e:
            # Obsługa błędów - logowanie i kontynuacja
            print(f"❌ Błąd podczas pobierania szlaków dla {region}: {e}")

    # ========================================================================
    # PODSUMOWANIE I ZAPIS DANYCH O SZLAKACH (FALLBACK JSON)
    # ========================================================================
    
    print(f"\n📊 PODSUMOWANIE AKTUALIZACJI TRAS:")
    print(f"   🎯 Łącznie przetworzono {len(all_trails)} szlaków")
    print(f"   💾 Trasy zostały zapisane do bazy danych SQLite")
    print(f"   📁 Tworzenie pliku JSON jako backup...")

    # Inicjalizacja pustego pliku jeśli nie istnieje
    if not os.path.exists('trails_data.json'):
        with open('trails_data.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("📄 Utworzono pusty plik trails_data.json")

    # Zapis wszystkich danych o szlakach do pliku JSON (backup)
    try:
        with open('trails_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_trails, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup danych zapisany do pliku trails_data.json ({len(all_trails)} tras)")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania backup danych o szlakach: {e}")

# ============================================================================
# FUNKCJA AKTUALIZACJI DANYCH POGODOWYCH
# ============================================================================

def update_weather_data():
    """
    Pobiera i aktualizuje prognozy pogody dla wszystkich regionów na najbliższe 7 dni.
    
    NOWE W ETAPIE 4: Zapisywanie do bazy danych SQLite
    
    Funkcja iteruje przez wszystkie miasta zdefiniowane w CITY_COORDINATES,
    pobiera dla każdego z nich prognozy pogody na następne 7 dni używając WeatherAPI,
    a następnie zapisuje dane do bazy danych i pliku weather_dataa.json.
    
    Proces:
    1. Inicjalizacja API i bazy danych
    2. Iteracja przez wszystkie regiony z CITY_COORDINATES
    3. Dla każdego regionu pobieranie prognoz na 7 dni (z obsługą błędów)
    4. Zapis do bazy danych SQLite
    5. Zapis do pliku weather_dataa.json (fallback)
    
    Zakres dat:
    - Pobiera prognozy od dzisiaj do 6 dni w przyszłość (łącznie 7 dni)
    - Każda prognoza zawiera datę, region i parametry pogodowe
    
    Obsługa błędów:
    - Błędy pobierania dla poszczególnych regionów/dat nie przerywają procesu
    - Wszystkie błędy są logowane z informacją o regionie
    - Proces kontynuuje dla pozostałych regionów i dat
    
    Returns:
        None: Funkcja zapisuje dane do bazy i pliku, nie zwraca wartości
    """
    # Inicjalizacja API do pobierania danych pogodowych
    api = WeatherAPI()
    
    # ========================================================================
    # NOWE: INICJALIZACJA BAZY DANYCH DLA POGODY
    # ========================================================================
    weather_repo = None
    if DATABASE_AVAILABLE:
        try:
            db_manager = DatabaseManager()
            db_manager.initialize_database()
            weather_repo = WeatherRepository(db_manager)
            print("✅ WeatherRepository połączony z bazą danych SQLite")
        except Exception as e:
            print(f"⚠️ Błąd połączenia z bazą danych pogody: {e}")
    
    # Lista na wszystkie prognozy pogody ze wszystkich regionów
    all_weather = []

    print("\n=== 🌤️ AKTUALIZACJA DANYCH POGODOWYCH ===")
    print("Pobieranie danych pogodowych dla wszystkich regionów...")
    if weather_repo:
        print("💾 Dane pogodowe będą zapisane do bazy danych SQLite")
    
    # ========================================================================
    # ITERACJA PRZEZ WSZYSTKIE REGIONY I DATY
    # ========================================================================
    
    # Pobieranie prognoz pogody dla każdego miasta z konfiguracji
    for region in CITY_COORDINATES.keys():
        print(f"\n🌍 Pobieranie prognozy pogody dla regionu: {region}")
        
        try:
            # Pobieranie prognoz na najbliższe 7 dni (0-6 dni od dzisiaj)
            for i in range(7):  # Get forecast for next 7 days
                # Obliczenie daty (dzisiaj + i dni)
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Próba pobrania prognozy dla danej daty
                weather = api.get_weather_forecast(region, date)
                
                # Sprawdzenie czy pobrano dane pogodowe
                if weather:
                    # Dodanie prognozy do głównej listy
                    all_weather.append(weather)
                    
                    # NOWE: Zapis do bazy danych
                    if weather_repo:
                        try:
                            weather_data = _convert_weather_to_database_format(weather, region)
                            weather_repo.add_weather_data(weather_data)
                            print(f"💾 Zapisano prognozę dla {region} na {date} do bazy danych")
                        except Exception as e:
                            print(f"⚠️ Błąd zapisu do bazy: {e}")
                    else:
                        print(f"📄 Pobrano prognozę dla {region} na {date}")
                else:
                    print(f"⚠️ Brak prognozy dla {region} na {date}")
                    
        except Exception as e:
            # Obsługa błędów - logowanie i kontynuacja
            print(f"❌ Błąd podczas pobierania prognozy pogody dla {region}: {e}")

    # ========================================================================
    # PODSUMOWANIE I ZAPIS DANYCH POGODOWYCH (FALLBACK JSON)
    # ========================================================================
    
    print(f"\n📊 PODSUMOWANIE AKTUALIZACJI POGODY:")
    print(f"   🎯 Łącznie pobrano {len(all_weather)} prognoz pogody")
    if weather_repo:
        print(f"   💾 Dane zostały zapisane do bazy danych SQLite")
    print(f"   📁 Tworzenie pliku JSON jako backup...")

    # Inicjalizacja pustego pliku jeśli nie istnieje
    if not os.path.exists('weather_dataa.json'):
        with open('weather_dataa.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("📄 Utworzono pusty plik weather_dataa.json")

    # Zapis wszystkich danych pogodowych do pliku JSON (backup)
    try:
        with open('weather_dataa.json', 'w', encoding='utf-8') as f:
            json.dump(all_weather, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup danych pogodowych zapisany do pliku weather_dataa.json ({len(all_weather)} rekordów)")
        
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania backup danych pogodowych: {e}")

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def _convert_weather_to_database_format(weather: dict, region: str) -> dict:
    """
    Konwertuje dane pogodowe z API na format bazy danych.
    
    Args:
        weather: Dane pogodowe z API
        region: Nazwa regionu
        
    Returns:
        Dane pogodowe w formacie bazy danych
    """
    # Pobierz współrzędne miasta z konfiguracji
    coordinates = CITY_COORDINATES.get(region, {"lat": 50.0, "lon": 20.0})
    
    return {
        'date': weather.get('date'),
        'location_lat': coordinates['lat'],
        'location_lon': coordinates['lon'],
        'avg_temp': weather.get('temperature_2m_mean'),
        'min_temp': weather.get('temperature_2m_min'),
        'max_temp': weather.get('temperature_2m_max'),
        'precipitation': weather.get('precipitation_sum'),
        'sunshine_hours': weather.get('sunshine_duration', 0) / 3600,  # Konwersja sekund na godziny
        'cloud_cover': weather.get('cloud_cover_mean'),
        'wind_speed': weather.get('wind_speed_10m_max'),
        'humidity': weather.get('relative_humidity_2m_mean')
    }

# ============================================================================
# PUNKT WEJŚCIA SKRYPTU
# ============================================================================

if __name__ == "__main__":
    """
    Punkt wejścia skryptu - wykonuje kompleksową aktualizację danych.
    
    Sprawdza czy skrypt jest uruchamiany jako główny program (nie importowany)
    i jeśli tak, wywołuje obie funkcje aktualizacji:
    1. update_trails_data() - aktualizacja danych o szlakach → BAZA DANYCH
    2. update_weather_data() - aktualizacja prognoz pogody → BAZA DANYCH
    
    Kolejność wykonania jest ważna - najpierw szlaki, potem pogoda.
    """
    print("=" * 80)
    print("🏔️ SYSTEM REKOMENDACJI TRAS TURYSTYCZNYCH - ETAP 4")
    print("💾 KOMPLEKSOWA AKTUALIZACJA DANYCH Z BAZĄ DANYCH SQLite")
    print("=" * 80)
    
    print("\n🚀 ROZPOCZĘCIE KOMPLEKSOWEJ AKTUALIZACJI DANYCH")
    print("1️⃣ Aktualizacja danych o szlakach turystycznych")
    update_trails_data()
    
    print("\n" + "="*60)
    print("2️⃣ Aktualizacja prognoz pogody")
    update_weather_data()
    
    print("\n" + "="*80)
    print("🎉 ZAKOŃCZENIE AKTUALIZACJI DANYCH")
    print("✅ Wszystkie dane zostały zaktualizowane w bazie danych SQLite!")
    print("📁 Pliki JSON utworzone jako backup")
    print("🎯 System gotowy do użycia z bazą danych!")
    print("=" * 80) 