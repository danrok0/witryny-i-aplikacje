"""
WeatherRepository - Repozytorium do obsługi danych pogodowych
Etap 4: Integracja z bazą danych
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import json
import sys
import os

# Dodaj ścieżkę do utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.validators import WeatherValidators, BasicValidators, ValidationError, safe_validate

from ..database_manager import DatabaseManager, rows_to_dicts, row_to_dict

logger = logging.getLogger(__name__)

class WeatherRepository:
    """
    Repozytorium do obsługi danych pogodowych w bazie danych.
    Implementuje operacje CRUD oraz statystyki pogodowe.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicjalizuje repozytorium danych pogodowych.
        
        Args:
            db_manager: Menedżer bazy danych
        """
        self.db_manager = db_manager
        logger.info("Inicjalizacja WeatherRepository")
    
    def add_weather_data(self, weather_data: Dict[str, Any]) -> Optional[int]:
        """
        Dodaje dane pogodowe do bazy danych z walidacją.
        
        Args:
            weather_data: Słownik z danymi pogodowymi
            
        Returns:
            ID nowego rekordu lub None w przypadku błędu
        """
        try:
            # WALIDACJA DANYCH POGODOWYCH
            validated_data = self._validate_weather_data(weather_data)
            if not validated_data:
                logger.error(f"❌ Walidacja danych pogodowych nie powiodła się")
                return None
            
            query = """
                INSERT OR REPLACE INTO weather_data (
                    date, location_lat, location_lon, avg_temp, min_temp, max_temp,
                    precipitation, sunshine_hours, cloud_cover, wind_speed, humidity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Użyj zwalidowanych danych
            params = (
                validated_data.get('date'),
                validated_data.get('location_lat', 0.0),
                validated_data.get('location_lon', 0.0),
                validated_data.get('temperature'),  # avg_temp w WeatherValidators to 'temperature'
                validated_data.get('min_temp'),
                validated_data.get('max_temp'),
                validated_data.get('precipitation', 0.0),
                validated_data.get('sunshine_hours'),
                validated_data.get('cloud_cover'),
                validated_data.get('wind_speed'),
                validated_data.get('humidity')
            )
            
            weather_id = self.db_manager.execute_insert(query, params)
            
            if weather_id:
                logger.info(f"✅ Dodano zwalidowane dane pogodowe: {validated_data.get('date')} (ID: {weather_id})")
            
            return weather_id
            
        except Exception as e:
            logger.error(f"Błąd dodawania danych pogodowych: {e}")
            return None
    
    def get_weather_by_date_and_location(self, target_date: str, lat: float, lon: float, tolerance: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Pobiera dane pogodowe dla określonej daty i lokalizacji.
        
        Args:
            target_date: Data w formacie YYYY-MM-DD
            lat: Szerokość geograficzna
            lon: Długość geograficzna
            tolerance: Tolerancja dla współrzędnych (stopnie)
            
        Returns:
            Słownik z danymi pogodowymi lub None
        """
        try:
            query = """
                SELECT * FROM weather_data 
                WHERE date = ? 
                AND location_lat BETWEEN ? AND ?
                AND location_lon BETWEEN ? AND ?
                ORDER BY 
                    ABS(location_lat - ?) + ABS(location_lon - ?)
                LIMIT 1
            """
            
            params = (
                target_date,
                lat - tolerance, lat + tolerance,
                lon - tolerance, lon + tolerance,
                lat, lon
            )
            
            results = self.db_manager.execute_query(query, params)
            
            if results:
                weather = row_to_dict(results[0])
                logger.info(f"Znaleziono dane pogodowe dla {target_date} w lokalizacji ({lat}, {lon})")
                return weather
            
            logger.warning(f"Brak danych pogodowych dla {target_date} w lokalizacji ({lat}, {lon})")
            return None
            
        except Exception as e:
            logger.error(f"Błąd pobierania danych pogodowych: {e}")
            return None
    
    def get_weather_for_location_range(self, lat: float, lon: float, start_date: str, end_date: str, tolerance: float = 0.1) -> List[Dict[str, Any]]:
        """
        Pobiera dane pogodowe dla lokalizacji w określonym zakresie dat.
        
        Args:
            lat: Szerokość geograficzna
            lon: Długość geograficzna
            start_date: Data początkowa (YYYY-MM-DD)
            end_date: Data końcowa (YYYY-MM-DD)
            tolerance: Tolerancja dla współrzędnych
            
        Returns:
            Lista danych pogodowych
        """
        try:
            query = """
                SELECT * FROM weather_data 
                WHERE date BETWEEN ? AND ?
                AND location_lat BETWEEN ? AND ?
                AND location_lon BETWEEN ? AND ?
                ORDER BY date
            """
            
            params = (
                start_date, end_date,
                lat - tolerance, lat + tolerance,
                lon - tolerance, lon + tolerance
            )
            
            results = self.db_manager.execute_query(query, params)
            weather_data = rows_to_dicts(results)
            
            logger.info(f"Znaleziono {len(weather_data)} rekordów pogodowych dla lokalizacji ({lat}, {lon}) w okresie {start_date} - {end_date}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Błąd pobierania danych pogodowych dla zakresu: {e}")
            return []
    
    def get_weather_statistics_for_location(self, lat: float, lon: float, tolerance: float = 0.1) -> Dict[str, Any]:
        """
        Oblicza statystyki pogodowe dla lokalizacji.
        
        Args:
            lat: Szerokość geograficzna
            lon: Długość geograficzna
            tolerance: Tolerancja dla współrzędnych
            
        Returns:
            Słownik ze statystykami pogodowymi
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as record_count,
                    AVG(avg_temp) as avg_temperature,
                    MIN(min_temp) as min_temperature,
                    MAX(max_temp) as max_temperature,
                    AVG(precipitation) as avg_precipitation,
                    MAX(precipitation) as max_precipitation,
                    AVG(sunshine_hours) as avg_sunshine,
                    AVG(cloud_cover) as avg_cloud_cover,
                    AVG(wind_speed) as avg_wind_speed,
                    AVG(humidity) as avg_humidity
                FROM weather_data 
                WHERE location_lat BETWEEN ? AND ?
                AND location_lon BETWEEN ? AND ?
            """
            
            params = (
                lat - tolerance, lat + tolerance,
                lon - tolerance, lon + tolerance
            )
            
            results = self.db_manager.execute_query(query, params)
            
            if results and results[0]['record_count'] > 0:
                row = results[0]
                stats = {
                    'record_count': row['record_count'],
                    'temperature': {
                        'average': round(row['avg_temperature'], 1) if row['avg_temperature'] else None,
                        'minimum': round(row['min_temperature'], 1) if row['min_temperature'] else None,
                        'maximum': round(row['max_temperature'], 1) if row['max_temperature'] else None
                    },
                    'precipitation': {
                        'average': round(row['avg_precipitation'], 1) if row['avg_precipitation'] else None,
                        'maximum': round(row['max_precipitation'], 1) if row['max_precipitation'] else None
                    },
                    'sunshine_hours': round(row['avg_sunshine'], 1) if row['avg_sunshine'] else None,
                    'cloud_cover': round(row['avg_cloud_cover'], 1) if row['avg_cloud_cover'] else None,
                    'wind_speed': round(row['avg_wind_speed'], 1) if row['avg_wind_speed'] else None,
                    'humidity': round(row['avg_humidity'], 1) if row['avg_humidity'] else None
                }
                
                logger.info(f"Obliczono statystyki pogodowe dla lokalizacji ({lat}, {lon})")
                return stats
            
            logger.warning(f"Brak danych pogodowych dla lokalizacji ({lat}, {lon})")
            return {}
            
        except Exception as e:
            logger.error(f"Błąd obliczania statystyk pogodowych: {e}")
            return {}
    
    def get_monthly_weather_statistics(self, lat: float, lon: float, tolerance: float = 0.1) -> Dict[int, Dict[str, Any]]:
        """
        Oblicza miesięczne statystyki pogodowe dla lokalizacji.
        
        Args:
            lat: Szerokość geograficzna
            lon: Długość geograficzna
            tolerance: Tolerancja dla współrzędnych
            
        Returns:
            Słownik z miesięcznymi statystykami (klucz: numer miesiąca)
        """
        try:
            query = """
                SELECT 
                    CAST(strftime('%m', date) AS INTEGER) as month,
                    COUNT(*) as record_count,
                    AVG(avg_temp) as avg_temperature,
                    AVG(precipitation) as avg_precipitation,
                    AVG(sunshine_hours) as avg_sunshine,
                    AVG(cloud_cover) as avg_cloud_cover
                FROM weather_data 
                WHERE location_lat BETWEEN ? AND ?
                AND location_lon BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month
            """
            
            params = (
                lat - tolerance, lat + tolerance,
                lon - tolerance, lon + tolerance
            )
            
            results = self.db_manager.execute_query(query, params)
            
            monthly_stats = {}
            for row in results:
                month = row['month']
                monthly_stats[month] = {
                    'record_count': row['record_count'],
                    'avg_temperature': round(row['avg_temperature'], 1) if row['avg_temperature'] else None,
                    'avg_precipitation': round(row['avg_precipitation'], 1) if row['avg_precipitation'] else None,
                    'avg_sunshine': round(row['avg_sunshine'], 1) if row['avg_sunshine'] else None,
                    'avg_cloud_cover': round(row['avg_cloud_cover'], 1) if row['avg_cloud_cover'] else None
                }
            
            logger.info(f"Obliczono miesięczne statystyki pogodowe dla lokalizacji ({lat}, {lon})")
            return monthly_stats
            
        except Exception as e:
            logger.error(f"Błąd obliczania miesięcznych statystyk: {e}")
            return {}
    
    def get_weather_for_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Pobiera wszystkie dane pogodowe z określonego zakresu dat.
        
        Args:
            start_date: Data początkowa (YYYY-MM-DD)
            end_date: Data końcowa (YYYY-MM-DD)
            
        Returns:
            Lista danych pogodowych
        """
        try:
            query = """
                SELECT * FROM weather_data 
                WHERE date BETWEEN ? AND ?
                ORDER BY date, location_lat, location_lon
            """
            
            results = self.db_manager.execute_query(query, (start_date, end_date))
            weather_data = rows_to_dicts(results)
            
            logger.info(f"Pobrano {len(weather_data)} rekordów pogodowych z okresu {start_date} - {end_date}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Błąd pobierania danych pogodowych z zakresu: {e}")
            return []
    
    def delete_old_weather_data(self, cutoff_date: str) -> int:
        """
        Usuwa stare dane pogodowe sprzed określonej daty.
        
        Args:
            cutoff_date: Data graniczna (YYYY-MM-DD)
            
        Returns:
            Liczba usuniętych rekordów
        """
        try:
            query = "DELETE FROM weather_data WHERE date < ?"
            rows_affected = self.db_manager.execute_update(query, (cutoff_date,))
            
            logger.info(f"✅ Usunięto {rows_affected} starych rekordów pogodowych sprzed {cutoff_date}")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Błąd usuwania starych danych pogodowych: {e}")
            return 0
    
    def get_unique_locations(self) -> List[Tuple[float, float]]:
        """
        Pobiera listę unikalnych lokalizacji z danymi pogodowymi.
        
        Returns:
            Lista krotek (lat, lon)
        """
        try:
            query = """
                SELECT DISTINCT location_lat, location_lon 
                FROM weather_data 
                ORDER BY location_lat, location_lon
            """
            
            results = self.db_manager.execute_query(query)
            locations = [(row['location_lat'], row['location_lon']) for row in results]
            
            logger.info(f"Znaleziono {len(locations)} unikalnych lokalizacji z danymi pogodowymi")
            return locations
            
        except Exception as e:
            logger.error(f"Błąd pobierania unikalnych lokalizacji: {e}")
            return []
    
    def get_weather_data_count(self) -> int:
        """
        Pobiera liczbę rekordów pogodowych w bazie danych.
        
        Returns:
            Liczba rekordów
        """
        try:
            query = "SELECT COUNT(*) as count FROM weather_data"
            results = self.db_manager.execute_query(query)
            
            count = results[0]['count'] if results else 0
            logger.info(f"Liczba rekordów pogodowych w bazie: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Błąd pobierania liczby rekordów pogodowych: {e}")
            return 0
    
    def update_weather_data(self, weather_id: int, weather_data: Dict[str, Any]) -> bool:
        """
        Aktualizuje dane pogodowe.
        
        Args:
            weather_id: ID rekordu pogodowego
            weather_data: Nowe dane pogodowe
            
        Returns:
            True jeśli aktualizacja się powiodła
        """
        try:
            # Buduj zapytanie UPDATE dynamicznie
            set_clauses = []
            params = []
            
            updatable_fields = [
                'date', 'location_lat', 'location_lon', 'avg_temp', 'min_temp', 'max_temp',
                'precipitation', 'sunshine_hours', 'cloud_cover', 'wind_speed', 'humidity'
            ]
            
            for field in updatable_fields:
                if field in weather_data:
                    set_clauses.append(f"{field} = ?")
                    params.append(weather_data[field])
            
            if not set_clauses:
                logger.warning("Brak danych do aktualizacji")
                return False
            
            params.append(weather_id)
            
            query = f"UPDATE weather_data SET {', '.join(set_clauses)} WHERE id = ?"
            
            rows_affected = self.db_manager.execute_update(query, tuple(params))
            
            if rows_affected > 0:
                logger.info(f"✅ Zaktualizowano dane pogodowe ID: {weather_id}")
                return True
            else:
                logger.warning(f"Nie znaleziono danych pogodowych ID: {weather_id}")
                return False
                
        except Exception as e:
            logger.error(f"Błąd aktualizacji danych pogodowych {weather_id}: {e}")
            return False
    
    def get_weather_statistics(self) -> Dict[str, Any]:
        """
        Pobiera ogólne statystyki danych pogodowych.
        
        Returns:
            Słownik ze statystykami
        """
        try:
            stats = {}
            
            # Liczba rekordów
            query = "SELECT COUNT(*) as count FROM weather_data"
            results = self.db_manager.execute_query(query)
            stats['total_records'] = results[0]['count'] if results else 0
            
            # Średnie wartości
            query = """
                SELECT 
                    AVG(avg_temp) as avg_temperature,
                    AVG(precipitation) as avg_precipitation,
                    COUNT(DISTINCT location_lat || ',' || location_lon) as unique_locations
                FROM weather_data
            """
            results = self.db_manager.execute_query(query)
            if results:
                row = results[0]
                stats['averages'] = {
                    'temperature': round(row['avg_temperature'], 1) if row['avg_temperature'] else 0,
                    'precipitation': round(row['avg_precipitation'], 1) if row['avg_precipitation'] else 0
                }
                stats['unique_locations'] = row['unique_locations']
            
            return stats
            
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk pogodowych: {e}")
            return {}
    
    def delete_old_weather_data(self, cutoff_date: str) -> int:
        """Usuwa stare dane pogodowe sprzed określonej daty."""
        try:
            query = "DELETE FROM weather_data WHERE date < ?"
            rows_affected = self.db_manager.execute_update(query, (cutoff_date,))
            
            logger.info(f"✅ Usunięto {rows_affected} starych rekordów pogodowych sprzed {cutoff_date}")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Błąd usuwania starych danych pogodowych: {e}")
            return 0
    
    def _validate_weather_data(self, weather_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Waliduje dane pogodowe przed zapisem do bazy danych.
        
        Args:
            weather_data: Słownik z danymi pogodowymi
            
        Returns:
            Zwalidowane dane lub None jeśli walidacja się nie powiodła
        """
        try:
            # Użyj WeatherValidators do walidacji
            validated = safe_validate(WeatherValidators.validate_weather_data, weather_data)
            if validated:
                logger.info(f"✅ Pełna walidacja danych pogodowych przeszła pomyślnie")
                return validated
            
            # Jeśli pełna walidacja się nie powiodła, spróbuj podstawowej walidacji
            logger.warning(f"⚠️ Pełna walidacja nie powiodła się, próbuję podstawową walidację")
            
            validated_basic = {}
            
            # Data jest wymagana
            if weather_data.get('date'):
                date_validated = safe_validate(BasicValidators.validate_date, weather_data['date'])
                if date_validated:
                    validated_basic['date'] = weather_data['date']
                else:
                    logger.error("❌ Nieprawidłowy format daty")
                    return None
            else:
                logger.error("❌ Data jest wymagana")
                return None
            
            # Walidacja współrzędnych (opcjonalne ale jeśli są to muszą być prawidłowe)
            if weather_data.get('location_lat') is not None and weather_data.get('location_lon') is not None:
                coords = safe_validate(BasicValidators.validate_coordinates, 
                                     weather_data['location_lat'], weather_data['location_lon'])
                if coords:
                    validated_basic['location_lat'], validated_basic['location_lon'] = coords
                else:
                    logger.warning("⚠️ Nieprawidłowe współrzędne - używam domyślnych")
                    validated_basic['location_lat'], validated_basic['location_lon'] = 0.0, 0.0
            
            # Walidacja temperatury
            if weather_data.get('temperature') is not None or weather_data.get('avg_temp') is not None:
                temp = weather_data.get('temperature') or weather_data.get('avg_temp')
                temp_validated = safe_validate(BasicValidators.validate_number, 
                                             temp, 'temperatura', min_val=-50, max_val=50)
                if temp_validated is not None:
                    validated_basic['temperature'] = temp_validated
            
            # Walidacja opadów
            if weather_data.get('precipitation') is not None:
                precip = safe_validate(BasicValidators.validate_number, 
                                     weather_data['precipitation'], 'opady', min_val=0, max_val=500)
                if precip is not None:
                    validated_basic['precipitation'] = precip
            
            # Skopiuj pozostałe pola z podstawową walidacją liczbową
            for field in ['min_temp', 'max_temp', 'wind_speed', 'sunshine_hours', 'cloud_cover', 'humidity']:
                if field in weather_data and weather_data[field] is not None:
                    if field in ['min_temp', 'max_temp']:
                        min_val, max_val = -50, 50
                    elif field == 'wind_speed':
                        min_val, max_val = 0, 200
                    elif field == 'sunshine_hours':
                        min_val, max_val = 0, 24
                    elif field in ['cloud_cover', 'humidity']:
                        min_val, max_val = 0, 100
                    else:
                        min_val, max_val = 0, 1000
                    
                    val = safe_validate(BasicValidators.validate_number, 
                                      weather_data[field], field, min_val=min_val, max_val=max_val)
                    if val is not None:
                        validated_basic[field] = val
            
            logger.info(f"✅ Podstawowa walidacja danych pogodowych przeszła pomyślnie")
            return validated_basic
            
        except Exception as e:
            logger.error(f"❌ Błąd walidacji danych pogodowych: {e}")
            return None 