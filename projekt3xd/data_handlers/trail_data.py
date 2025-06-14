import json
from functools import reduce
from typing import List, Dict, Any
import os
import sys
from datetime import datetime
import inspect

# Dodaj katalog projektu do ścieżki Pythona
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Dodaj ścieżkę do nowych modułów
currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, currentdir)

from api.trails_api import TrailsAPI
from api.weather_api import WeatherAPI
from config import CITY_COORDINATES

try:
    from analyzers.text_processor import TextProcessor
    from analyzers.review_analyzer import ReviewAnalyzer
    from extractors.web_data_collector import WebDataCollector
except ImportError as e:
    print(f"Ostrzeżenie: Nie można zaimportować nowych modułów: {e}")
    # Definicje zastępcze
    class TextProcessor:
        def enhance_trail_data(self, trail_data):
            return trail_data
    
    class ReviewAnalyzer:
        def enhance_trail_with_reviews(self, trail_data, reviews):
            return trail_data
    
    class WebDataCollector:
        def collect_sample_data(self):
            return []

class TrailDataHandler:
    def __init__(self):
        self.api = TrailsAPI()
        self.weather_api = WeatherAPI()
        self.data_file = "api/trails_data.json"
        
        # Inicjalizuj nowe moduły analizy
        self.text_processor = TextProcessor()
        self.review_analyzer = ReviewAnalyzer()
        self.web_collector = WebDataCollector()
        
        print("Pobieranie danych o szlakach z API...")
        self._update_trails_data()
        self.trails_data = self._load_trails_data()

    def _load_trails_data(self) -> List[Dict[str, Any]]:
        """Load trails data from JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd podczas wczytywania danych o trasach: {e}")
            return []

    def _update_trails_data(self):
        """Update trails data by fetching from API and saving to file."""
        print("Aktualizacja danych o szlakach...")
        all_trails = []
        
        # Get trails for all regions
        for region in CITY_COORDINATES.keys():
            print(f"\nPobieranie szlaków dla regionu: {region}")
            try:
                trails = self.api.get_hiking_trails(region)
                if trails:
                    all_trails.extend(trails)
                    print(f"Znaleziono {len(trails)} szlaków dla {region}")
            except Exception as e:
                print(f"Błąd podczas pobierania szlaków dla {region}: {e}")

        print(f"\nŁącznie znaleziono {len(all_trails)} szlaków")

        # Save to trails_data.json
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(all_trails, f, ensure_ascii=False, indent=2)
            print("Dane o szlakach zostały zapisane do pliku trails_data.json")
        except Exception as e:
            print(f"Błąd podczas zapisywania danych o szlakach: {e}")

    def _validate_trail(self, trail: Any) -> Dict[str, Any]:
        """Waliduje i formatuje dane szlaku."""
        if not isinstance(trail, dict):
            return None
            
        # Required fields with default values
        default_trail = {
            "id": "unknown",
            "name": "Unknown Trail",
            "region": "unknown",
            "length_km": 0.0,
            "difficulty": 1,
            "terrain_type": "mixed",
            "tags": []
        }
        
        # Update default values with actual data if valid
        if isinstance(trail, dict):
            for key in default_trail:
                if key in trail and trail[key] is not None:
                    default_trail[key] = trail[key]
                    
            # Ensure numeric fields are correct type
            try:
                default_trail["length_km"] = float(default_trail["length_km"])
                default_trail["difficulty"] = int(default_trail["difficulty"])
            except (ValueError, TypeError):
                default_trail["length_km"] = 0.0
                default_trail["difficulty"] = 1
                
        return default_trail

    def get_trails(self) -> List[Dict[str, Any]]:
        """Get all available trails."""
        all_trails = []
        for city in CITY_COORDINATES.keys():
            city_trails = self.get_trails_for_city(city)
            all_trails.extend(trail for trail in city_trails if trail is not None)
        return self._remove_duplicates(all_trails)
    
    def _remove_duplicates(self, trails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Usuwa duplikaty tras na podstawie nazwy, długości i regionu."""
        seen = set()
        unique_trails = []
        
        for trail in trails:
            # Utwórz klucz unikalności na podstawie nazwy, długości i regionu
            key = (
                trail.get('name', '').lower().strip(),
                trail.get('length_km', 0),
                trail.get('region', '').lower().strip()
            )
            
            if key not in seen:
                seen.add(key)
                unique_trails.append(trail)
        
        if len(trails) != len(unique_trails):
            print(f"Usunięto {len(trails) - len(unique_trails)} duplikatów tras")
        
        return unique_trails

    def get_trails_for_city(self, city: str) -> List[Dict[str, Any]]:
        """Get trails for a specific city from the data file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                all_trails = json.load(f)
                city_trails = [trail for trail in all_trails if trail.get("region", "").lower() == city.lower()]
                unique_trails = self._remove_duplicates(city_trails)
                print(f"Znaleziono {len(unique_trails)} unikalnych szlaków dla miasta {city}")
                return unique_trails
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych o szlakach: {e}")
            return []

    def get_trail_by_id(self, trail_id: str) -> Dict[str, Any]:
        """Get a specific trail by its ID from the data file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                all_trails = json.load(f)
                for trail in all_trails:
                    if trail.get("id") == trail_id:
                        return trail
                return None
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych o szlakach: {e}")
            return None

    def get_trails_by_difficulty(self, difficulty: int) -> List[Dict[str, Any]]:
        """Get trails with specific difficulty level from the data file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                all_trails = json.load(f)
                difficulty_trails = [trail for trail in all_trails if trail.get("difficulty") == difficulty]
                print(f"Znaleziono {len(difficulty_trails)} szlaków o trudności {difficulty}")
                return difficulty_trails
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych o szlakach: {e}")
            return []

    def get_trails_by_terrain(self, terrain_type: str) -> List[Dict[str, Any]]:
        """Get trails with specific terrain type from the data file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                all_trails = json.load(f)
                terrain_trails = [trail for trail in all_trails if trail.get("terrain_type", "").lower() == terrain_type.lower()]
                print(f"Znaleziono {len(terrain_trails)} szlaków o typie terenu {terrain_type}")
                return terrain_trails
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Błąd podczas wczytywania danych o szlakach: {e}")
            return []

    def filter_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Filter trails by region."""
        return [trail for trail in self.get_trails() 
                if isinstance(trail, dict) and 
                trail.get('region', '').lower() == region.lower()]

    def filter_by_length(self, min_length: float, max_length: float) -> List[Dict[str, Any]]:
        """Filter trails by length range."""
        return [trail for trail in self.get_trails()
                if isinstance(trail, dict) and
                min_length <= trail.get('length_km', 0) <= max_length]

    def filter_by_difficulty(self, difficulty: int) -> List[Dict[str, Any]]:
        """Filter trails by difficulty level."""
        return [trail for trail in self.get_trails()
                if isinstance(trail, dict) and
                trail.get('difficulty') == difficulty]

    def get_average_length(self) -> float:
        """Calculate average length of all trails."""
        trails = [trail for trail in self.get_trails() if isinstance(trail, dict)]
        if not trails:
            return 0
        return sum(trail.get('length_km', 0) for trail in trails) / len(trails)

    def save_trails(self, filename: str):
        """Save all trails to a JSON file."""
        trails = [trail for trail in self.get_trails() if isinstance(trail, dict)]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trails, f, ensure_ascii=False, indent=2)

    def get_trails_by_weather_conditions(self, city: str, date: str, 
                                       max_precipitation: float = None,
                                       min_temperature: float = None,
                                       max_temperature: float = None) -> List[Dict[str, Any]]:
        """Get trails filtered by weather conditions."""
        try:
            # Get weather forecast for the specified date
            weather = self.weather_api.get_weather_forecast(city, date)
            if not weather:
                print(f"Brak danych pogodowych dla {city} na dzień {date}")
                return []
            
            # Calculate hiking comfort index
            from utils.weather_utils import WeatherUtils
            comfort_index = WeatherUtils.calculate_hiking_comfort(weather)

            # Get all trails for the city
            trails = self.get_trails_for_city(city)
            if not trails:
                return []

            # Filter trails based on weather conditions
            filtered_trails = []
            for trail in trails:
                # Check precipitation
                if max_precipitation is not None and weather["precipitation"] > max_precipitation:
                    continue
                
                # Check temperature
                if min_temperature is not None and weather["temperature_avg"] < min_temperature:
                    continue
                if max_temperature is not None and weather["temperature_avg"] > max_temperature:
                    continue
                
                # Add comfort index to trail data
                trail_with_comfort = trail.copy()
                trail_with_comfort['comfort_index'] = WeatherUtils.calculate_hiking_comfort(weather)
                filtered_trails.append(trail_with_comfort)

            print(f"Znaleziono {len(filtered_trails)} szlaków spełniających kryteria pogodowe")
            return filtered_trails

        except Exception as e:
            print(f"Błąd podczas filtrowania tras według warunków pogodowych: {e}")
            return []

    def get_trails_by_all_criteria(self, city: str, date: str,
                                 difficulty: int = None,
                                 terrain_type: str = None,
                                 max_precipitation: float = None,
                                 min_temperature: float = None,
                                 max_temperature: float = None,
                                 min_length: float = None,
                                 max_length: float = None,
                                 min_sunshine: float = None) -> List[Dict[str, Any]]:
        """Get trails filtered by all criteria."""
        try:
            # Filter trails by city
            city_trails = [trail for trail in self.trails_data if trail.get('region', '').lower() == city.lower()]
            print(f"Znaleziono {len(city_trails)} szlaków dla miasta {city}")

            if not city_trails:
                print(f"Nie znaleziono szlaków dla miasta {city}")
                return []

            # Get weather data
            print(f"Pobieranie danych pogodowych dla {city} na dzień {date}...")
            weather = self.weather_api.get_weather_forecast(city, date)
            if not weather:
                print(f"Brak danych pogodowych dla {city} na dzień {date}")
                return []

            # Filter trails by all criteria
            filtered_trails = []
            for trail in city_trails:
                # Check difficulty
                if difficulty is not None and trail.get('difficulty') != difficulty:
                    continue

                # Check terrain type
                if terrain_type and trail.get('terrain_type', '').lower() != terrain_type.lower():
                    continue

                # Check length
                if min_length is not None and trail.get('length_km', 0) < min_length:
                    continue
                if max_length is not None and trail.get('length_km', 0) > max_length:
                    continue

                # Check weather conditions
                if max_precipitation is not None and weather.get('precipitation', 0) > max_precipitation:
                    continue
                if min_temperature is not None and weather.get('temperature_min', 0) < min_temperature:
                    continue
                if max_temperature is not None and weather.get('temperature_max', 0) > max_temperature:
                    continue
                if min_sunshine is not None and weather.get('sunshine_hours', 0) < min_sunshine:
                    continue

                filtered_trails.append(trail)

            if not filtered_trails:
                print("Nie znaleziono tras spełniających podane kryteria")
                return []

            return filtered_trails

        except Exception as e:
            print(f"Błąd podczas filtrowania tras: {e}")
            return []

    def enhance_trail_with_analysis(self, trail_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rozszerza dane trasy o analizę tekstu i recenzji.
        
        Args:
            trail_data: Podstawowe dane trasy
            
        Returns:
            Rozszerzone dane trasy z analizą
        """
        enhanced_trail = trail_data.copy()
        
        # Przetwarzanie opisu trasy za pomocą TextProcessor
        if trail_data.get('description'):
            enhanced_trail = self.text_processor.enhance_trail_data(enhanced_trail)
        
        # Dodaj przykładowe recenzje jeśli ich brak
        if not enhanced_trail.get('reviews'):
            # Generuj przykładowe recenzje na podstawie nazwy i kategorii trasy
            enhanced_trail['reviews'] = self._generate_sample_reviews(enhanced_trail)
        
        # Analiza recenzji
        reviews = enhanced_trail.get('reviews', [])
        if reviews:
            enhanced_trail = self.review_analyzer.enhance_trail_with_reviews(enhanced_trail, reviews)
        
        return enhanced_trail
    
    def _generate_sample_reviews(self, trail_data: Dict[str, Any]) -> List[str]:
        """
        Generuje przykładowe recenzje dla tras, które ich nie mają.
        
        Args:
            trail_data: Dane trasy
            
        Returns:
            Lista przykładowych recenzji
        """
        trail_name = trail_data.get('name', 'trasa')
        difficulty = trail_data.get('difficulty', 2)
        length = trail_data.get('length_km', 10)
        category = trail_data.get('category', 'sportowa')
        terrain = trail_data.get('terrain_type', 'mixed')
        
        sample_reviews = []
        
        # Pozytywne recenzje (60% szans)
        positive_reviews = [
            f"Fantastyczna trasa! {trail_name} zachwyca na każdym kroku. Polecam wszystkim miłośnikom przyrody. 5/5",
            f"Wspaniałe widoki i dobrze oznakowana trasa. Spędziłem tu cudowny dzień. Zdecydowanie wrócę! 5/5",
            f"Jedna z najpiękniejszych tras jakie przeszedłem. {trail_name} to prawdziwa perła. 4/5",
            f"Świetna organizacja, czyste szlaki, piękne krajobrazy. Bardzo polecam! 5/5",
            f"Trasa idealna na weekend z rodziną. Dzieci były zachwycone! 4/5",
            f"Doskonałe miejsce na aktywny wypoczynek. Powietrze czyste, widoki przepiękne. 5/5"
        ]
        
        # Neutralne recenzje (25% szans)
        neutral_reviews = [
            f"Trasa w porządku, nic szczególnego ale da się przejść. Oznakowanie mogłoby być lepsze. 3/5",
            f"Przeciętna trasa, widoki średnie. Dla początkujących może być ok. 3/5",
            f"Nie najgorsza trasa, ale są lepsze w okolicy. Parking płatny. 3/5",
            f"Standardowa trasa turystyczna. Nic co by mnie zaskoczyło pozytywnie. 3/5",
            f"Trasa jak trasa. Przeszedłem, ale nie zostanie mi w pamięci. 3/5"
        ]
        
        # Negatywne recenzje (15% szans)
        negative_reviews = [
            f"Rozczarowanie. Trasa przeceniona, widoki słabe. Nie polecam. 2/5",
            f"Źle oznakowana trasa, zgubiłem się kilka razy. Frustrujące doświadczenie. 2/5",
            f"Za dużo ludzi, hałas, śmieci na szlaku. Nie wrócę tu więcej. 2/5",
            f"Trasa w złym stanie, błoto wszędzie. Lepiej wybrać inną trasę. 1/5",
            f"Przepłacone i przereklamowane. Oczekiwałem więcej. 2/5"
        ]
        
        # Recenzje specyficzne dla trudności
        if difficulty == 1:
            sample_reviews.extend([
                "Łatwa trasa, idealna dla początkujących. Przeszedłem z dziećmi bez problemu. 4/5",
                "Spokojna trasa, można iść w zwykłych butach. Polecam seniorom. 4/5"
            ])
        elif difficulty == 2:
            sample_reviews.extend([
                "Średnia trudność, trzeba mieć podstawową kondycję. Warto się wybrać. 4/5",
                "Trasa wymagająca ale do przejścia. Kilka stromych odcinków. 3/5"
            ])
        else:
            sample_reviews.extend([
                "Bardzo trudna trasa! Tylko dla doświadczonych. Ale widoki niesamowite! 4/5",
                "Ekstremalna trasa, wymaga doskonałej kondycji. Nie dla każdego. 3/5"
            ])
        
        # Recenzje specyficzne dla długości
        if length < 5:
            sample_reviews.append("Krótka ale przyjemna trasa. Idealna na popołudniowy spacer. 4/5")
        elif length > 15:
            sample_reviews.append("Długa trasa na cały dzień. Zabierz dużo wody i jedzenia! 4/5")
        
        # Recenzje specyficzne dla terenu
        if terrain == 'górski':
            sample_reviews.extend([
                "Górska trasa z pięknymi widokami na szczyty. Uwaga na pogodę! 4/5",
                "Strome podejścia ale warto! Panorama z góry zapiera dech. 5/5"
            ])
        elif terrain == 'leśny':
            sample_reviews.extend([
                "Spokojna trasa przez las. Dużo cienia, przyjemnie w upały. 4/5",
                "Piękny las, świeże powietrze. Widziałem sarny! 4/5"
            ])
        elif terrain == 'miejski':
            sample_reviews.extend([
                "Miejska trasa, dobre połączenia komunikacyjne. Wygodnie. 3/5",
                "Trasa przez miasto, ciekawe zabytki po drodze. 3/5"
            ])
        
        # Recenzje sezonowe
        seasonal_reviews = [
            "Wiosną najpiękniej - wszystko kwitnie! Polecam maj. 5/5",
            "Latem może być gorąco, ale widoki rekompensują. Zabierz kapelusz. 4/5",
            "Jesienią kolory liści są niesamowite! Złota polska jesień. 5/5",
            "Zimą trasa trudniejsza ale magiczna. Raki na buty obowiązkowo. 4/5"
        ]
        
        # Losowo wybierz 5-8 recenzji z różnych kategorii
        import random
        
        # Dodaj pozytywne (60% szans)
        sample_reviews.extend(random.sample(positive_reviews, min(3, len(positive_reviews))))
        
        # Dodaj neutralne (25% szans)
        if random.random() < 0.6:  # 60% szans na dodanie neutralnej
            sample_reviews.extend(random.sample(neutral_reviews, min(2, len(neutral_reviews))))
        
        # Dodaj negatywne (15% szans)
        if random.random() < 0.4:  # 40% szans na dodanie negatywnej
            sample_reviews.extend(random.sample(negative_reviews, min(1, len(negative_reviews))))
        
        # Dodaj sezonową
        sample_reviews.append(random.choice(seasonal_reviews))
        
        # Ogranicz do 6-8 recenzji
        return random.sample(sample_reviews, min(8, len(sample_reviews)))

    def get_enhanced_trails(self) -> List[Dict[str, Any]]:
        """
        Zwraca wszystkie trasy z rozszerzoną analizą.
        
        Returns:
            Lista rozszerzonych danych tras
        """
        all_trails = []
        base_trails = self.get_trails()
        
        for trail in base_trails:
            enhanced_trail = self.enhance_trail_with_analysis(trail)
            all_trails.append(enhanced_trail)
        
        return all_trails

    def get_enhanced_trails_for_city(self, city: str) -> List[Dict[str, Any]]:
        """
        Zwraca rozszerzone dane tras dla konkretnego miasta.
        
        Args:
            city: Nazwa miasta
            
        Returns:
            Lista rozszerzonych tras dla miasta
        """
        city_trails = self.get_trails_for_city(city)
        enhanced_trails = []
        
        for trail in city_trails:
            enhanced_trail = self.enhance_trail_with_analysis(trail)
            enhanced_trails.append(enhanced_trail)
        
        return enhanced_trails

    def collect_additional_trail_data(self, max_trails: int = 10) -> List[Dict[str, Any]]:
        """
        Zbiera dodatkowe dane o trasach z web collectora.
        
        Args:
            max_trails: Maksymalna liczba tras do zebrania
            
        Returns:
            Lista dodatkowych tras
        """
        try:
            additional_trails = self.web_collector.collect_sample_data()
            
            # Przetwórz dodatkowe trasy przez analizery
            processed_trails = []
            for trail in additional_trails[:max_trails]:
                enhanced_trail = self.enhance_trail_with_analysis(trail)
                processed_trails.append(enhanced_trail)
            
            return processed_trails
            
        except Exception as e:
            print(f"Błąd podczas zbierania dodatkowych danych o trasach: {e}")
            return [] 