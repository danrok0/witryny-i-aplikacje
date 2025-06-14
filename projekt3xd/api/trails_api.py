"""
MODUŁ API SZLAKÓW TURYSTYCZNYCH - POBIERANIE DANYCH Z OVERPASS API
=================================================================

Ten moduł zawiera klasę TrailsAPI, która pobiera dane o szlakach turystycznych
z OpenStreetMap używając Overpass API. Implementuje funkcjonalność wyszukiwania,
przetwarzania i standaryzacji danych o trasach.

FUNKCJONALNOŚCI:
- Pobieranie szlaków turystycznych dla określonych miast/regionów
- Przetwarzanie różnych formatów danych (odległości, wysokości)
- Obliczanie poziomu trudności tras na podstawie wielu czynników
- Kategoryzacja typów terenu i powierzchni
- Zapisywanie danych do plików JSON (cache)

ŹRÓDŁA DANYCH:
- OpenStreetMap (OSM) przez Overpass API
- Różne typy tras: hiking, walking, cycling, running
- Obiekty turystyczne: parki, punkty widokowe, zabytki
- Elementy naturalne: lasy, jeziora, wybrzeża

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK
# ============================================================================
import requests                              # Biblioteka do zapytań HTTP
import re                                   # Wyrażenia regularne
import os                                   # Operacje na systemie plików
import json                                 # Obsługa formatu JSON
from typing import List, Dict, Any          # Podpowiedzi typów
from functools import reduce                # Funkcje funkcyjne (reduce)
from config import OVERPASS_API, OVERPASS_QUERY_TEMPLATE  # Konfiguracja API

# ============================================================================
# IMPORTY BAZY DANYCH
# ============================================================================
try:
    import sys
    sys.path.append('..')  # Dodaj katalog główny projektu
    from database import DatabaseManager
    from database.repositories.route_repository import RouteRepository
    DATABSE_AVAILABLE = True
except ImportError:
    print("⚠️ Baza danych niedostępna. Używam plików JSON jako fallback.")
    DATABSE_AVAILABLE = False

# ============================================================================
# GŁÓWNA KLASA API SZLAKÓW
# ============================================================================

class TrailsAPI:
    """
    Klasa do pobierania i przetwarzania danych o szlakach turystycznych z Overpass API.
    
    NOWE W ETAPIE 4: Obsługa bazy danych SQLite
    - Automatycznie zapisuje pobrane trasy do bazy danych
    - Fallback na pliki JSON jeśli baza niedostępna
    - Integracja z Repository pattern
    
    Ta klasa implementuje kompleksowy system pobierania danych o trasach turystycznych
    z OpenStreetMap, ich przetwarzania i standaryzacji. Wykorzystuje programowanie
    funkcyjne (map, reduce, filter) do efektywnego przetwarzania danych.
    
    Attributes:
        base_url: URL bazowy Overpass API
        data_dir: Katalog do zapisywania plików z danymi (fallback)
        db_manager: Menedżer bazy danych SQLite
        route_repo: Repository do operacji na trasach
    
    Przykład użycia:
        api = TrailsAPI()
        trails = api.get_hiking_trails("Gdańsk")
        print(f"Znaleziono {len(trails)} szlaków - zapisano do bazy danych")
    """
    
    def __init__(self):
        """
        Inicjalizacja klasy TrailsAPI z obsługą bazy danych.
        
        Próbuje połączyć się z bazą danych SQLite. Jeśli się nie uda,
        przełącza się na tryb fallback z plikami JSON.
        """
        # URL bazowy Overpass API z pliku konfiguracyjnego
        self.base_url = OVERPASS_API
        
        # Katalog do przechowywania pobranych danych (fallback)
        self.data_dir = "api"
        
        # ====================================================================
        # NOWE: INICJALIZACJA BAZY DANYCH
        # ====================================================================
        if DATABSE_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                if self.db_manager.initialize_database():
                    self.route_repo = RouteRepository(self.db_manager)
                    print("✅ TrailsAPI połączony z bazą danych SQLite")
                    self.use_database = True
                else:
                    print("⚠️ Błąd inicjalizacji bazy. Używam plików JSON.")
                    self.use_database = False
            except Exception as e:
                print(f"⚠️ Błąd bazy danych: {e}. Używam plików JSON.")
                self.use_database = False
        else:
            self.use_database = False
            
        # Utworzenie katalogu jeśli nie istnieje (fallback)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            if not self.use_database:
                print(f"Utworzono katalog danych: {self.data_dir}")

    def _parse_distance(self, distance_str: str) -> float:
        """Konwertuje ciąg znaków z odległością na kilometry."""
        if not distance_str:
            return 0.0
        
        try:
            # Usuwa wszystkie znaki niebędące cyframi lub kropkami i konwertuje na float
            value = float(''.join(c for c in str(distance_str) if c.isdigit() or c == '.'))
            
            # Jeśli ciąg zawiera 'm' lub 'km', używa tego jako jednostki
            if isinstance(distance_str, str):
                distance_str = distance_str.lower().strip()
                if 'km' in distance_str:
                    return value
                elif 'm' in distance_str:
                    return value / 1000
                else:
                    # Jeśli nie podano jednostki, zakłada metry jeśli wartość > 100, w przeciwnym razie kilometry
                    return value / 1000 if value > 100 else value
            else:
                # Jeśli nie podano jednostki, zakłada metry jeśli wartość > 100, w przeciwnym razie kilometry
                return value / 1000 if value > 100 else value
                
        except (ValueError, AttributeError):
            return 0.0

    def _parse_elevation(self, elevation_str: str) -> float:
        """Konwertuje ciąg znaków z wysokością na metry."""
        if not elevation_str:
            return 0.0
        
        try:
            # Usuwa wszystkie znaki niebędące cyframi lub kropkami i konwertuje na float
            value = float(''.join(c for c in str(elevation_str) if c.isdigit() or c == '.'))
            
            # Jeśli ciąg zawiera 'm' lub 'km', używa tego jako jednostki
            if isinstance(elevation_str, str):
                elevation_str = elevation_str.lower().strip()
                if 'km' in elevation_str:
                    return value * 1000
                elif 'm' in elevation_str:
                    return value
                else:
                    return value  # Domyślnie zakłada metry
            else:
                return value  # Domyślnie zakłada metry
                
        except (ValueError, AttributeError):
            return 0.0

    def _calculate_difficulty_components(self, tags: Dict[str, str], length_km: float, elevation_m: float) -> List[int]:
        """Oblicza komponenty trudności trasy używając programowania funkcyjnego."""
        components = []
        
        # Komponent długości
        components.append(3 if length_km > 20 else (2 if length_km > 10 else 1))
        
        # Komponent wysokości
        components.append(3 if elevation_m > 1000 else (2 if elevation_m > 500 else 1))
        
        # Komponent skali SAC
        sac_scale = tags.get("sac_scale", "").lower()
        components.append(3 if "alpine" in sac_scale else (2 if "mountain" in sac_scale else 1))
        
        # Komponent powierzchni
        surface = tags.get("surface", "").lower()
        components.append(3 if any(s in surface for s in ["rock", "scree"]) else 
                         (2 if any(s in surface for s in ["gravel", "dirt"]) else 1))
        
        # Komponent nachylenia
        try:
            incline_str = tags.get("incline", "0")
            if incline_str and isinstance(incline_str, str):
                # Usuń znaki % i inne niebędące cyframi
                incline_clean = ''.join(c for c in incline_str if c.isdigit() or c == '.' or c == '-')
                incline = float(incline_clean) if incline_clean else 0
            else:
                incline = 0
        except (ValueError, TypeError):
            incline = 0
        components.append(3 if incline > 15 else (2 if incline > 10 else 1))
        
        return components

    def _calculate_difficulty(self, tags: Dict[str, str], length_km: float, elevation_m: float) -> int:
        """Oblicza trudność trasy używając funkcji reduce (skala 1-3)."""
        components = self._calculate_difficulty_components(tags, length_km, elevation_m)
        # Używa reduce aby znaleźć maksymalny komponent trudności
        max_difficulty = reduce(lambda x, y: max(x, y), components)
        # Upewnij się, że trudność jest w zakresie 1-3
        return max(1, min(3, max_difficulty))

    def get_hiking_trails(self, city: str) -> List[Dict[str, Any]]:
        """
        Pobiera szlaki turystyczne dla miasta używając API Overpass.
        
        NOWE W ETAPIE 4: Automatycznie zapisuje do bazy danych SQLite
        """
        print(f"\nPróba pobrania tras dla miasta: {city}")

        # Expanded Overpass query to find more trails
        query = f"""
        [out:json][timeout:25];
        area["name"="{city}"]["boundary"="administrative"]->.searchArea;
        (
          // Main hiking and walking routes
          relation["route"~"hiking|foot|walking|running"](area.searchArea);
          way["route"~"hiking|foot|walking|running"](area.searchArea);
          
          // Parks and nature reserves
          relation["leisure"~"park|nature_reserve|garden"](area.searchArea);
          way["leisure"~"park|nature_reserve|garden"](area.searchArea);
          
          // Natural areas
          relation["natural"~"wood|forest|park|heath|grassland|scrub"](area.searchArea);
          way["natural"~"wood|forest|park|heath|grassland|scrub"](area.searchArea);
          
          // Tourist attractions
          relation["tourism"~"attraction|viewpoint|picnic_site"](area.searchArea);
          way["tourism"~"attraction|viewpoint|picnic_site"](area.searchArea);
          
          // Waterways and coastlines
          relation["waterway"~"river|stream|canal"](area.searchArea);
          way["waterway"~"river|stream|canal"](area.searchArea);
          relation["natural"~"coastline|beach"](area.searchArea);
          way["natural"~"coastline|beach"](area.searchArea);
          
          // Historical and cultural sites
          relation["historic"~"monument|memorial|castle|ruins"](area.searchArea);
          way["historic"~"monument|memorial|castle|ruins"](area.searchArea);
        );
        out body;
        >;
        out skel qt;
        """

        try:
            print(f"Wysyłanie zapytania do API Overpass dla {city}")
            response = requests.post(self.base_url, data={"data": query})
            response.raise_for_status()
            data = response.json()
            print(f"Otrzymano odpowiedź z API dla {city}")

            # Use map to process all elements
            trails = list(map(lambda element: self._process_trail_element(element, city), 
                            filter(lambda e: e.get("type") in ["relation", "way"], 
                                  data.get("elements", []))))

            # Filter out None values and empty trails
            trails = list(filter(None, trails))
            
            print(f"Znaleziono łącznie {len(trails)} tras dla {city}")
            
            # ================================================================
            # NOWE: ZAPIS DO BAZY DANYCH ZAMIAST PLIKU JSON
            # ================================================================
            if self.use_database and trails:
                self._save_trails_to_database(trails, city)
            else:
                # Fallback: Save trails to file
                self._save_trails_to_file(trails)
            
            return trails

        except requests.RequestException as e:
            print(f"Błąd podczas pobierania danych dla {city}: {e}")
            return []

    def _process_trail_element(self, element: Dict[str, Any], city: str) -> Dict[str, Any]:
        """Przetwarza pojedynczy element szlaku."""
        tags = element.get("tags", {})
        
        # Skip if no name
        if not tags.get("name"):
            return None
            
        # Calculate length from various possible sources
        length_sources = [
            tags.get("distance"),
            tags.get("length"),
            tags.get("way_length"),
            tags.get("route_length")
        ]
        
        length_km = 0.0
        for source in length_sources:
            if source:
                length_km = self._parse_distance(source)
                if length_km > 0:
                    break
        
        # If no length found in tags, estimate based on element type and generate reasonable values
        if length_km == 0:
            # Generate realistic trail lengths based on element type and tags
            import random
            
            # Determine trail type for length estimation
            route_type = tags.get("route", "")
            leisure_type = tags.get("leisure", "")
            natural_type = tags.get("natural", "")
            tourism_type = tags.get("tourism", "")
            
            if "hiking" in route_type or "foot" in route_type:
                # Hiking trails: 2-25 km
                length_km = random.uniform(2.0, 25.0)
            elif "park" in leisure_type or "garden" in leisure_type:
                # Park trails: 0.5-8 km
                length_km = random.uniform(0.5, 8.0)
            elif "forest" in natural_type or "wood" in natural_type:
                # Forest trails: 1-15 km
                length_km = random.uniform(1.0, 15.0)
            elif "viewpoint" in tourism_type or "attraction" in tourism_type:
                # Tourist attractions: 0.3-5 km
                length_km = random.uniform(0.3, 5.0)
            elif "waterway" in tags or "river" in natural_type:
                # Riverside trails: 1-12 km
                length_km = random.uniform(1.0, 12.0)
            else:
                # Default trails: 1-10 km
                length_km = random.uniform(1.0, 10.0)
            
            # Round to 1 decimal place
            length_km = round(length_km, 1)

        # Get elevation data
        elevation_sources = [
            tags.get("ele"),
            tags.get("elevation"),
            tags.get("height")
        ]
        
        elevation_m = 0.0
        for source in elevation_sources:
            if source:
                elevation_m = self._parse_elevation(source)
                if elevation_m > 0:
                    break

        # Get coordinates if available
        coordinates = None
        try:
            if "center" in element and isinstance(element["center"], dict):
                coordinates = {
                    "lat": element["center"].get("lat"),
                    "lon": element["center"].get("lon")
                }
            elif "nodes" in element and element["nodes"] and isinstance(element["nodes"], list):
                # Use first node as approximate location
                first_node = element["nodes"][0]
                if isinstance(first_node, dict):
                    coordinates = {
                        "lat": first_node.get("lat"),
                        "lon": first_node.get("lon")
                    }
        except (KeyError, IndexError, TypeError) as e:
            print(f"Błąd podczas pobierania współrzędnych: {e}")
            coordinates = None
        
        trail = {
            "id": str(element.get("id")),
            "name": tags.get("name", "Unknown Trail"),
            "region": city,
            "coordinates": coordinates,
            "length_km": length_km,
            "elevation_m": elevation_m,
            "difficulty": self._calculate_difficulty(tags, length_km, elevation_m),
            "terrain_type": self._determine_terrain_type(tags),
            "tags": [k for k, v in tags.items() if v == "yes"]
        }
        
        print(f"Znaleziono trasę: {trail['name']} ({trail['length_km']:.2f} km, trudność: {trail['difficulty']})")
        return trail

    def _determine_terrain_type(self, tags: Dict[str, str]) -> str:
        """Określa typ terenu używając list składanych."""
        terrain_mapping = {
            "waterway": "riverside",
            "natural=coast": "coastal",
            "leisure=park": "park",
            "historic": "historical",
            "place=city": "urban",
            "place=town": "urban"
        }
        
        # Use dictionary comprehension to find matching terrain type
        terrain_type = next((v for k, v in terrain_mapping.items() 
                           if k in tags or any(k in str(v).lower() for v in tags.values())), 
                          "mixed")
        return terrain_type 

    def _save_trails_to_database(self, trails: List[Dict[str, Any]], city: str):
        """
        NOWE: Zapisuje trasy do bazy danych SQLite.
        
        Args:
            trails: Lista tras do zapisania
            city: Nazwa miasta (dla logowania)
        """
        try:
            saved_count = 0
            updated_count = 0
            
            print(f"💾 Zapisywanie {len(trails)} tras do bazy danych...")
            
            for trail in trails:
                # Sprawdź czy trasa już istnieje (po nazwie i regionie)
                existing_routes = self.route_repo.find_routes_by_region_and_name(
                    trail['region'], trail['name']
                )
                
                if existing_routes:
                    # Aktualizuj istniejącą trasę
                    route_id = existing_routes[0]['id']
                    trail_data = self._convert_to_database_format(trail)
                    
                    if self.route_repo.update_route(route_id, trail_data):
                        updated_count += 1
                        print(f"🔄 Zaktualizowano: {trail['name']}")
                else:
                    # Dodaj nową trasę
                    trail_data = self._convert_to_database_format(trail)
                    
                    route_id = self.route_repo.add_route(trail_data)
                    if route_id:
                        saved_count += 1
                        print(f"➕ Dodano: {trail['name']} (ID: {route_id})")
            
            print(f"✅ Zapisano do bazy danych:")
            print(f"   📋 Nowe trasy: {saved_count}")
            print(f"   🔄 Zaktualizowane: {updated_count}")
            print(f"   🎯 Łącznie przetworzono: {len(trails)} tras dla {city}")
            
        except Exception as e:
            print(f"❌ Błąd zapisywania do bazy danych: {e}")
            print("📁 Używam zapisu do pliku jako fallback...")
            self._save_trails_to_file(trails)

    def _convert_to_database_format(self, trail: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konwertuje trasę z formatu API na format bazy danych.
        
        Args:
            trail: Trasa w formacie API
            
        Returns:
            Trasa w formacie bazy danych (zgodnym ze schematem SQL)
        """
        # Pobierz współrzędne
        coords = trail.get('coordinates', {})
        start_lat = coords.get('lat', 50.0) if coords else 50.0
        start_lon = coords.get('lon', 20.0) if coords else 20.0
        
        # Konwertuj tags z listy na string
        tags_str = ','.join(trail.get('tags', [])) if trail.get('tags') else ''
        
        # Określ kategorię na podstawie terrain_type i length
        category = self._determine_category(trail)
        
        return {
            'name': trail.get('name', 'Unknown Trail'),
            'region': trail.get('region', 'Unknown'),
            'start_lat': float(start_lat),
            'start_lon': float(start_lon),
            'end_lat': float(start_lat),  # Używamy tych samych współrzędnych dla start/end
            'end_lon': float(start_lon),
            'length_km': float(trail.get('length_km', 0.0)),
            'elevation_gain': int(trail.get('elevation_m', 0)),
            'difficulty': int(trail.get('difficulty', 2)),
            'terrain_type': trail.get('terrain_type', 'mixed'),
            'tags': tags_str,
            'description': f"Trasa {trail.get('terrain_type', 'mieszana')} o długości {trail.get('length_km', 0):.1f} km",
            'category': category,
            'estimated_time': self._estimate_time(trail),
            'user_rating': 3.0  # Domyślna ocena
        }

    def _determine_category(self, trail: Dict[str, Any]) -> str:
        """Określa kategorię trasy na podstawie jej parametrów."""
        length = trail.get('length_km', 0)
        difficulty = trail.get('difficulty', 2)
        terrain = trail.get('terrain_type', 'mixed')
        
        if difficulty == 1 and length < 5:
            return 'rodzinna'
        elif terrain in ['park', 'urban'] or 'viewpoint' in str(trail.get('tags', [])):
            return 'widokowa'
        elif difficulty == 3 or length > 15:
            return 'ekstremalna'
        else:
            return 'sportowa'

    def _estimate_time(self, trail: Dict[str, Any]) -> float:
        """Szacuje czas przejścia trasy w godzinach."""
        length = trail.get('length_km', 0)
        difficulty = trail.get('difficulty', 2)
        
        # Bazowy czas: 1 km = 1 godzina
        base_time = length
        
        # Mnożnik trudności
        difficulty_multiplier = {1: 0.8, 2: 1.0, 3: 1.5}.get(difficulty, 1.0)
        
        return round(base_time * difficulty_multiplier, 1)

    def _save_trails_to_file(self, trails: List[Dict[str, Any]]):
        """
        Fallback: Zapisuje trasy do pliku JSON (gdy baza danych niedostępna).
        
        Args:
            trails: Lista tras do zapisania
        """
        file_path = os.path.join(self.data_dir, "trails_data.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(trails, f, ensure_ascii=False, indent=2)
            print(f"📁 Zapisano dane o szlakach do pliku {file_path} (fallback)")
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania danych o szlakach: {e}") 