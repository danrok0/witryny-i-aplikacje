"""
RouteRepository - Repozytorium do obsługi tras turystycznych
Etap 4: Integracja z bazą danych
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import math
import sys
import os

# Dodaj ścieżkę do utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.validators import TrailValidators, BasicValidators, ValidationError, safe_validate

from ..database_manager import DatabaseManager, rows_to_dicts, row_to_dict

logger = logging.getLogger(__name__)

class RouteRepository:
    """
    Repozytorium do obsługi tras turystycznych w bazie danych.
    Implementuje podstawowe operacje CRUD oraz zaawansowane wyszukiwanie.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium tras.
        
        Args:
            db_manager: Menedżer bazy danych
        """
        self.db_manager = db_manager
        logger.info("Inicjalizacja RouteRepository")
    
    def add_route(self, route_data: Dict[str, Any]) -> Optional[int]:
        """
        Dodaje nową trasę do bazy danych z walidacją danych.
        
        Args:
            route_data: Słownik z danymi trasy
            
        Returns:
            ID nowej trasy lub None w przypadku błędu
        """
        try:
            # WALIDACJA DANYCH PRZED ZAPISEM DO BAZY
            validated_data = self._validate_route_data(route_data)
            if not validated_data:
                logger.error(f"❌ Walidacja danych trasy nie powiodła się: {route_data.get('name', 'UNKNOWN')}")
                return None
            
            # Sprawdź czy trasa już istnieje (duplikat)
            if self._route_exists(validated_data['name'], validated_data.get('region')):
                logger.warning(f"⚠️ Trasa już istnieje: {validated_data['name']} w {validated_data.get('region')}")
                return None
            
            # Przygotuj zapytanie INSERT z zwalidowanymi danymi
            query = """
                INSERT INTO routes (
                    name, region, start_lat, start_lon, end_lat, end_lon,
                    length_km, elevation_gain, difficulty, terrain_type,
                    tags, description, category, estimated_time, user_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Użyj zwalidowanych danych
            params = (
                validated_data['name'],
                validated_data.get('region'),
                validated_data['start_lat'],
                validated_data['start_lon'],
                validated_data.get('end_lat', validated_data['start_lat']),
                validated_data.get('end_lon', validated_data['start_lon']),
                validated_data.get('length_km'),
                validated_data.get('elevation_gain'),
                validated_data.get('difficulty'),
                validated_data.get('terrain_type'),
                json.dumps(validated_data.get('tags', [])) if validated_data.get('tags') else None,
                validated_data.get('description'),
                validated_data.get('category', 'sportowa'),
                validated_data.get('estimated_time'),
                validated_data.get('user_rating')
            )
            
            route_id = self.db_manager.execute_insert(query, params)
            
            if route_id:
                logger.info(f"✅ Dodano zwalidowaną trasę: {validated_data['name']} (ID: {route_id})")
                
                # Dodaj recenzje jeśli są dostępne
                if 'reviews' in validated_data and validated_data['reviews']:
                    self._add_route_reviews(route_id, validated_data['reviews'])
            
            return route_id
            
        except Exception as e:
            logger.error(f"Błąd dodawania trasy: {e}")
            return None
    
    def get_route_by_id(self, route_id: int) -> Optional[Dict[str, Any]]:
        """
        Pobiera trasę po ID.
        
        Args:
            route_id: ID trasy
            
        Returns:
            Słownik z danymi trasy lub None
        """
        try:
            query = "SELECT * FROM routes WHERE id = ?"
            results = self.db_manager.execute_query(query, (route_id,))
            
            if results:
                route = row_to_dict(results[0])
                # Dodaj recenzje
                route['reviews'] = self._get_route_reviews(route_id)
                return route
            
            return None
            
        except Exception as e:
            logger.error(f"Błąd pobierania trasy {route_id}: {e}")
            return None
    
    def find_routes_by_region(self, region: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Wyszukuje trasy w określonym regionie.
        
        Args:
            region: Nazwa regionu
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista tras
        """
        try:
            query = """
                SELECT * FROM routes 
                WHERE region LIKE ? 
                ORDER BY user_rating DESC, name
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (f"%{region}%", limit))
            routes = rows_to_dicts(results)
            
            # Dodaj recenzje do każdej trasy
            for route in routes:
                route['reviews'] = self._get_route_reviews(route['id'])
            
            logger.info(f"Znaleziono {len(routes)} tras w regionie: {region}")
            return routes
            
        except Exception as e:
            logger.error(f"Błąd wyszukiwania tras w regionie {region}: {e}")
            return []
    
    def find_routes_by_region_and_name(self, region: str, name: str) -> List[Dict[str, Any]]:
        """
        Wyszukuje trasy po regionie i nazwie (do sprawdzania duplikatów).
        
        Args:
            region: Nazwa regionu
            name: Nazwa trasy
            
        Returns:
            Lista tras pasujących do kryteriów
        """
        try:
            query = """
                SELECT * FROM routes 
                WHERE region = ? AND name = ?
                LIMIT 1
            """
            
            results = self.db_manager.execute_query(query, (region, name))
            routes = rows_to_dicts(results)
            
            return routes
            
        except Exception as e:
            logger.error(f"Błąd wyszukiwania tras po regionie i nazwie: {e}")
            return []
    
    def find_routes_by_difficulty(self, max_difficulty: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Wyszukuje trasy o określonej maksymalnej trudności.
        
        Args:
            max_difficulty: Maksymalna trudność (1-5)
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista tras
        """
        try:
            query = """
                SELECT * FROM routes 
                WHERE difficulty <= ? 
                ORDER BY difficulty, user_rating DESC
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (max_difficulty, limit))
            routes = rows_to_dicts(results)
            
            # Dodaj recenzje do każdej trasy
            for route in routes:
                route['reviews'] = self._get_route_reviews(route['id'])
            
            logger.info(f"Znaleziono {len(routes)} tras o trudności <= {max_difficulty}")
            return routes
            
        except Exception as e:
            logger.error(f"Błąd wyszukiwania tras po trudności: {e}")
            return []
    
    def find_routes_by_region_and_difficulty(self, region: str, max_difficulty: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Wyszukuje trasy w regionie o określonej maksymalnej trudności.
        
        Args:
            region: Nazwa regionu
            max_difficulty: Maksymalna trudność
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista tras
        """
        try:
            query = """
                SELECT * FROM routes 
                WHERE region LIKE ? AND difficulty <= ?
                ORDER BY user_rating DESC, difficulty
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (f"%{region}%", max_difficulty, limit))
            routes = rows_to_dicts(results)
            
            # Dodaj recenzje do każdej trasy
            for route in routes:
                route['reviews'] = self._get_route_reviews(route['id'])
            
            logger.info(f"Znaleziono {len(routes)} tras w regionie {region} o trudności <= {max_difficulty}")
            return routes
            
        except Exception as e:
            logger.error(f"Błąd wyszukiwania tras: {e}")
            return []
    
    def find_routes_in_radius(self, lat: float, lon: float, radius_km: float, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Wyszukuje trasy w określonym promieniu od punktu.
        
        Args:
            lat: Szerokość geograficzna punktu
            lon: Długość geograficzna punktu
            radius_km: Promień wyszukiwania w kilometrach
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista tras z odległościami
        """
        try:
            # Pobierz wszystkie trasy (można zoptymalizować używając bounding box)
            query = "SELECT * FROM routes"
            results = self.db_manager.execute_query(query)
            
            routes_with_distance = []
            
            for row in results:
                route = row_to_dict(row)
                
                # Oblicz odległość do punktu startowego trasy
                distance = self._calculate_distance(
                    lat, lon, 
                    route['start_lat'], route['start_lon']
                )
                
                if distance <= radius_km:
                    route['distance_km'] = round(distance, 2)
                    route['reviews'] = self._get_route_reviews(route['id'])
                    routes_with_distance.append(route)
            
            # Sortuj po odległości
            routes_with_distance.sort(key=lambda x: x['distance_km'])
            
            # Ogranicz wyniki
            routes_with_distance = routes_with_distance[:limit]
            
            logger.info(f"Znaleziono {len(routes_with_distance)} tras w promieniu {radius_km}km")
            return routes_with_distance
            
        except Exception as e:
            logger.error(f"Błąd wyszukiwania tras w promieniu: {e}")
            return []
    
    def search_routes(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Zaawansowane wyszukiwanie tras według wielu kryteriów z walidacją.
        
        Args:
            criteria: Słownik z kryteriami wyszukiwania
            
        Returns:
            Lista tras spełniających kryteria
        """
        try:
            # Waliduj kryteria wyszukiwania
            validated_criteria = self.validate_search_criteria(criteria)
            if not validated_criteria:
                logger.warning("❌ Brak prawidłowych kryteriów wyszukiwania")
                return []
            
            # Buduj zapytanie dynamicznie z zwalidowanych kryteriów
            where_conditions = []
            params = []
            
            if validated_criteria.get('name'):
                where_conditions.append("name LIKE ?")
                params.append(f"%{validated_criteria['name']}%")
            
            if validated_criteria.get('region'):
                where_conditions.append("region LIKE ?")
                params.append(f"%{validated_criteria['region']}%")
            
            if validated_criteria.get('max_difficulty'):
                where_conditions.append("difficulty <= ?")
                params.append(validated_criteria['max_difficulty'])
            
            if validated_criteria.get('min_length'):
                where_conditions.append("length_km >= ?")
                params.append(validated_criteria['min_length'])
            
            if validated_criteria.get('max_length'):
                where_conditions.append("length_km <= ?")
                params.append(validated_criteria['max_length'])
            
            if validated_criteria.get('terrain_type'):
                where_conditions.append("terrain_type LIKE ?")
                params.append(f"%{validated_criteria['terrain_type']}%")
            
            if validated_criteria.get('category'):
                where_conditions.append("category = ?")
                params.append(validated_criteria['category'])
            
            if validated_criteria.get('min_rating'):
                where_conditions.append("user_rating >= ?")
                params.append(validated_criteria['min_rating'])
            
            # Buduj zapytanie
            query = "SELECT * FROM routes"
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY user_rating DESC, name"
            
            # Dodaj zwalidowany limit
            limit = validated_criteria.get('limit', 50)
            query += f" LIMIT {limit}"
            
            results = self.db_manager.execute_query(query, tuple(params))
            routes = rows_to_dicts(results)
            
            # Dodaj recenzje do każdej trasy
            for route in routes:
                route['reviews'] = self._get_route_reviews(route['id'])
            
            logger.info(f"Wyszukiwanie zaawansowane: znaleziono {len(routes)} tras")
            return routes
            
        except Exception as e:
            logger.error(f"Błąd zaawansowanego wyszukiwania: {e}")
            return []
    
    def get_all_routes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Pobiera wszystkie trasy z bazy danych.
        
        Args:
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista wszystkich tras
        """
        try:
            query = "SELECT * FROM routes ORDER BY name LIMIT ?"
            results = self.db_manager.execute_query(query, (limit,))
            routes = rows_to_dicts(results)
            
            # Dodaj recenzje do każdej trasy (może być kosztowne dla dużej liczby tras)
            for route in routes:
                route['reviews'] = self._get_route_reviews(route['id'])
            
            logger.info(f"Pobrano {len(routes)} tras z bazy danych")
            return routes
            
        except Exception as e:
            logger.error(f"Błąd pobierania wszystkich tras: {e}")
            return []
    
    def update_route(self, route_id: int, route_data: Dict[str, Any]) -> bool:
        """
        Aktualizuje dane trasy.
        
        Args:
            route_id: ID trasy do aktualizacji
            route_data: Nowe dane trasy
            
        Returns:
            True jeśli aktualizacja się powiodła
        """
        try:
            # Buduj zapytanie UPDATE dynamicznie
            set_clauses = []
            params = []
            
            updatable_fields = [
                'name', 'region', 'start_lat', 'start_lon', 'end_lat', 'end_lon',
                'length_km', 'elevation_gain', 'difficulty', 'terrain_type',
                'tags', 'description', 'category', 'estimated_time', 'user_rating'
            ]
            
            for field in updatable_fields:
                if field in route_data:
                    set_clauses.append(f"{field} = ?")
                    params.append(route_data[field])
            
            if not set_clauses:
                logger.warning("Brak danych do aktualizacji")
                return False
            
            params.append(route_id)
            
            query = f"UPDATE routes SET {', '.join(set_clauses)} WHERE id = ?"
            
            rows_affected = self.db_manager.execute_update(query, tuple(params))
            
            if rows_affected > 0:
                logger.info(f"✅ Zaktualizowano trasę ID: {route_id}")
                return True
            else:
                logger.warning(f"Nie znaleziono trasy ID: {route_id}")
                return False
                
        except Exception as e:
            logger.error(f"Błąd aktualizacji trasy {route_id}: {e}")
            return False
    
    def delete_route(self, route_id: int) -> bool:
        """
        Usuwa trasę z bazy danych.
        
        Args:
            route_id: ID trasy do usunięcia
            
        Returns:
            True jeśli usunięcie się powiodło
        """
        try:
            query = "DELETE FROM routes WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (route_id,))
            
            if rows_affected > 0:
                logger.info(f"✅ Usunięto trasę ID: {route_id}")
                return True
            else:
                logger.warning(f"Nie znaleziono trasy ID: {route_id}")
                return False
                
        except Exception as e:
            logger.error(f"Błąd usuwania trasy {route_id}: {e}")
            return False
    
    def get_route_statistics(self) -> Dict[str, Any]:
        """
        Pobiera statystyki tras.
        
        Returns:
            Słownik ze statystykami
        """
        try:
            stats = {}
            
            # Liczba tras
            result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM routes")
            stats['total_routes'] = result[0]['count'] if result else 0
            
            # Rozkład trudności
            result = self.db_manager.execute_query("""
                SELECT difficulty, COUNT(*) as count 
                FROM routes 
                WHERE difficulty IS NOT NULL 
                GROUP BY difficulty 
                ORDER BY difficulty
            """)
            stats['difficulty_distribution'] = [dict(row) for row in result]
            
            # Najpopularniejsze regiony
            result = self.db_manager.execute_query("""
                SELECT region, COUNT(*) as count 
                FROM routes 
                WHERE region IS NOT NULL 
                GROUP BY region 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['popular_regions'] = [dict(row) for row in result]
            
            # Rozkład kategorii
            result = self.db_manager.execute_query("""
                SELECT category, COUNT(*) as count 
                FROM routes 
                WHERE category IS NOT NULL 
                GROUP BY category 
                ORDER BY count DESC
            """)
            stats['category_distribution'] = [dict(row) for row in result]
            
            # Średnie wartości
            result = self.db_manager.execute_query("""
                SELECT 
                    AVG(length_km) as avg_length,
                    AVG(elevation_gain) as avg_elevation,
                    AVG(user_rating) as avg_rating,
                    AVG(estimated_time) as avg_time
                FROM routes 
                WHERE length_km IS NOT NULL
            """)
            if result:
                row = result[0]
                stats['averages'] = {
                    'length_km': round(row['avg_length'], 2) if row['avg_length'] else 0,
                    'elevation_gain': round(row['avg_elevation'], 1) if row['avg_elevation'] else 0,
                    'user_rating': round(row['avg_rating'], 2) if row['avg_rating'] else 0,
                    'estimated_time': round(row['avg_time'], 1) if row['avg_time'] else 0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk tras: {e}")
            return {}
    
    def _add_route_reviews(self, route_id: int, reviews: List[str]) -> None:
        """
        Dodaje recenzje do trasy.
        
        Args:
            route_id: ID trasy
            reviews: Lista recenzji
        """
        try:
            for review_text in reviews:
                query = """
                    INSERT INTO route_reviews (
                        route_id, review_text, rating, sentiment
                    ) VALUES (?, ?, ?, ?)
                """
                
                # Prosta analiza sentymentu
                sentiment = 'positive' if any(word in review_text.lower() for word in ['dobra', 'świetna', 'polecam']) else 'neutral'
                rating = 4.0 if sentiment == 'positive' else 3.0
                
                params = (route_id, review_text, rating, sentiment)
                self.db_manager.execute_insert(query, params)
            
            logger.info(f"Dodano {len(reviews)} recenzji do trasy {route_id}")
            
        except Exception as e:
            logger.error(f"Błąd dodawania recenzji: {e}")
    
    def _get_route_reviews(self, route_id: int) -> List[str]:
        """
        Pobiera recenzje trasy.
        
        Args:
            route_id: ID trasy
            
        Returns:
            Lista recenzji
        """
        try:
            query = "SELECT review_text FROM route_reviews WHERE route_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (route_id,))
            
            return [row['review_text'] for row in results]
            
        except Exception as e:
            logger.error(f"Błąd pobierania recenzji trasy {route_id}: {e}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Oblicza odległość między dwoma punktami geograficznymi (wzór Haversine).
        
        Args:
            lat1, lon1: Współrzędne pierwszego punktu
            lat2, lon2: Współrzędne drugiego punktu
            
        Returns:
            Odległość w kilometrach
        """
        # Promień Ziemi w kilometrach
        R = 6371.0
        
        # Konwersja na radiany
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Różnice
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Wzór Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _validate_route_data(self, route_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Waliduje dane trasy przed zapisem do bazy danych.
        
        Args:
            route_data: Słownik z danymi trasy
            
        Returns:
            Zwalidowane dane lub None jeśli walidacja się nie powiodła
        """
        try:
            # Użyj TrailValidators do podstawowej walidacji
            validated = safe_validate(TrailValidators.validate_trail_data, route_data)
            if validated:
                logger.info(f"✅ Pełna walidacja trasy '{validated['name']}' przeszła pomyślnie")
                return validated
            
            # Jeśli pełna walidacja się nie powiodła, spróbuj walidacji podstawowej
            logger.warning(f"⚠️ Pełna walidacja nie powiodła się, próbuję podstawową walidację")
            
            # Podstawowe wymagania dla bazy danych
            validated_basic = {}
            
            # Nazwa jest wymagana
            name = safe_validate(BasicValidators.validate_string, 
                               route_data.get('name'), 'nazwa trasy', min_length=2, max_length=200)
            if not name:
                logger.error("❌ Nazwa trasy jest wymagana")
                return None
            validated_basic['name'] = name
            
            # Współrzędne startu są wymagane
            start_lat = route_data.get('start_lat')
            start_lon = route_data.get('start_lon')
            if start_lat is None or start_lon is None:
                logger.error("❌ Współrzędne startu są wymagane")
                return None
                
            coords = safe_validate(BasicValidators.validate_coordinates, start_lat, start_lon)
            if not coords:
                logger.error("❌ Nieprawidłowe współrzędne startu")
                return None
            validated_basic['start_lat'], validated_basic['start_lon'] = coords
            
            # Opcjonalne pola z walidacją
            if route_data.get('region'):
                region = safe_validate(BasicValidators.validate_string, 
                                     route_data['region'], 'region', max_length=100)
                if region:
                    validated_basic['region'] = region
            
            if route_data.get('length_km') is not None:
                length = safe_validate(BasicValidators.validate_number, 
                                     route_data['length_km'], 'długość', min_val=0, max_val=1000)
                if length is not None:
                    validated_basic['length_km'] = length
            
            if route_data.get('difficulty') is not None:
                difficulty = safe_validate(BasicValidators.validate_integer, 
                                         route_data['difficulty'], 'trudność', min_val=1, max_val=5)
                if difficulty is not None:
                    validated_basic['difficulty'] = difficulty
            
            if route_data.get('terrain_type'):
                terrain_choices = ['górski', 'leśny', 'nizinny', 'miejski', 'mieszany']
                terrain = safe_validate(BasicValidators.validate_choice, 
                                      route_data['terrain_type'].lower(), terrain_choices, 'typ terenu')
                if terrain:
                    validated_basic['terrain_type'] = terrain
            
            if route_data.get('category'):
                category_choices = ['rodzinna', 'widokowa', 'sportowa', 'ekstremalna']
                category = safe_validate(BasicValidators.validate_choice, 
                                       route_data['category'].lower(), category_choices, 'kategoria')
                if category:
                    validated_basic['category'] = category
            
            if route_data.get('user_rating') is not None:
                rating = safe_validate(BasicValidators.validate_number, 
                                     route_data['user_rating'], 'ocena', min_val=1.0, max_val=5.0)
                if rating is not None:
                    validated_basic['user_rating'] = rating
            
            # Skopiuj pozostałe pola bez dodatkowej walidacji
            for field in ['end_lat', 'end_lon', 'elevation_gain', 'description', 'estimated_time', 'tags', 'reviews']:
                if field in route_data:
                    validated_basic[field] = route_data[field]
            
            logger.info(f"✅ Podstawowa walidacja trasy '{validated_basic['name']}' przeszła pomyślnie")
            return validated_basic
            
        except Exception as e:
            logger.error(f"❌ Błąd walidacji danych trasy: {e}")
            return None
    
    def _route_exists(self, name: str, region: str = None) -> bool:
        """
        Sprawdza czy trasa o podanej nazwie już istnieje w bazie.
        
        Args:
            name: Nazwa trasy
            region: Region (opcjonalnie)
            
        Returns:
            True jeśli trasa istnieje
        """
        try:
            if region:
                existing = self.find_routes_by_region_and_name(region, name)
            else:
                query = "SELECT COUNT(*) as count FROM routes WHERE name = ?"
                result = self.db_manager.execute_query(query, (name,))
                count = result[0]['count'] if result else 0
                return count > 0
            
            return len(existing) > 0
            
        except Exception as e:
            logger.error(f"Błąd sprawdzania duplikatu trasy: {e}")
            return False
    
    def validate_search_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Waliduje kryteria wyszukiwania tras.
        
        Args:
            criteria: Słownik z kryteriami wyszukiwania
            
        Returns:
            Zwalidowane kryteria
        """
        validated = {}
        
        try:
            # Walidacja regionu
            if criteria.get('region'):
                region = safe_validate(BasicValidators.validate_string, 
                                     criteria['region'], 'region', max_length=100)
                if region:
                    validated['region'] = region
            
            # Walidacja trudności
            if criteria.get('max_difficulty') is not None:
                difficulty = safe_validate(BasicValidators.validate_integer, 
                                         criteria['max_difficulty'], 'trudność', min_val=1, max_val=5)
                if difficulty is not None:
                    validated['max_difficulty'] = difficulty
            
            # Walidacja długości
            if criteria.get('min_length') is not None:
                min_len = safe_validate(BasicValidators.validate_number, 
                                      criteria['min_length'], 'minimalna długość', min_val=0, max_val=1000)
                if min_len is not None:
                    validated['min_length'] = min_len
            
            if criteria.get('max_length') is not None:
                max_len = safe_validate(BasicValidators.validate_number, 
                                      criteria['max_length'], 'maksymalna długość', min_val=0, max_val=1000)
                if max_len is not None:
                    validated['max_length'] = max_len
            
            # Walidacja współrzędnych dla wyszukiwania w promieniu
            if criteria.get('lat') is not None and criteria.get('lon') is not None:
                coords = safe_validate(BasicValidators.validate_coordinates, 
                                     criteria['lat'], criteria['lon'])
                if coords:
                    validated['lat'], validated['lon'] = coords
            
            if criteria.get('radius_km') is not None:
                radius = safe_validate(BasicValidators.validate_number, 
                                     criteria['radius_km'], 'promień', min_val=0.1, max_val=1000)
                if radius is not None:
                    validated['radius_km'] = radius
            
            # Walidacja limitu wyników
            if criteria.get('limit') is not None:
                limit = safe_validate(BasicValidators.validate_integer, 
                                    criteria['limit'], 'limit', min_val=1, max_val=1000)
                if limit is not None:
                    validated['limit'] = limit
            
            logger.info(f"✅ Zwalidowano kryteria wyszukiwania: {len(validated)} kryteriów")
            return validated
            
        except Exception as e:
            logger.error(f"Błąd walidacji kryteriów wyszukiwania: {e}")
            return {} 