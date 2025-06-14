"""
UserRepository - Repozytorium do obsługi preferencji użytkowników
Etap 4: Integracja z bazą danych
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..database_manager import DatabaseManager, rows_to_dicts, row_to_dict

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Repozytorium do obsługi preferencji użytkowników w bazie danych.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        logger.info("Inicjalizacja UserRepository")
    
    def save_user_preferences(self, user_name: str = 'default', preferences: Dict[str, Any] = None) -> Optional[int]:
        """Zapisuje preferencje użytkownika."""
        try:
            if preferences is None:
                preferences = {}
            
            # Sprawdź czy użytkownik już istnieje
            existing = self.get_user_preferences(user_name)
            
            if existing:
                # Aktualizuj istniejące preferencje
                return self._update_user_preferences(existing['id'], preferences)
            else:
                # Utwórz nowe preferencje
                query = """
                    INSERT INTO user_preferences (
                        user_name, preferred_temp_min, preferred_temp_max, max_precipitation,
                        max_difficulty, max_length_km, preferred_terrain_types, preferred_categories
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    user_name,
                    preferences.get('preferred_temp_min', 15.0),
                    preferences.get('preferred_temp_max', 25.0),
                    preferences.get('max_precipitation', 5.0),
                    preferences.get('max_difficulty', 3),
                    preferences.get('max_length_km', 20.0),
                    ','.join(preferences.get('preferred_terrain_types', ['górski', 'leśny'])),
                    ','.join(preferences.get('preferred_categories', ['sportowa', 'widokowa']))
                )
                
                pref_id = self.db_manager.execute_insert(query, params)
                
                if pref_id:
                    logger.info(f"✅ Zapisano preferencje użytkownika: {user_name} (ID: {pref_id})")
                
                return pref_id
                
        except Exception as e:
            logger.error(f"Błąd zapisywania preferencji użytkownika: {e}")
            return None
    
    def get_user_preferences(self, user_name: str = 'default') -> Optional[Dict[str, Any]]:
        """Pobiera preferencje użytkownika."""
        try:
            query = "SELECT * FROM user_preferences WHERE user_name = ? ORDER BY updated_at DESC LIMIT 1"
            results = self.db_manager.execute_query(query, (user_name,))
            
            if results:
                prefs = row_to_dict(results[0])
                
                # Konwertuj stringi z powrotem na listy
                if prefs.get('preferred_terrain_types'):
                    prefs['preferred_terrain_types'] = prefs['preferred_terrain_types'].split(',')
                if prefs.get('preferred_categories'):
                    prefs['preferred_categories'] = prefs['preferred_categories'].split(',')
                
                logger.info(f"Pobrano preferencje użytkownika: {user_name}")
                return prefs
            
            logger.info(f"Brak preferencji dla użytkownika: {user_name}")
            return None
            
        except Exception as e:
            logger.error(f"Błąd pobierania preferencji użytkownika: {e}")
            return None
    
    def _update_user_preferences(self, pref_id: int, preferences: Dict[str, Any]) -> Optional[int]:
        """Aktualizuje istniejące preferencje użytkownika."""
        try:
            set_clauses = []
            params = []
            
            updatable_fields = {
                'preferred_temp_min': preferences.get('preferred_temp_min'),
                'preferred_temp_max': preferences.get('preferred_temp_max'),
                'max_precipitation': preferences.get('max_precipitation'),
                'max_difficulty': preferences.get('max_difficulty'),
                'max_length_km': preferences.get('max_length_km'),
                'preferred_terrain_types': ','.join(preferences.get('preferred_terrain_types', [])) if preferences.get('preferred_terrain_types') else None,
                'preferred_categories': ','.join(preferences.get('preferred_categories', [])) if preferences.get('preferred_categories') else None
            }
            
            for field, value in updatable_fields.items():
                if value is not None:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return pref_id
            
            params.append(pref_id)
            
            query = f"UPDATE user_preferences SET {', '.join(set_clauses)} WHERE id = ?"
            
            rows_affected = self.db_manager.execute_update(query, tuple(params))
            
            if rows_affected > 0:
                logger.info(f"✅ Zaktualizowano preferencje użytkownika ID: {pref_id}")
                return pref_id
            
            return None
            
        except Exception as e:
            logger.error(f"Błąd aktualizacji preferencji: {e}")
            return None
    
    def save_recommendation_history(self, user_name: str, search_criteria: Dict[str, Any], recommended_routes: List[Dict[str, Any]]) -> Optional[int]:
        """Zapisuje historię rekomendacji."""
        try:
            query = """
                INSERT INTO recommendation_history (
                    user_name, search_criteria, recommended_routes
                ) VALUES (?, ?, ?)
            """
            
            # Konwertuj na JSON
            criteria_json = json.dumps(search_criteria, ensure_ascii=False)
            routes_json = json.dumps([route.get('name', 'Unknown') for route in recommended_routes], ensure_ascii=False)
            
            params = (user_name, criteria_json, routes_json)
            
            history_id = self.db_manager.execute_insert(query, params)
            
            if history_id:
                logger.info(f"✅ Zapisano historię rekomendacji dla: {user_name} (ID: {history_id})")
            
            return history_id
            
        except Exception as e:
            logger.error(f"Błąd zapisywania historii rekomendacji: {e}")
            return None
    
    def get_recommendation_history(self, user_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Pobiera historię rekomendacji użytkownika."""
        try:
            query = """
                SELECT * FROM recommendation_history 
                WHERE user_name = ? 
                ORDER BY search_date DESC 
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (user_name, limit))
            history = rows_to_dicts(results)
            
            # Konwertuj JSON z powrotem na obiekty
            for item in history:
                try:
                    if item.get('search_criteria'):
                        item['search_criteria'] = json.loads(item['search_criteria'])
                    if item.get('recommended_routes'):
                        item['recommended_routes'] = json.loads(item['recommended_routes'])
                except json.JSONDecodeError:
                    logger.warning(f"Błąd parsowania JSON w historii ID: {item.get('id')}")
            
            logger.info(f"Pobrano {len(history)} rekordów historii dla: {user_name}")
            return history
            
        except Exception as e:
            logger.error(f"Błąd pobierania historii rekomendacji: {e}")
            return []
    
    def get_all_users(self) -> List[str]:
        """Pobiera listę wszystkich użytkowników."""
        try:
            query = "SELECT DISTINCT user_name FROM user_preferences ORDER BY user_name"
            results = self.db_manager.execute_query(query)
            
            users = [row['user_name'] for row in results]
            logger.info(f"Znaleziono {len(users)} użytkowników")
            return users
            
        except Exception as e:
            logger.error(f"Błąd pobierania listy użytkowników: {e}")
            return []
    
    def delete_user_data(self, user_name: str) -> bool:
        """Usuwa wszystkie dane użytkownika."""
        try:
            # Usuń preferencje
            query1 = "DELETE FROM user_preferences WHERE user_name = ?"
            prefs_deleted = self.db_manager.execute_update(query1, (user_name,))
            
            # Usuń historię
            query2 = "DELETE FROM recommendation_history WHERE user_name = ?"
            history_deleted = self.db_manager.execute_update(query2, (user_name,))
            
            total_deleted = prefs_deleted + history_deleted
            
            if total_deleted > 0:
                logger.info(f"✅ Usunięto dane użytkownika {user_name}: {prefs_deleted} preferencji, {history_deleted} historii")
                return True
            else:
                logger.warning(f"Nie znaleziono danych użytkownika: {user_name}")
                return False
                
        except Exception as e:
            logger.error(f"Błąd usuwania danych użytkownika: {e}")
            return False
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Pobiera statystyki użytkowników."""
        try:
            stats = {}
            
            # Liczba użytkowników
            query = "SELECT COUNT(DISTINCT user_name) as count FROM user_preferences"
            results = self.db_manager.execute_query(query)
            stats['total_users'] = results[0]['count'] if results else 0
            
            # Liczba preferencji
            query = "SELECT COUNT(*) as count FROM user_preferences"
            results = self.db_manager.execute_query(query)
            stats['total_preferences'] = results[0]['count'] if results else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk użytkowników: {e}")
            return {} 