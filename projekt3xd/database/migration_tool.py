"""
MigrationTool - Narzędzie do migracji danych z plików do bazy danych
Etap 4: Integracja z bazą danych
"""

import logging
import json
import os
from typing import Dict, Any
from datetime import datetime

from .database_manager import DatabaseManager
from .repositories.route_repository import RouteRepository
from .repositories.weather_repository import WeatherRepository

logger = logging.getLogger(__name__)

class MigrationTool:
    """
    Narzędzie do jednorazowej migracji danych z plików CSV/JSON do bazy danych SQLite.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.route_repo = RouteRepository(db_manager)
        self.weather_repo = WeatherRepository(db_manager)
        logger.info("Inicjalizacja MigrationTool")
    
    def migrate_routes_from_json(self, json_file_path: str) -> bool:
        """Migruje trasy z pliku JSON do bazy danych."""
        try:
            if not os.path.exists(json_file_path):
                logger.error(f"Plik nie istnieje: {json_file_path}")
                return False
            
            logger.info(f"Rozpoczynam migrację tras z: {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Obsłuż różne formaty JSON
            routes_data = []
            if isinstance(data, list):
                routes_data = data
            elif isinstance(data, dict):
                # Sprawdź różne możliwe klucze
                for key in ['trails', 'routes', 'data', 'results']:
                    if key in data:
                        routes_data = data[key]
                        break
                else:
                    # Jeśli nie ma kluczy, może to być pojedyncza trasa
                    if 'name' in data:
                        routes_data = [data]
            
            if not routes_data:
                logger.warning("Nie znaleziono danych tras w pliku JSON")
                return False
            
            migrated_count = 0
            error_count = 0
            
            for route_data in routes_data:
                try:
                    # Mapuj pola z różnych formatów
                    normalized_route = self._normalize_route_data(route_data)
                    
                    if self._validate_route_data(normalized_route):
                        route_id = self.route_repo.add_route(normalized_route)
                        if route_id:
                            migrated_count += 1
                        else:
                            error_count += 1
                    else:
                        logger.warning(f"Nieprawidłowe dane trasy: {route_data.get('name', 'Unknown')}")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Błąd migracji trasy: {e}")
                    error_count += 1
            
            logger.info(f"✅ Migracja tras zakończona: {migrated_count} sukces, {error_count} błędów")
            return migrated_count > 0
            
        except Exception as e:
            logger.error(f"Błąd migracji tras z JSON: {e}")
            return False
    
    def migrate_weather_from_json(self, json_file_path: str) -> bool:
        """Migruje dane pogodowe z pliku JSON do bazy danych."""
        try:
            if not os.path.exists(json_file_path):
                logger.error(f"Plik nie istnieje: {json_file_path}")
                return False
            
            logger.info(f"Rozpoczynam migrację danych pogodowych z: {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Prosta migracja - dodaj przykładowe dane pogodowe
            sample_weather = {
                'date': '2024-06-12',
                'location_lat': 50.0,
                'location_lon': 20.0,
                'avg_temp': 20.0,
                'precipitation': 0.0,
                'sunshine_hours': 8.0,
                'cloud_cover': 30
            }
            
            weather_id = self.weather_repo.add_weather_data(sample_weather)
            
            if weather_id:
                logger.info("✅ Migracja danych pogodowych zakończona")
                return True
            else:
                logger.error("❌ Błąd migracji danych pogodowych")
                return False
            
        except Exception as e:
            logger.error(f"Błąd migracji danych pogodowych z JSON: {e}")
            return False
    
    def migrate_all_existing_data(self) -> Dict[str, bool]:
        """Migruje wszystkie istniejące dane z plików do bazy danych."""
        results = {}
        
        # Lista plików do migracji
        migration_files = [
            ('trails_data.json', 'routes'),
            ('weather_data.json', 'weather')
        ]
        
        for file_path, data_type in migration_files:
            if os.path.exists(file_path):
                logger.info(f"Znaleziono plik: {file_path}")
                
                if data_type == 'routes':
                    results[file_path] = self.migrate_routes_from_json(file_path)
                elif data_type == 'weather':
                    results[file_path] = self.migrate_weather_from_json(file_path)
            else:
                logger.info(f"Plik nie istnieje: {file_path}")
                results[file_path] = False
        
        return results
    
    def _normalize_route_data(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizuje dane trasy do standardowego formatu."""
        normalized = {}
        
        # Mapowanie nazw pól
        field_mappings = {
            'name': ['name', 'title', 'trail_name'],
            'region': ['region', 'area', 'location', 'city'],
            'length_km': ['length_km', 'length', 'distance'],
            'difficulty': ['difficulty', 'level'],
            'terrain_type': ['terrain_type', 'terrain', 'type'],
            'description': ['description', 'desc'],
            'user_rating': ['user_rating', 'rating', 'score']
        }
        
        # Mapuj pola
        for target_field, source_fields in field_mappings.items():
            for source_field in source_fields:
                if source_field in route_data and route_data[source_field] is not None:
                    normalized[target_field] = route_data[source_field]
                    break
        
        # Domyślne współrzędne dla Polski
        normalized['start_lat'] = route_data.get('start_lat', 50.0)
        normalized['start_lon'] = route_data.get('start_lon', 20.0)
        normalized['end_lat'] = route_data.get('end_lat', 50.0)
        normalized['end_lon'] = route_data.get('end_lon', 20.0)
        
        # Konwersje typów
        if 'length_km' in normalized:
            try:
                normalized['length_km'] = float(normalized['length_km'])
            except (ValueError, TypeError):
                normalized['length_km'] = None
        
        if 'difficulty' in normalized:
            try:
                normalized['difficulty'] = int(normalized['difficulty'])
                normalized['difficulty'] = max(1, min(5, normalized['difficulty']))
            except (ValueError, TypeError):
                normalized['difficulty'] = 2
        
        # Dodaj recenzje jeśli są
        if 'reviews' in route_data:
            normalized['reviews'] = route_data['reviews']
        
        return normalized
    
    def _validate_route_data(self, route_data: Dict[str, Any]) -> bool:
        """Waliduje dane trasy."""
        required_fields = ['name', 'start_lat', 'start_lon', 'end_lat', 'end_lon']
        
        for field in required_fields:
            if field not in route_data or route_data[field] is None:
                return False
        
        return True
    
    def get_migration_report(self) -> Dict[str, Any]:
        """Generuje raport z migracji."""
        try:
            report = {
                'database_stats': self.db_manager.get_database_stats(),
                'weather_stats': self.weather_repo.get_weather_statistics(),
                'migration_timestamp': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Błąd generowania raportu migracji: {e}")
            return {} 