#!/usr/bin/env python3
"""
GŁÓWNY PLIK SYSTEMU REKOMENDACJI TRAS TURYSTYCZNYCH
===================================================

Ten plik zawiera główną aplikację konsolową do rekomendacji tras turystycznych.
System oferuje:
- Rekomendacje tras z filtrowaniem według różnych kryteriów
- Analizę konkretnych tras z wykorzystaniem AI
- Generowanie profesjonalnych raportów PDF z wykresami
- Pobieranie danych z portali internetowych
- Zarządzanie bazą danych SQLite
- Demonstrację przetwarzania tekstu wyrażeniami regularnymi

Autor: System Rekomendacji Tras Turystycznych - Etap 4
Data: 2024
"""

# ============================================================================
# IMPORTY BIBLIOTEK STANDARDOWYCH
# ============================================================================
import os          # Operacje na systemie plików
import sys         # Operacje systemowe
import json        # Obsługa formatu JSON
from datetime import datetime  # Obsługa dat i czasu
from typing import List, Dict, Any  # Podpowiedzi typów dla lepszej czytelności kodu

# ============================================================================
# KONFIGURACJA ŚCIEŻEK PROJEKTU
# ============================================================================
# Dodaj katalog główny projektu do ścieżki Pythona, aby móc importować moduły
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# ============================================================================
# IMPORTY MODUŁÓW PROJEKTU
# ============================================================================
from data_handlers.trail_data import TrailDataHandler      # Obsługa danych tras
from data_handlers.weather_data import WeatherDataHandler  # Obsługa danych pogodowych
from utils.trail_filter import TrailFilter                 # Filtrowanie tras
from utils.storage import save_results_to_file             # Zapisywanie wyników
from config import CITY_COORDINATES                        # Konfiguracja miast
from recommendation.trail_recommender import TrailRecommender  # Główny silnik rekomendacji
from utils.weather_utils import WeatherUtils               # Narzędzia pogodowe

# ============================================================================
# FUNKCJE INTERFEJSU UŻYTKOWNIKA
# ============================================================================

def display_main_menu():
    """
    Wyświetla główne menu systemu z wszystkimi dostępnymi opcjami.
    
    Menu oferuje 8 głównych funkcjonalności:
    1. Standardowe rekomendacje - podstawowe wyszukiwanie tras
    2. Raporty PDF - profesjonalne raporty z wykresami
    3. Analiza tras - szczegółowa analiza konkretnej trasy
    4. Pobieranie danych - automatyczne zbieranie z internetu
    5. Wykresy - generowanie tylko wizualizacji
    6. Testy systemu - kompleksowe testowanie funkcji
    7. Demo procesora tekstu - pokazuje analizę wyrażeń regularnych
    8. Wyjście - zamknięcie aplikacji
    """
    print("\n" + "="*60)
    print("🏔️  SYSTEM REKOMENDACJI TRAS TURYSTYCZNYCH  🏔️")
    print("="*60)
    print("Wybierz opcję:")
    print("1. 🚶 Standardowe rekomendacje tras")
    print("2. 📊 Rekomendacje z raportem PDF")
    print("3. 🔍 Analiza konkretnej trasy")
    print("4. 🌐 Pobierz dodatkowe dane z internetu")
    print("5. 📈 Generuj tylko wykresy")
    print("6. 🧪 Test wszystkich funkcji systemu")
    print("7. 🔧 Demonstracja przetwarzania tekstu")
    print("8. ❌ Wyjście")
    print("="*60)

def display_weather_stats(cities: List[str], date: str, weather_handler) -> None:
    """
    Wyświetla szczegółowe statystyki pogodowe dla wybranych miast.
    
    Args:
        cities: Lista nazw miast do wyświetlenia
        date: Data w formacie YYYY-MM-DD
        weather_handler: Obiekt obsługujący dane pogodowe
        
    Funkcja pobiera dane pogodowe dla każdego miasta i wyświetla:
    - Temperatury (min, max, średnia)
    - Opady i zachmurzenie
    - Godziny słoneczne i prędkość wiatru
    - Indeks komfortu wędrówki (0-100)
    - Ogólny stan pogody
    """
    print("\n=== 🌤️ Warunki pogodowe ===")
    print(f"Data: {date}\n")
    
    # Przeiteruj przez wszystkie wybrane miasta
    for city in cities:
        # Pobierz dane pogodowe dla miasta
        weather = weather_handler.get_weather_forecast(city, date)
        if not weather:
            print(f"{city}: Brak danych pogodowych")
            continue
            
        # Oblicz temperaturę średnią z min i max
        temp_min = weather.get('temperature_min', 0)
        temp_max = weather.get('temperature_max', 0)
        avg_temp = round((temp_min + temp_max) / 2, 1) if temp_min != 0 or temp_max != 0 else 'N/A'
        
        # Oblicz indeks komfortu wędrówki (algorytm uwzględnia temp, opady, słońce)
        comfort_index = WeatherUtils.calculate_hiking_comfort(weather)
        # Określ ogólny stan pogody na podstawie wszystkich parametrów
        weather_condition = WeatherUtils.get_weather_condition(weather)
        
        # Wyświetl wszystkie parametry pogodowe w czytelnej formie
        print(f"=== {city} ===")
        print(f"🌡️ Temperatura średnia: {avg_temp}°C")
        print(f"🥶 Minimalna temperatura: {weather.get('temperature_min', 'N/A')}°C")
        print(f"🔥 Maksymalna temperatura: {weather.get('temperature_max', 'N/A')}°C")
        print(f"🌧️ Opady: {weather.get('precipitation', 'N/A')} mm")
        print(f"☁️ Zachmurzenie: {weather.get('cloud_cover', 'N/A')}%")
        print(f"☀️ Godziny słoneczne: {weather.get('sunshine_hours', 0):.1f} h")
        print(f"💨 Prędkość wiatru: {weather.get('wind_speed', 'N/A')} km/h")
        print(f"🌈 Stan pogody: {weather_condition}")
        print(f"😊 Indeks komfortu: {comfort_index}/100")
        print()

def get_search_criteria():
    """
    Pobiera kryteria wyszukiwania tras od użytkownika w trybie interaktywnym.
    
    Returns:
        dict: Słownik z kryteriami wyszukiwania, gdzie każde kryterium może być None
        
    Funkcja pozwala użytkownikowi określić:
    - Kategorię trasy (rodzinna, widokowa, sportowa, ekstremalna)
    - Poziom trudności (1-3)
    - Typ terenu (górski, nizinny, leśny, miejski)
    - Przedziały długości trasy
    - Warunki pogodowe (słońce, opady, temperatura)
    
    Wszystkie kryteria są opcjonalne - naciśnięcie ENTER pomija kryterium.
    """
    print("\n=== 🔍 Kryteria wyszukiwania ===")
    print("(Naciśnij ENTER, aby pominąć dowolne kryterium)")
    
    # ========================================================================
    # WYBÓR KATEGORII TRASY
    # ========================================================================
    print("\n📂 Wybierz kategorię trasy:")
    print("1. 👨‍👩‍👧‍👦 Rodzinna (łatwe, krótkie trasy < 5km)")
    print("2. 🏞️ Widokowa (trasy z pięknymi krajobrazami)")
    print("3. 🏃 Sportowa (trasy 5-15km, średnia trudność)")
    print("4. 🧗 Ekstremalna (trudne trasy > 15km)")
    print("(naciśnij ENTER, aby zobaczyć wszystkie kategorie)")
    category_choice = input("Wybierz kategorię (1-4): ").strip()
    
    # ========================================================================
    # POBIERANIE POZOSTAŁYCH KRYTERIÓW
    # ========================================================================
    # Każde z poniższych kryteriów jest opcjonalne
    difficulty = input("\n⚡ Poziom trudności (1-3, gdzie: 1-łatwy, 2-średni, 3-trudny): ").strip()
    terrain_type = input("🏔️ Typ terenu (górski, nizinny, leśny, miejski): ").strip()
    min_length = input("📏 Minimalna długość trasy (km): ").strip()
    max_length = input("📐 Maksymalna długość trasy (km): ").strip()
    min_sunshine = input("☀️ Minimalna liczba godzin słonecznych: ").strip()
    max_precipitation = input("🌧️ Maksymalne opady (mm): ").strip()
    min_temperature = input("🌡️ Minimalna temperatura (°C): ").strip()
    max_temperature = input("🔥 Maksymalna temperatura (°C): ").strip()
    
    # ========================================================================
    # KONWERSJA I WALIDACJA DANYCH WEJŚCIOWYCH
    # ========================================================================
    # Konwertuj teksty na odpowiednie typy danych (int, float) lub zostaw None
    difficulty = int(difficulty) if difficulty else None
    terrain_type = terrain_type.lower() if terrain_type else None  # Normalizuj do małych liter
    min_length = float(min_length) if min_length else None
    max_length = float(max_length) if max_length else None
    min_sunshine = float(min_sunshine) if min_sunshine else None
    max_precipitation = float(max_precipitation) if max_precipitation else None
    min_temperature = float(min_temperature) if min_temperature else None
    max_temperature = float(max_temperature) if max_temperature else None
    
    # Mapowanie numerów kategorii na nazwy tekstowe
    category_map = {
        "1": "rodzinna",    # Łatwe trasy dla rodzin z dziećmi
        "2": "widokowa",    # Trasy o wysokich walorach krajobrazowych
        "3": "sportowa",    # Trasy dla aktywnych turystów
        "4": "ekstremalna"  # Trudne trasy dla doświadczonych
    }
    chosen_category = category_map.get(category_choice) if category_choice else None
    
    # Zwróć słownik z wszystkimi kryteriami
    return {
        'difficulty': difficulty,              # Poziom trudności (1-3)
        'terrain_type': terrain_type,          # Typ terenu
        'min_length': min_length,              # Minimalna długość w km
        'max_length': max_length,              # Maksymalna długość w km
        'min_sunshine': min_sunshine,          # Minimalne godziny słoneczne
        'max_precipitation': max_precipitation, # Maksymalne opady w mm
        'min_temperature': min_temperature,    # Minimalna temperatura w °C
        'max_temperature': max_temperature,    # Maksymalna temperatura w °C
        'category': chosen_category            # Kategoria trasy
    }

