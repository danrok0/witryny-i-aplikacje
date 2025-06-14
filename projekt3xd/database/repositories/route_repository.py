"""
RouteRepository - Repozytorium do obsługi tras turystycznych
Etap 4: Integracja z bazą danych
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import math

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
        Dodaje nową trasę do bazy danych.
        
        Args:
            route_data: Słownik z danymi trasy
            
        Returns:
            ID nowej trasy lub None w przypadku błędu
        """
        try:
            # Przygotuj zapytanie INSERT
            query = """
                INSERT INTO routes (
                    name, region, start_lat, start_lon, end_lat, end_lon,
                    length_km, elevation_gain, difficulty, terrain_type,
                    tags, description, category, estimated_time, user_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                route_data.get('name', ''),
                route_data.get('region'),
                route_data.get('start_lat', 0.0),
                route_data.get('start_lon', 0.0),
                route_data.get('end_lat', 0.0),
                route_data.get('end_lon', 0.0),
                route_data.get('length_km'),
                route_data.get('elevation_gain'),
                route_data.get('difficulty'),
                route_data.get('terrain_type'),
                route_data.get('tags'),
                route_data.get('description'),
                route_data.get('category', 'sportowa'),
                route_data.get('estimated_time'),
                route_data.get('user_rating')
            )
            
            route_id = self.db_manager.execute_insert(query, params)
            
            if route_id:
                logger.info(f"✅ Dodano trasę: {route_data.get('name')} (ID: {route_id})")
                
                # Dodaj recenzje jeśli są dostępne
                if 'reviews' in route_data and route_data['reviews']:
                    self._add_route_reviews(route_id, route_data['reviews'])
            
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
        Zaawansowane wyszukiwanie tras według wielu kryteriów.
        
        Args:
            criteria: Słownik z kryteriami wyszukiwania
            
        Returns:
            Lista tras spełniających kryteria
        """
        try:
            # Buduj zapytanie dynamicznie
            where_conditions = []
            params = []
            
            if criteria.get('name'):
                where_conditions.append("name LIKE ?")
                params.append(f"%{criteria['name']}%")
            
            if criteria.get('region'):
                where_conditions.append("region LIKE ?")
                params.append(f"%{criteria['region']}%")
            
            if criteria.get('max_difficulty'):
                where_conditions.append("difficulty <= ?")
                params.append(criteria['max_difficulty'])
            
            if criteria.get('min_length'):
                where_conditions.append("length_km >= ?")
                params.append(criteria['min_length'])
            
            if criteria.get('max_length'):
                where_conditions.append("length_km <= ?")
                params.append(criteria['max_length'])
            
            if criteria.get('terrain_type'):
                where_conditions.append("terrain_type LIKE ?")
                params.append(f"%{criteria['terrain_type']}%")
            
            if criteria.get('category'):
                where_conditions.append("category = ?")
                params.append(criteria['category'])
            
            if criteria.get('min_rating'):
                where_conditions.append("user_rating >= ?")
                params.append(criteria['min_rating'])
            
            # Buduj zapytanie
            query = "SELECT * FROM routes"
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY user_rating DESC, name"
            
            # Dodaj limit
            limit = criteria.get('limit', 50)
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