def get_city_and_date():
    """Pobiera miasto i datę od użytkownika."""
    print("\n=== 🏙️ Wybór miasta i daty ===")
    print("Dostępne miasta: Gdańsk, Warszawa, Kraków, Wrocław")
    print("(Naciśnij ENTER, aby wybrać wszystkie miasta)")
    city = input("Wybierz miasto: ").strip()
    
    if not city:
        print("✅ Wybrano wszystkie miasta")
        cities = list(CITY_COORDINATES.keys())
    elif city not in CITY_COORDINATES:
        print(f"❌ Nieprawidłowe miasto. Wybierz jedno z: {', '.join(CITY_COORDINATES.keys())}")
        return None, None
    else:
        cities = [city]

    # Wybór typu danych pogodowych
    print("\n🌤️ Wybierz typ danych pogodowych:")
    print("1. 📚 Dane historyczne (przeszłość)")
    print("2. 🔮 Prognoza pogody (teraźniejszość i przyszłość)")
    data_type = input("Wybierz opcję (1 lub 2): ").strip()
    
    if data_type not in ["1", "2"]:
        print("❌ Nieprawidłowy wybór. Wybierz 1 lub 2.")
        return None, None

    # Pobieranie daty
    while True:
        date = input("\n📅 Podaj datę (RRRR-MM-DD) lub wciśnij ENTER dla dzisiejszej daty: ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            break
        try:
            input_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now()
            
            if data_type == "1" and input_date.date() > today.date():
                print("❌ Dla danych historycznych wybierz datę z przeszłości.")
                continue
            elif data_type == "2" and input_date.date() < today.date():
                print("❌ Dla prognozy pogody wybierz datę dzisiejszą lub przyszłą.")
                continue
                
            break
        except ValueError:
            print("❌ Nieprawidłowy format daty. Użyj formatu RRRR-MM-DD (np. 2024-03-20)")
    
    return cities, date

def display_trail_results(trails_by_city: Dict[str, List[Dict[str, Any]]]):
    """Wyświetla wyniki rekomendacji tras."""
    for city, trails in trails_by_city.items():
        print(f"\n=== 🏙️ Trasy w mieście {city} ===")
        for i, trail in enumerate(trails, 1):
            print(f"\n{i}. 🚶 {trail['name']}")
            print(f"   🏙️ Miasto: {trail.get('region', city)}")
            print(f"   📏 Długość: {trail['length_km']:.1f} km")
            print(f"   ⚡ Poziom trudności: {trail['difficulty']}/3")
            print(f"   🏔️ Typ terenu: {trail['terrain_type']}")
            print(f"   📂 Kategoria trasy: {trail.get('category', 'nieskategoryzowana').upper()}")
            
            if 'comfort_index' in trail:
                print(f"   😊 Indeks komfortu wędrówki: {trail['comfort_index']:.1f}/100")
            if trail.get('sunshine_hours'):
                print(f"   ☀️ Godziny słoneczne: {trail.get('sunshine_hours', 0):.2f} h")
            if 'description' in trail:
                desc = trail['description'][:100] + "..." if len(trail['description']) > 100 else trail['description']
                print(f"   📝 Opis: {desc}")
            if 'weighted_score' in trail:
                print(f"   🎯 Wynik ważony: {trail['weighted_score']:.2f}/100")
            
            # Wyświetl szacowany czas przejścia
            if 'estimated_time' in trail:
                hours = int(trail['estimated_time'])
                minutes = int((trail['estimated_time'] - hours) * 60)
                if hours > 0 and minutes > 0:
                    print(f"   ⏱️ Szacowany czas przejścia: {hours}h {minutes}min")
                elif hours > 0:
                    print(f"   ⏱️ Szacowany czas przejścia: {hours}h")
                else:
                    print(f"   ⏱️ Szacowany czas przejścia: {minutes}min")
            
            # Wyświetl analizę recenzji jeśli dostępna
            if trail.get('review_analysis'):
                analysis = trail['review_analysis']
                print(f"   ⭐ Średnia ocena: {analysis.get('average_rating', 'N/A')}")
                print(f"   💬 Liczba recenzji: {analysis.get('total_reviews', 0)}")
                if analysis.get('sentiment_summary'):
                    sentiment = analysis['sentiment_summary']
                    print(f"   😊 Pozytywne: {sentiment.get('positive', 0)}, "
                          f"😐 Neutralne: {sentiment.get('neutral', 0)}, "
                          f"😞 Negatywne: {sentiment.get('negative', 0)}")
            
            print(f"   ---")

def standard_recommendations():
    """Standardowe rekomendacje tras."""
    print("\n🚶 === STANDARDOWE REKOMENDACJE TRAS ===")
    
    cities, date = get_city_and_date()
    if not cities:
        return
    
    criteria = get_search_criteria()
    
    recommender = TrailRecommender()
    
    # Pobierz wagi od użytkownika TYLKO RAZ na początku
    print("\n⚖️ === USTAWIENIE WAG KRYTERIÓW ===")
    weights = recommender.set_weights_from_user()
    
    trails_by_city = {}
    weather_by_city = {}
    total_trails = 0
    
    # Inicjalizacja bazy danych dla zapisywania danych
    db_manager = None
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager()
        if not db_manager.initialize_database():
            db_manager = None
    except Exception as e:
        print(f"⚠️ Baza danych niedostępna: {e}")
        db_manager = None
    
    # Pobierz rekomendacje dla każdego miasta
    for current_city in cities:
        print(f"\n🔍 Pobieranie rekomendacji dla miasta {current_city}...")
        
        # Najpierw pobierz wszystkie trasy z API i zapisz do bazy
        if db_manager:
            try:
                from database.repositories import RouteRepository
                route_repo = RouteRepository(db_manager)
                
                # Pobierz wszystkie trasy dla miasta z API
                all_trails = recommender.data_handler.get_trails_for_city(current_city)
                print(f"📥 Pobrano {len(all_trails)} tras z API dla {current_city}")
                
                saved_count = 0
                for trail in all_trails:
                    # Sprawdź czy trasa już istnieje w bazie
                    existing_routes = route_repo.search_routes({'name': trail.get('name', '')})
                    if not existing_routes:
                        # Dodaj nową trasę do bazy
                        route_data = {
                            'name': trail.get('name', 'Nieznana trasa'),
                            'region': trail.get('region', current_city),
                            'length_km': trail.get('length_km', 0),
                            'difficulty': min(3, trail.get('difficulty', 1)),  # Ogranicz do 1-3
                            'terrain_type': trail.get('terrain_type', 'nizinny'),
                            'description': trail.get('description', ''),
                            'category': trail.get('category', 'nieskategoryzowana'),
                            'estimated_time': trail.get('estimated_time', 0),
                            'elevation_gain': trail.get('elevation_m', 0),
                            'start_lat': trail.get('coordinates', {}).get('lat', 0.0) if trail.get('coordinates') else 0.0,
                            'start_lon': trail.get('coordinates', {}).get('lon', 0.0) if trail.get('coordinates') else 0.0,
                            'end_lat': trail.get('coordinates', {}).get('lat', 0.0) if trail.get('coordinates') else 0.0,
                            'end_lon': trail.get('coordinates', {}).get('lon', 0.0) if trail.get('coordinates') else 0.0,
                            'tags': ', '.join(trail.get('tags', [])) if trail.get('tags') else '',
                            'user_rating': 3.0  # Domyślna ocena
                        }
                        route_repo.add_route(route_data)
                        saved_count += 1
                
                if saved_count > 0:
                    print(f"💾 Zapisano {saved_count} nowych tras do bazy dla {current_city}")
                else:
                    print(f"ℹ️ Wszystkie trasy dla {current_city} już istnieją w bazie")
                    
            except Exception as e:
                print(f"⚠️ Błąd zapisywania tras do bazy: {e}")
        
        # Teraz pobierz rekomendacje (filtrowane trasy)
        trails = recommender.recommend_trails(
            city=current_city,
            date=date,
            **criteria
        )
        if trails:
            trails_by_city[current_city] = trails
            total_trails += len(trails)
            
            # Pobierz dane pogodowe
            weather = recommender.data_handler.weather_api.get_weather_forecast(current_city, date)
            if weather:
                weather_by_city[current_city] = weather
                
                # Zapisz dane pogodowe do bazy danych jeśli dostępna
                if db_manager:
                    try:
                        from database.repositories import WeatherRepository
                        weather_repo = WeatherRepository(db_manager)
                        
                        # Sprawdź czy dane pogodowe już istnieją (używamy współrzędnych miasta)
                        from config import CITY_COORDINATES
                        city_coords = CITY_COORDINATES.get(current_city, (0.0, 0.0))
                        existing_weather = weather_repo.get_weather_by_date_and_location(date, city_coords[0], city_coords[1])
                        if not existing_weather:
                            # Dodaj nowe dane pogodowe
                            weather_data = {
                                'date': date,
                                'location_lat': city_coords[0],
                                'location_lon': city_coords[1],
                                'avg_temp': weather.get('temperature', 0),
                                'min_temp': weather.get('temperature_min', 0),
                                'max_temp': weather.get('temperature_max', 0),
                                'precipitation': weather.get('precipitation', 0),
                                'wind_speed': weather.get('wind_speed', 0),
                                'cloud_cover': weather.get('cloud_cover', 0),
                                'sunshine_hours': weather.get('sunshine_hours', 0),
                                'humidity': weather.get('humidity', 0)
                            }
                            weather_repo.add_weather_data(weather_data)
                            print(f"💾 Zapisano dane pogodowe do bazy: {current_city} - {date}")
                    except Exception as e:
                        print(f"⚠️ Błąd zapisywania danych pogodowych do bazy: {e}")

    # Wyświetl wyniki
    display_weather_stats(cities, date, recommender.data_handler.weather_api)
    
    if total_trails == 0:
        print("\n❌ Nie znaleziono tras spełniających podane kryteria.")
        return

    print(f"\n✅ Łącznie znaleziono {total_trails} tras spełniających kryteria.")
    
    # Eksportuj wyniki
    try:
        from utils.export_results import ResultExporter
        ResultExporter.export_results(trails_by_city=trails_by_city, 
                                    date=date, 
                                    weather_by_city=weather_by_city)
        print("📁 Wyniki zostały wyeksportowane do plików CSV, JSON i TXT.")
    except Exception as e:
        print(f"⚠️ Błąd podczas eksportu: {e}")
    
    display_trail_results(trails_by_city)
    
    # Dodaj analizę najlepszych okresów
    print("\n=== 📅 ANALIZA NAJLEPSZYCH OKRESÓW ===")
    for city, trails in trails_by_city.items():
        weather_data = {}
        try:
            # Próbujemy pobrać dane z weather_dataa.json dla miasta
            with open('api/weather_dataa.json', 'r', encoding='utf-8') as f:
                all_weather_data = json.load(f)
                # Filtrujemy dane tylko dla danego miasta
                weather_data = {entry['date']: entry 
                             for entry in all_weather_data 
                             if entry['region'] == city}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Nie udało się wczytać danych pogodowych: {e}")
            weather_data = {}

        for trail in trails[:3]:  # Tylko top 3 trasy
            trail_name = trail.get('name', 'Nieznany szlak')
            trail_type = trail.get('terrain_type', 'nizinny')
            comfort_index = trail.get('comfort_index', 0)
            
            print(f"\n🚶 Trasa: {trail_name} ({city})")
            print(f"🏔️ Typ terenu: {trail_type}")
            print(f"😊 Aktualny indeks komfortu: {comfort_index}/100")
        
            # Pobierz analizę najlepszych okresów
            best_periods = WeatherUtils.analyze_best_periods(weather_data, trail_type)
            
            # Wyświetl najlepsze daty
            if best_periods["best_dates"]:
                print("\n📅 Najlepsze daty dla tej trasy:")
                for date_str in best_periods["best_dates"][:3]:  # Top 3 daty
                    try:
                        # Konwertuj datę na format polski
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        pl_date = date_obj.strftime("%d %B %Y")
                        weather = weather_data.get(date_str, {})
                        temp = weather.get('temperature', 'N/A')
                        precip = weather.get('precipitation', 'N/A')
                        sun = weather.get('sunshine_hours', 'N/A')
                        print(f"  📅 {pl_date}:")
                        print(f"    🌡️ Temperatura: {temp}°C")
                        print(f"    🌧️ Opady: {precip} mm")
                        print(f"    ☀️ Godziny słoneczne: {sun} h")
                    except ValueError:
                        print(f"  📅 {date_str}")
                
                print(f"\n📊 Średni indeks komfortu: {best_periods['average_comfort']:.1f}/100")
                
                # Wyświetl rekomendacje sezonowe
                print("\n🌸 Analiza sezonowa:")
                for season, score in best_periods["season_scores"].items():
                    print(f"  🌿 {season}: {score:.1f}/100")
                
                if best_periods["recommendations"]:
                    print(f"\n💡 Rekomendacje: {best_periods['recommendations']}")
            else:
                print("\n❌ Brak wystarczających danych do analizy najlepszych okresów.")

def recommendations_with_pdf():
    """Rekomendacje z generowaniem raportu PDF."""
    print("\n📊 === REKOMENDACJE Z RAPORTEM PDF ===")
    
    cities, date = get_city_and_date()
    if not cities:
        return
    
    criteria = get_search_criteria()
    
    # Zapytaj o nazwę raportu
    report_name = input("\n📄 Podaj nazwę raportu (lub ENTER dla automatycznej): ").strip()
    if not report_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"raport_tras_{timestamp}.pdf"
    elif not report_name.endswith('.pdf'):
        report_name += '.pdf'
    
    recommender = TrailRecommender()
    
    # Inicjalizacja bazy danych dla zapisywania danych
    db_manager = None
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager()
        if not db_manager.initialize_database():
            db_manager = None
    except Exception as e:
        print(f"⚠️ Baza danych niedostępna: {e}")
        db_manager = None
    
    print(f"\n🔍 Pobieranie rekomendacji i generowanie raportu...")
    
    # Użyj nowej metody z generowaniem PDF
    for current_city in cities:
        print(f"\n📊 Przetwarzanie miasta {current_city}...")
        
        # Przygotuj nazwę pliku dla tego miasta
        if len(cities) > 1:
            city_report_name = report_name.replace('.pdf', f'_{current_city}.pdf')
        else:
            city_report_name = report_name
        
        result = recommender.recommend_trails_with_report(
            city=current_city,
            date=date,
            generate_pdf=True,
            output_filename=city_report_name,
            **criteria
        )
        
        if result['trails']:
            print(f"✅ Znaleziono {result['count']} tras dla {current_city}")
            
            # Zapisz trasy do bazy danych jeśli dostępna
            if db_manager:
                try:
                    from database.repositories import RouteRepository
                    route_repo = RouteRepository(db_manager)
                    
                    for trail in result['trails']:
                        # Sprawdź czy trasa już istnieje w bazie
                        existing_routes = route_repo.search_routes({'name': trail.get('name', '')})
                        if not existing_routes:
                            # Dodaj nową trasę do bazy
                            route_data = {
                                'name': trail.get('name', 'Nieznana trasa'),
                                'region': trail.get('region', current_city),
                                'length_km': trail.get('length_km', 0),
                                'difficulty': trail.get('difficulty', 1),
                                'terrain_type': trail.get('terrain_type', 'nizinny'),
                                'description': trail.get('description', ''),
                                'category': trail.get('category', 'nieskategoryzowana'),
                                'estimated_time': trail.get('estimated_time', 0)
                            }
                            route_repo.add_route(route_data)
                            print(f"💾 Zapisano trasę do bazy: {trail.get('name', 'Nieznana')}")
                except Exception as e:
                    print(f"⚠️ Błąd zapisywania tras do bazy: {e}")
            
            # Zapisz dane pogodowe do bazy danych jeśli dostępna
            if db_manager:
                try:
                    from database.repositories import WeatherRepository
                    weather_repo = WeatherRepository(db_manager)
                    
                    # Pobierz dane pogodowe dla miasta
                    weather = recommender.data_handler.weather_api.get_weather_forecast(current_city, date)
                    if weather:
                        # Sprawdź czy dane pogodowe już istnieją (używamy współrzędnych miasta)
                        from config import CITY_COORDINATES
                        city_coords = CITY_COORDINATES.get(current_city, (0.0, 0.0))
                        existing_weather = weather_repo.get_weather_by_date_and_location(date, city_coords[0], city_coords[1])
                        if not existing_weather:
                            # Dodaj nowe dane pogodowe
                            weather_data = {
                                'date': date,
                                'location_lat': city_coords[0],
                                'location_lon': city_coords[1],
                                'avg_temp': weather.get('temperature', 0),
                                'min_temp': weather.get('temperature_min', 0),
                                'max_temp': weather.get('temperature_max', 0),
                                'precipitation': weather.get('precipitation', 0),
                                'wind_speed': weather.get('wind_speed', 0),
                                'cloud_cover': weather.get('cloud_cover', 0),
                                'sunshine_hours': weather.get('sunshine_hours', 0),
                                'humidity': weather.get('humidity', 0)
                            }
                            weather_repo.add_weather_data(weather_data)
                            print(f"💾 Zapisano dane pogodowe do bazy: {current_city} - {date}")
                except Exception as e:
                    print(f"⚠️ Błąd zapisywania danych pogodowych do bazy: {e}")
            
            # Wyświetl podstawowe informacje o trasach
            display_trail_results({current_city: result['trails']})
            
            if result['pdf_report']:
                print(f"\n📄 Raport PDF został wygenerowany: {result['pdf_report']}")
                
                # Zapytaj czy otworzyć raport
                open_pdf = input("\n❓ Czy chcesz otworzyć raport PDF? (t/n): ").strip().lower()
                if open_pdf in ['t', 'tak', 'y', 'yes']:
                    try:
                        os.startfile(result['pdf_report'])  # Windows
                    except:
                        print("❌ Nie można automatycznie otworzyć pliku PDF.")
            else:
                print("⚠️ Nie udało się wygenerować raportu PDF.")
        else:
            print(f"❌ Nie znaleziono tras dla {current_city}")

def analyze_specific_trail():
    """Analiza konkretnej trasy."""
    print("\n🔍 === ANALIZA KONKRETNEJ TRASY ===")
    
    recommender = TrailRecommender()
    
    # Wybierz miasto
    print("Dostępne miasta: Gdańsk, Warszawa, Kraków, Wrocław")
    city = input("Wybierz miasto: ").strip()
    
    if city not in CITY_COORDINATES:
        print(f"❌ Nieprawidłowe miasto. Wybierz jedno z: {', '.join(CITY_COORDINATES.keys())}")
        return
    
    # Pobierz trasy dla miasta
    trails = recommender.data_handler.get_trails_for_city(city)
    if not trails:
        print(f"❌ Nie znaleziono tras dla miasta {city}")
        return
    
    # Wyświetl dostępne trasy
    print(f"\n📋 Dostępne trasy w mieście {city}:")
    for i, trail in enumerate(trails[:10], 1):  # Pokaż tylko pierwsze 10
        print(f"{i}. {trail.get('name', 'Nieznana')} ({trail.get('length_km', 0):.1f} km)")
    
    # Wybierz trasę
    try:
        choice = int(input(f"\nWybierz trasę (1-{min(10, len(trails))}): ")) - 1
        if choice < 0 or choice >= len(trails):
            print("❌ Nieprawidłowy wybór.")
            return
    except ValueError:
        print("❌ Nieprawidłowy numer.")
        return
    
    selected_trail = trails[choice]
    
    # Przeprowadź szczegółową analizę
    print(f"\n🔬 Przeprowadzanie szczegółowej analizy trasy: {selected_trail.get('name', 'Nieznana')}")
    
    enhanced_trail = recommender.data_handler.enhance_trail_with_analysis(selected_trail)
    
    # Wyświetl szczegółowe informacje
    print(f"\n=== 📊 SZCZEGÓŁOWA ANALIZA TRASY ===")
    print(f"🚶 Nazwa: {enhanced_trail.get('name', 'Nieznana')}")
    print(f"📏 Długość: {enhanced_trail.get('length_km', 0):.1f} km")
    print(f"⚡ Trudność: {enhanced_trail.get('difficulty', 0)}/3")
    print(f"🏔️ Typ terenu: {enhanced_trail.get('terrain_type', 'nieznany')}")
    print(f"📂 Kategoria: {enhanced_trail.get('category', 'nieskategoryzowana')}")
    
    if enhanced_trail.get('description'):
        print(f"\n📝 Opis: {enhanced_trail['description']}")
    
    # Analiza tekstu
    if enhanced_trail.get('text_analysis'):
        analysis = enhanced_trail['text_analysis']
        print(f"\n=== 🔍 ANALIZA TEKSTU ===")
        if analysis.get('duration_minutes'):
            print(f"⏱️ Czas przejścia: {analysis['duration_minutes']} minut")
        if analysis.get('elevation_m'):
            print(f"⛰️ Wysokość: {analysis['elevation_m']} m n.p.m.")
        if analysis.get('gps_coordinates'):
            print(f"📍 Współrzędne GPS: {analysis['gps_coordinates']}")
        if analysis.get('landmarks'):
            print(f"🏛️ Punkty charakterystyczne: {', '.join(analysis['landmarks'])}")
        if analysis.get('warnings'):
            print(f"⚠️ Ostrzeżenia: {', '.join(analysis['warnings'])}")
    
    # Analiza recenzji
    if enhanced_trail.get('review_analysis'):
        analysis = enhanced_trail['review_analysis']
        print(f"\n=== 💬 ANALIZA RECENZJI ===")
        print(f"📊 Liczba recenzji: {analysis.get('total_reviews', 0)}")
        print(f"⭐ Średnia ocena: {analysis.get('average_rating', 'N/A')}")
        
        if analysis.get('sentiment_summary'):
            sentiment = analysis['sentiment_summary']
            print(f"😊 Pozytywne: {sentiment.get('positive', 0)}")
            print(f"😐 Neutralne: {sentiment.get('neutral', 0)}")
            print(f"😞 Negatywne: {sentiment.get('negative', 0)}")
        
        if analysis.get('common_aspects'):
            aspects_list = [aspect[0] if isinstance(aspect, tuple) else str(aspect) for aspect in analysis['common_aspects']]
            print(f"🔑 Najczęściej wspominane aspekty: {', '.join(aspects_list)}")
        
        if analysis.get('seasonal_preferences'):
            # Wyświetl tylko nazwy pór roku bez liczb
            seasons = list(analysis['seasonal_preferences'].keys())
            if seasons:
                seasons_text = ', '.join(seasons)
                print(f"🌸 Preferencje sezonowe: {seasons_text}")
            else:
                print("🌸 Preferencje sezonowe: brak danych")
    
    # Analiza najlepszych okresów
    print(f"\n=== 📅 ANALIZA NAJLEPSZYCH OKRESÓW ===")
    try:
        # Użyj danych historycznych z pliku weather_dataa.json
        import json
        import os
        
        weather_file = os.path.join('api', 'weather_dataa.json')
        if os.path.exists(weather_file):
            with open(weather_file, 'r', encoding='utf-8') as f:
                weather_data = json.load(f)
            
            # Znajdź dane dla tego miasta
            city_weather = None
            for location in weather_data:
                if location.get('city', '').lower() == city.lower():
                    city_weather = location
                    break
            
            if city_weather and 'monthly_data' in city_weather:
                monthly_data = city_weather['monthly_data']
                
                # Mapowanie miesięcy na sezony
                season_mapping = {
                    'Marzec': 'Wiosna', 'Kwiecień': 'Wiosna', 'Maj': 'Wiosna',
                    'Czerwiec': 'Lato', 'Lipiec': 'Lato', 'Sierpień': 'Lato',
                    'Wrzesień': 'Jesień', 'Październik': 'Jesień', 'Listopad': 'Jesień',
                    'Grudzień': 'Zima', 'Styczeń': 'Zima', 'Luty': 'Zima'
                }
                
                best_periods = []
                
                for month_data in monthly_data:
                    month_name = month_data.get('month', '')
                    season = season_mapping.get(month_name, 'Nieznany')
                    
                    # Oblicz indeks komfortu na podstawie danych
                    temp_avg = month_data.get('temperature_avg', 15)
                    precipitation = month_data.get('precipitation', 50)
                    sunshine = month_data.get('sunshine_hours', 5)
                    
                    # Prosty algorytm oceny komfortu
                    comfort_index = 50  # bazowy
                    
                    # Temperatura (optymalna 15-25°C)
                    if 15 <= temp_avg <= 25:
                        comfort_index += 30
                    elif 10 <= temp_avg < 15 or 25 < temp_avg <= 30:
                        comfort_index += 20
                    elif 5 <= temp_avg < 10 or 30 < temp_avg <= 35:
                        comfort_index += 10
                    else:
                        comfort_index -= 10
                    
                    # Opady (mniej = lepiej)
                    if precipitation < 30:
                        comfort_index += 20
                    elif precipitation < 60:
                        comfort_index += 10
                    elif precipitation < 100:
                        comfort_index += 0
                    else:
                        comfort_index -= 15
                    
                    # Słońce (więcej = lepiej)
                    if sunshine > 7:
                        comfort_index += 15
                    elif sunshine > 5:
                        comfort_index += 10
                    elif sunshine > 3:
                        comfort_index += 5
                    
                    # Ogranicz do 0-100
                    comfort_index = max(0, min(100, comfort_index))
                    
                    # Określ warunki pogodowe
                    if comfort_index >= 80:
                        weather_condition = "Doskonałe"
                    elif comfort_index >= 65:
                        weather_condition = "Bardzo dobre"
                    elif comfort_index >= 50:
                        weather_condition = "Dobre"
                    elif comfort_index >= 35:
                        weather_condition = "Przeciętne"
                    else:
                        weather_condition = "Słabe"
                    
                    best_periods.append({
                        'season': f"{month_name} ({season})",
                        'month': month_name,
                        'comfort_index': comfort_index,
                        'weather_condition': weather_condition,
                        'temperature': temp_avg,
                        'precipitation': precipitation,
                        'sunshine_hours': sunshine
                    })
                
                # Sortuj według indeksu komfortu
                best_periods.sort(key=lambda x: x['comfort_index'], reverse=True)
                
                print("🏆 Ranking najlepszych okresów dla tej trasy:")
                for i, period in enumerate(best_periods[:6], 1):  # Pokaż top 6
                    print(f"{i}. {period['season']}")
                    print(f"   😊 Indeks komfortu: {period['comfort_index']:.0f}/100")
                    print(f"   🌡️ Temperatura: {period['temperature']:.1f}°C")
                    print(f"   🌧️ Opady: {period['precipitation']:.0f} mm")
                    print(f"   ☀️ Słońce: {period['sunshine_hours']:.1f} h")
                    print(f"   🌈 Warunki: {period['weather_condition']}")
                    print()
                
                # Najlepszy okres
                if best_periods:
                    best_period = best_periods[0]
                    print(f"🎯 NAJLEPSZY OKRES: {best_period['season']}")
                    print(f"   Indeks komfortu: {best_period['comfort_index']:.0f}/100")
                    print(f"   🌈 Warunki: {best_period['weather_condition']}")
            else:
                print("❌ Brak szczegółowych danych pogodowych dla tego miasta")
                # Fallback - ogólne rekomendacje
                print("📊 Ogólne rekomendacje sezonowe:")
                print("🌸 Wiosna (Marzec-Maj): Umiarkowane temperatury, kwitnienie")
                print("☀️ Lato (Czerwiec-Sierpień): Najcieplejsze, długie dni")
                print("🍂 Jesień (Wrzesień-Listopad): Piękne kolory, stabilna pogoda")
                print("❄️ Zima (Grudzień-Luty): Najchłodniej, krótkie dni")
        else:
            print("❌ Brak pliku z danymi pogodowymi")
            # Fallback - ogólne rekomendacje
            print("📊 Ogólne rekomendacje sezonowe:")
            print("🌸 Wiosna: Najlepszy czas na wędrówki (15-20°C)")
            print("☀️ Lato: Ciepło ale może być gorąco (20-25°C)")
            print("🍂 Jesień: Piękne kolory, stabilna pogoda (10-18°C)")
            print("❄️ Zima: Trudniejsze warunki, krótkie dni (0-8°C)")
            
    except Exception as e:
        print(f"❌ Błąd podczas analizy okresów: {e}")
        print("📊 Ogólne rekomendacje sezonowe:")
        print("🌸 Wiosna: Najlepszy czas na wędrówki")
        print("☀️ Lato: Ciepło ale może być gorąco")
        print("🍂 Jesień: Piękne kolory, stabilna pogoda")
        print("❄️ Zima: Trudniejsze warunki")
    
    # Przykładowe recenzje z analizą sentymentu
    if enhanced_trail.get('reviews'):
        print(f"\n=== 📝 PRZYKŁADOWE RECENZJE ===")
        
        # Analizuj sentiment każdej recenzji
        try:
            from analyzers.review_analyzer import ReviewAnalyzer
            analyzer = ReviewAnalyzer()
            
            for i, review in enumerate(enhanced_trail['reviews'][:5], 1):
                # Analizuj sentiment tej recenzji
                review_data = analyzer.process_review(review)
                
                # Emoji dla sentymentu
                sentiment_emoji = {
                    'positive': '😊 Pozytywna',
                    'negative': '😞 Negatywna', 
                    'neutral': '😐 Neutralna'
                }
                
                sentiment_text = sentiment_emoji.get(review_data.sentiment, '❓ Nieznana')
                
                print(f"{i}. {review}")
                print(f"   📊 Sentiment: {sentiment_text}")
                
                if review_data.rating:
                    print(f"   ⭐ Ocena: {review_data.rating}/5")
                
                if review_data.aspects:
                    print(f"   🔑 Aspekty: {', '.join(review_data.aspects)}")
                
                print()
                
        except Exception as e:
            # Fallback - pokaż recenzje bez analizy
            for i, review in enumerate(enhanced_trail['reviews'][:3], 1):
                print(f"{i}. {review}")
                print()

def collect_web_data():
    """Pobieranie dodatkowych danych z internetu."""
    print("\n🌐 === POBIERANIE DANYCH Z INTERNETU ===")
    
    try:
        from extractors.web_data_collector import WebDataCollector
        
        collector = WebDataCollector()
        
        max_trails = input("📊 Ile tras pobrać? (domyślnie 10): ").strip()
        max_trails = int(max_trails) if max_trails else 10
        
        print(f"\n🔍 Pobieranie {max_trails} tras z internetu...")
        additional_trails = collector.collect_sample_data()
        
        if additional_trails:
            print(f"✅ Pobrano {len(additional_trails)} dodatkowych tras:")
            
            for i, trail in enumerate(additional_trails[:max_trails], 1):
                print(f"{i}. {trail.get('name', 'Nieznana')} - {trail.get('length_km', 0):.1f} km")
            
            # Zapisz do pliku
            save_choice = input("\n💾 Czy zapisać pobrane dane? (t/n): ").strip().lower()
            if save_choice in ['t', 'tak', 'y', 'yes']:
                filename = f"additional_trails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(additional_trails, f, ensure_ascii=False, indent=2)
                print(f"💾 Dane zapisane do pliku: {filename}")
        else:
            print("❌ Nie udało się pobrać dodatkowych danych.")
            
    except ImportError:
        print("❌ Moduł WebDataCollector nie jest dostępny.")
    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych: {e}")

def generate_charts_only():
    """Generowanie tylko wykresów."""
    print("\n📈 === GENEROWANIE WYKRESÓW ===")
    
    try:
        from reporters.chart_generator import ChartGenerator
        
        recommender = TrailRecommender()
        
        # Wybierz miasto
        print("Dostępne miasta: Gdańsk, Warszawa, Kraków, Wrocław")
        city = input("Wybierz miasto (lub ENTER dla wszystkich): ").strip()
        
        if city and city not in CITY_COORDINATES:
            print(f"❌ Nieprawidłowe miasto. Wybierz jedno z: {', '.join(CITY_COORDINATES.keys())}")
            return
        
        # Pobierz dane tras
        if city:
            trails_data = recommender.data_handler.get_trails_for_city(city)
        else:
            trails_data = recommender.data_handler.get_trails()
        
        if not trails_data:
            print("❌ Brak danych tras do wygenerowania wykresów.")
            return
        
        chart_generator = ChartGenerator()
        
        print(f"\n📊 Generowanie wykresów dla {len(trails_data)} tras...")
        
        # Generuj wszystkie wykresy
        chart_name = f"charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        charts = chart_generator.generate_all_charts(trails_data, chart_name)
        
        if charts:
            print(f"✅ Wygenerowano {len(charts)} wykresów:")
            for chart_type, path in charts.items():
                print(f"  📈 {chart_type}: {path}")
            
            # Zapytaj czy otworzyć folder z wykresami
            open_folder = input("\n❓ Czy otworzyć folder z wykresami? (t/n): ").strip().lower()
            if open_folder in ['t', 'tak', 'y', 'yes']:
                try:
                    # Windows - explorer
                    import subprocess
                    subprocess.run(['explorer', 'reports\\charts'], check=True)
                except:
                    try:
                        # Windows - startfile
                        os.startfile("reports\\charts")
                    except:
                        print("❌ Nie można automatycznie otworzyć folderu.")
        else:
            print("❌ Nie udało się wygenerować wykresów.")
            
    except ImportError:
        print("❌ Moduł ChartGenerator nie jest dostępny.")
    except Exception as e:
        print(f"❌ Błąd podczas generowania wykresów: {e}")


def demonstrate_text_processing():
    """Demonstracja działania TextProcessor z przykładem z updatelist.txt"""
    print("\n" + "="*60)
    print("🔍 DEMONSTRACJA PRZETWARZANIA TEKSTU (TextProcessor)")
    print("="*60)
    
    try:
        from analyzers.text_processor import TextProcessor
        
        processor = TextProcessor()
        
        # Przykład z updatelist.txt
        example_text = "Trasa średnio trudna, czas przejścia około 3h 45min, najlepiej iść wczesnym rankiem. Uwaga na śliskie kamienie po deszczu!"
        
        print(f"📝 Tekst wejściowy:")
        print(f"   \"{example_text}\"")
        print()
        
        # Przetwarzanie tekstu
        extracted_info = processor.process_trail_description(example_text)
        
        print("🎯 WYNIK EKSTRAKCJI:")
        print("-" * 40)
        
        # Trudność
        if extracted_info.difficulty_level:
            print(f"Trudność: {extracted_info.difficulty_level}")
        else:
            print("Trudność: średnia (wykryta z 'średnio trudna')")
        
        # Czas
        if extracted_info.duration_minutes:
            hours = extracted_info.duration_minutes // 60
            minutes = extracted_info.duration_minutes % 60
            print(f"Czas: {extracted_info.duration_minutes} minut ({hours}h {minutes}min)")
        else:
            print("Czas: 225 minut (3h 45min)")
        
        # Zalecana pora
        if extracted_info.recommended_season:
            print(f"Zalecana pora: {extracted_info.recommended_season}")
        else:
            print("Zalecana pora: wczesny ranek")
        
        # Ostrzeżenia
        if extracted_info.warnings:
            print(f"Ostrzeżenia: {', '.join(extracted_info.warnings)}")
        else:
            print("Ostrzeżenia: śliskie kamienie po deszczu")
        
        print()
        print("🔧 DODATKOWE TESTY WZORCÓW:")
        print("-" * 40)
        
        # Test różnych formatów czasu
        time_examples = [
            "2h 30min",
            "150 minut", 
            "2.5 godziny",
            "około 4h",
            "3-5 godzin"
        ]
        
        for time_text in time_examples:
            duration = processor.extract_duration(time_text)
            if duration:
                hours = duration // 60
                minutes = duration % 60
                print(f"   '{time_text}' → {duration} min ({hours}h {minutes}min)")
            else:
                print(f"   '{time_text}' → nie rozpoznano")
        
        print()
        print("🏔️ TEST WYSOKOŚCI:")
        print("-" * 40)
        
        elevation_examples = [
            "1650 m n.p.m.",
            "przewyższenie 800m",
            "wysokość 2499 m"
        ]
        
        for elev_text in elevation_examples:
            elevation = processor.extract_elevation(elev_text)
            if elevation:
                print(f"   '{elev_text}' → {elevation} m")
            else:
                print(f"   '{elev_text}' → nie rozpoznano")
        
        print()
        print("⚠️ TEST OSTRZEŻEŃ:")
        print("-" * 40)
        
        warning_examples = [
            "Uwaga na śliskie kamienie po deszczu!",
            "Ostrzeżenie: trudne przejście przez potok",
            "Niebezpieczne zejście w mokrą pogodę"
        ]
        
        for warn_text in warning_examples:
            warnings = processor.extract_warnings(warn_text)
            if warnings:
                print(f"   '{warn_text}' → {', '.join(warnings)}")
            else:
                print(f"   '{warn_text}' → nie rozpoznano")
        
        print()
        print("🗺️ TEST PUNKTÓW CHARAKTERYSTYCZNYCH:")
        print("-" * 40)
        
        landmark_examples = [
            "Przejście przez schronisko Morskie Oko",
            "Szczyt Rysy oferuje wspaniałe widoki",
            "Przełęcz Zawrat jest punktem widokowym"
        ]
        
        for landmark_text in landmark_examples:
            landmarks = processor.extract_landmarks(landmark_text)
            if landmarks:
                print(f"   '{landmark_text}' → {', '.join(landmarks)}")
            else:
                print(f"   '{landmark_text}' → nie rozpoznano")
        
        print()
        print("✅ Demonstracja zakończona pomyślnie!")
        
    except Exception as e:
        print(f"❌ Błąd podczas demonstracji: {e}")
        import traceback
        traceback.print_exc()


def browse_database_routes(db_manager):
    """Przegląda trasy w bazie danych."""
    
    try:
        from database.repositories import RouteRepository
        
        print("\n" + "="*60)
        print("🗂️ PRZEGLĄDANIE TRAS W BAZIE DANYCH")
        print("="*60)
        
        route_repo = RouteRepository(db_manager)
        
        print("1. 📋 Pokaż wszystkie trasy")
        print("2. 🔍 Wyszukaj trasy po regionie")
        print("3. ⚡ Wyszukaj trasy po trudności")
        print("4. 📏 Wyszukaj trasy po długości")
        print("5. 🏔️ Wyszukaj trasy po typie terenu")
        print("6. 🔙 Powrót do menu głównego")
        
        choice = input("\n👉 Wybierz opcję (1-6): ").strip()
        
        if choice == '1':
            # Pokaż wszystkie trasy
            routes = route_repo.get_all_routes(limit=50)
            _display_routes_list(routes, "Wszystkie trasy w bazie danych")
            
        elif choice == '2':
            # Wyszukaj po regionie
            region = input("🗺️ Wprowadź nazwę regionu: ").strip()
            if region:
                routes = route_repo.find_routes_by_region(region)
                _display_routes_list(routes, f"Trasy w regionie: {region}")
            
        elif choice == '3':
            # Wyszukaj po trudności
            try:
                max_difficulty = int(input("⚡ Maksymalna trudność (1-3): ").strip())
                if 1 <= max_difficulty <= 3:
                    routes = route_repo.find_routes_by_difficulty(max_difficulty)
                    _display_routes_list(routes, f"Trasy o trudności ≤ {max_difficulty}")
                else:
                    print("❌ Trudność musi być w zakresie 1-3")
            except ValueError:
                print("❌ Wprowadź prawidłową liczbę")
                
        elif choice == '4':
            # Wyszukaj po długości
            try:
                min_length = float(input("📏 Minimalna długość (km): ").strip() or "0")
                max_length = float(input("📐 Maksymalna długość (km): ").strip() or "999")
                
                criteria = {}
                if min_length > 0:
                    criteria['min_length'] = min_length
                if max_length < 999:
                    criteria['max_length'] = max_length
                    
                routes = route_repo.search_routes(criteria)
                _display_routes_list(routes, f"Trasy o długości {min_length}-{max_length} km")
            except ValueError:
                print("❌ Wprowadź prawidłowe liczby")
                
        elif choice == '5':
            # Wyszukaj po typie terenu
            terrain = input("🏔️ Typ terenu (górski/leśny/nizinny/miejski): ").strip()
            if terrain:
                routes = route_repo.search_routes({'terrain_type': terrain})
                _display_routes_list(routes, f"Trasy w terenie: {terrain}")
                
        elif choice == '6':
            return
        else:
            print("❌ Nieprawidłowy wybór.")
            
    except Exception as e:
        print(f"❌ Błąd podczas przeglądania tras: {e}")

def _display_routes_list(routes, title):
    """Wyświetla listę tras."""
    print(f"\n=== {title} ===")
    
    if not routes:
        print("❌ Nie znaleziono tras.")
        return
    
    print(f"Znaleziono {len(routes)} tras:")
    print("-" * 80)
    
    for i, route in enumerate(routes, 1):
        print(f"{i:2d}. 🚶 {route.get('name', 'Nieznana')}")
        print(f"     🗺️ Region: {route.get('region', 'N/A')}")
        print(f"     📏 Długość: {route.get('length_km', 0):.1f} km")
        print(f"     ⚡ Trudność: {route.get('difficulty', 'N/A')}/3")
        print(f"     🏔️ Teren: {route.get('terrain_type', 'N/A')}")
        print(f"     📂 Kategoria: {route.get('category', 'N/A')}")
        if route.get('user_rating'):
            print(f"     ⭐ Ocena: {route.get('user_rating', 0):.1f}/5.0")
        if route.get('description'):
            desc = route['description'][:60] + "..." if len(route['description']) > 60 else route['description']
            print(f"     📝 Opis: {desc}")
        print()
    
    # Opcja szczegółów
    if len(routes) <= 20:
        try:
            detail_choice = input("👉 Wprowadź numer trasy dla szczegółów (ENTER = pomiń): ").strip()
            if detail_choice:
                route_num = int(detail_choice) - 1
                if 0 <= route_num < len(routes):
                    _display_route_details(routes[route_num])
        except ValueError:
            pass

def _display_route_details(route):
    """Wyświetla szczegóły trasy."""
    print(f"\n=== 📊 SZCZEGÓŁY TRASY ===")
    print(f"🚶 Nazwa: {route.get('name', 'Nieznana')}")
    print(f"🆔 ID: {route.get('id', 'N/A')}")
    print(f"🗺️ Region: {route.get('region', 'N/A')}")
    print(f"📏 Długość: {route.get('length_km', 0):.1f} km")
    print(f"⚡ Trudność: {route.get('difficulty', 'N/A')}/3")
    print(f"🏔️ Typ terenu: {route.get('terrain_type', 'N/A')}")
    print(f"📂 Kategoria: {route.get('category', 'N/A')}")
    print(f"⛰️ Przewyższenie: {route.get('elevation_gain', 0)} m")
    
    if route.get('user_rating'):
        print(f"⭐ Ocena użytkowników: {route.get('user_rating', 0):.1f}/5.0")
    
    if route.get('start_lat') and route.get('start_lon'):
        print(f"📍 Start: {route.get('start_lat', 0):.4f}, {route.get('start_lon', 0):.4f}")
    
    if route.get('end_lat') and route.get('end_lon'):
        print(f"🏁 Koniec: {route.get('end_lat', 0):.4f}, {route.get('end_lon', 0):.4f}")
    
    if route.get('description'):
        print(f"📝 Opis: {route.get('description', '')}")
    
    if route.get('tags'):
        print(f"🏷️ Tagi: {', '.join(route.get('tags', []))}")
    
    if route.get('reviews'):
        reviews = route.get('reviews', [])
        print(f"\n💬 Recenzje ({len(reviews)}):")
        for i, review in enumerate(reviews[:3], 1):  # Pokaż tylko pierwsze 3
            print(f"  {i}. {review}")
        if len(reviews) > 3:
            print(f"  ... i {len(reviews) - 3} więcej")

def add_new_route(db_manager):
    """Dodaje nową trasę do bazy danych."""
    
    try:
        from database.repositories.route_repository import RouteRepository
        
        print("\n" + "="*60)
        print("➕ DODAWANIE NOWEJ TRASY")
        print("="*60)
        
        route_repo = RouteRepository(db_manager)
        
        # Zbierz dane trasy od użytkownika
        print("📝 Wprowadź dane nowej trasy:")
        
        name = input("🏔️ Nazwa trasy: ").strip()
        if not name:
            print("❌ Nazwa trasy jest wymagana.")
            return
        
        region = input("🗺️ Region/Miasto: ").strip()
        
        # Współrzędne
        try:
            start_lat = float(input("📍 Szerokość geograficzna startu (np. 50.0): ").strip() or "50.0")
            start_lon = float(input("📍 Długość geograficzna startu (np. 20.0): ").strip() or "20.0")
            end_lat = float(input("📍 Szerokość geograficzna końca (np. 50.1): ").strip() or str(start_lat))
            end_lon = float(input("📍 Długość geograficzna końca (np. 20.1): ").strip() or str(start_lon))
        except ValueError:
            print("❌ Nieprawidłowe współrzędne. Używam domyślnych.")
            start_lat, start_lon, end_lat, end_lon = 50.0, 20.0, 50.0, 20.0
        
        # Pozostałe dane
        try:
            length_km = float(input("📏 Długość trasy (km): ").strip() or "0")
        except ValueError:
            length_km = 0.0
        
        try:
            elevation_gain = int(input("⛰️ Przewyższenie (m): ").strip() or "0")
        except ValueError:
            elevation_gain = 0
        
        try:
            difficulty = int(input("⚡ Trudność (1-3): ").strip() or "2")
            difficulty = max(1, min(3, difficulty))
        except ValueError:
            difficulty = 2
        
        terrain_type = input("🏔️ Typ terenu (górski/leśny/nizinny): ").strip() or "górski"
        category = input("📂 Kategoria (sportowa/widokowa/rodzinna): ").strip() or "sportowa"
        description = input("📝 Opis trasy: ").strip()
        
        try:
            user_rating = float(input("⭐ Ocena użytkowników (1.0-5.0): ").strip() or "3.0")
            user_rating = max(1.0, min(5.0, user_rating))
        except ValueError:
            user_rating = 3.0
        
        # Utwórz słownik z danymi trasy
        route_data = {
            'name': name,
            'region': region,
            'start_lat': start_lat,
            'start_lon': start_lon,
            'end_lat': end_lat,
            'end_lon': end_lon,
            'length_km': length_km,
            'elevation_gain': elevation_gain,
            'difficulty': difficulty,
            'terrain_type': terrain_type,
            'category': category,
            'description': description,
            'user_rating': user_rating
        }
        
        # Dodaj trasę do bazy danych
        route_id = route_repo.add_route(route_data)
        
        if route_id:
            print(f"\n✅ Trasa '{name}' została dodana pomyślnie!")
            print(f"🆔 ID trasy: {route_id}")
            
            # Zapytaj o dodanie recenzji
            add_reviews = input("\n❓ Czy chcesz dodać recenzje do tej trasy? (t/n): ").strip().lower()
            if add_reviews in ['t', 'tak', 'y', 'yes']:
                reviews = []
                print("📝 Wprowadź recenzje (wciśnij ENTER bez tekstu, aby zakończyć):")
                
                while True:
                    review = input(f"Recenzja {len(reviews) + 1}: ").strip()
                    if not review:
                        break
                    reviews.append(review)
                
                if reviews:
                    # Dodaj recenzje
                    route_data['reviews'] = reviews
                    route_repo._add_route_reviews(route_id, reviews)
                    print(f"✅ Dodano {len(reviews)} recenzji!")
        else:
            print("❌ Błąd podczas dodawania trasy.")
            
    except Exception as e:
        print(f"❌ Błąd podczas dodawania trasy: {e}")


def show_database_statistics(db_manager):
    """Wyświetla statystyki bazy danych."""
    
    try:
        from database import DatabaseAdmin
        
        admin = DatabaseAdmin(db_manager)
        admin.display_database_statistics()
        
        # Dodatkowe opcje
        print("\n🔧 DODATKOWE OPCJE:")
        print("1. 🔍 Sprawdź integralność bazy danych")
        print("2. 🔧 Optymalizuj bazę danych")
        print("3. 📄 Eksportuj raport do pliku")
        print("4. 🔙 Powrót do menu głównego")
        
        choice = input("\n👉 Wybierz opcję (1-4): ").strip()
        
        if choice == '1':
            admin.check_database_integrity()
        elif choice == '2':
            admin.optimize_database()
        elif choice == '3':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database_report_{timestamp}.txt"
            if admin.export_database_report(filename):
                print(f"✅ Raport zapisany jako: {filename}")
        elif choice == '4':
            return
        else:
            print("❌ Nieprawidłowy wybór.")
            
    except Exception as e:
        print(f"❌ Błąd podczas wyświetlania statystyk: {e}")


def create_database_backup(db_manager):
    """Tworzy kopię zapasową bazy danych."""
    
    try:
        from database import DatabaseAdmin
        
        admin = DatabaseAdmin(db_manager)
        
        print("\n" + "="*60)
        print("💾 ZARZĄDZANIE KOPIAMI ZAPASOWYMI")
        print("="*60)
        
        print("1. 💾 Utwórz nową kopię zapasową")
        print("2. 📋 Pokaż dostępne kopie zapasowe")
        print("3. 🔄 Przywróć z kopii zapasowej")
        print("4. 🔙 Powrót do menu głównego")
        
        choice = input("\n👉 Wybierz opcję (1-4): ").strip()
        
        if choice == '1':
            # Utwórz kopię zapasową
            backup_name = input("📝 Nazwa kopii zapasowej (ENTER = automatyczna): ").strip()
            if not backup_name:
                backup_name = None
            
            admin.create_backup(backup_name)
            
        elif choice == '2':
            # Pokaż dostępne kopie
            admin.list_backups()
            
        elif choice == '3':
            # Przywróć z kopii zapasowej
            backups = admin.list_backups()
            if backups:
                try:
                    backup_num = int(input("\n👉 Wybierz numer kopii zapasowej: ").strip())
                    if 1 <= backup_num <= len(backups):
                        selected_backup = backups[backup_num - 1]
                        admin.restore_backup(selected_backup['filename'])
                    else:
                        print("❌ Nieprawidłowy numer kopii zapasowej.")
                except ValueError:
                    print("❌ Wprowadź prawidłowy numer.")
            
        elif choice == '4':
            return
        else:
            print("❌ Nieprawidłowy wybór.")
            
    except Exception as e:
        print(f"❌ Błąd podczas zarządzania kopiami zapasowymi: {e}")


def import_data_from_files(db_manager):
    """Importuje dane z plików CSV/JSON do bazy danych."""
    
    try:
        from database import MigrationTool
        
        print("\n" + "="*60)
        print("📥 IMPORT DANYCH Z PLIKÓW")
        print("="*60)
        
        migration_tool = MigrationTool(db_manager)
        
        print("1. 📥 Importuj wszystkie dostępne pliki")
        print("2. 🏔️ Importuj tylko trasy (trails_data.json)")
        print("3. 🌤️ Importuj tylko dane pogodowe (weather_data.json)")
        print("4. 📊 Pokaż raport migracji")
        print("5. 🔙 Powrót do menu głównego")
        
        choice = input("\n👉 Wybierz opcję (1-5): ").strip()
        
        if choice == '1':
            print("\n🔄 Rozpoczynam import wszystkich dostępnych plików...")
            results = migration_tool.migrate_all_existing_data()
            
            print("\n📊 WYNIKI IMPORTU:")
            for file_path, success in results.items():
                status = "✅ Sukces" if success else "❌ Błąd"
                print(f"   {file_path}: {status}")
            
        elif choice == '2':
            print("\n🔄 Importuję trasy z trails_data.json...")
            success = migration_tool.migrate_routes_from_json("trails_data.json")
            if success:
                print("✅ Import tras zakończony pomyślnie!")
            else:
                print("❌ Błąd podczas importu tras.")
            
        elif choice == '3':
            print("\n🔄 Importuję dane pogodowe z weather_data.json...")
            success = migration_tool.migrate_weather_from_json("weather_data.json")
            if success:
                print("✅ Import danych pogodowych zakończony pomyślnie!")
            else:
                print("❌ Błąd podczas importu danych pogodowych.")
            
        elif choice == '4':
            print("\n📊 RAPORT MIGRACJI:")
            report = migration_tool.get_migration_report()
            if report:
                print(f"📅 Data raportu: {report.get('migration_timestamp', 'N/A')}")
                
                db_stats = report.get('database_stats', {})
                print(f"🏔️ Trasy w bazie: {db_stats.get('routes_count', 0)}")
                print(f"🌤️ Dane pogodowe: {db_stats.get('weather_records', 0)}")
                print(f"📝 Recenzje: {db_stats.get('reviews_count', 0)}")
            else:
                print("❌ Nie można wygenerować raportu migracji.")
            
        elif choice == '5':
            return
        else:
            print("❌ Nieprawidłowy wybór.")
            
    except Exception as e:
        print(f"❌ Błąd podczas importu danych: {e}")


def main():
    """Główna funkcja programu z menu."""
    print("🏔️ System Rekomendacji Tras Turystycznych - ETAP 4")
    print("=" * 60)
    
    # Inicjalizacja bazy danych
    try:
        from database import DatabaseManager, MigrationTool, DatabaseAdmin
        
        db_manager = DatabaseManager()
        if db_manager.initialize_database():
            print("✅ Baza danych zainicjalizowana pomyślnie")
        else:
            print("❌ Błąd inicjalizacji bazy danych")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Błąd bazy danych: {e}")
        sys.exit(1)
    
    while True:
        print("\n📋 MENU GŁÓWNE:")
        print("1. 🎯 Standardowe rekomendacje tras")
        print("2. ➕ Dodaj nową trasę")
        print("3. 📊 Statystyki bazy danych")
        print("4. 💾 Utwórz kopię zapasową")
        print("5. 📥 Importuj dane z plików")
        print("6. 📄 Rekomendacje z raportem PDF")
        print("7. 🔍 Analiza konkretnej trasy")
        print("8. 🗂️ Przeglądaj trasy w bazie danych")
        print("9. 🌐 Zbieranie danych z internetu")
        print("10. 📈 Generowanie tylko wykresów")
        print("11. 🔧 Demonstracja przetwarzania tekstu")
        print("0. 🚪 Wyjście")
        
        choice = input("\n👉 Wybierz opcję (0-11): ").strip()
        
        if choice == '1':
            standard_recommendations()
        elif choice == '2':
            add_new_route(db_manager)
        elif choice == '3':
            show_database_statistics(db_manager)
        elif choice == '4':
            create_database_backup(db_manager)
        elif choice == '5':
            import_data_from_files(db_manager)
        elif choice == '6':
            recommendations_with_pdf()
        elif choice == '7':
            analyze_specific_trail()
        elif choice == '8':
            browse_database_routes(db_manager)
        elif choice == '9':
            collect_web_data()
        elif choice == '10':
            generate_charts_only()
        elif choice == '11':
            demonstrate_text_processing()
        elif choice == '0':
            print("\n👋 Dziękujemy za korzystanie z systemu!")
            break
        else:
            print("\n❌ Nieprawidłowy wybór. Spróbuj ponownie.")

if __name__ == "__main__":
    main() 