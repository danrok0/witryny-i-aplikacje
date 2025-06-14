"""
MENEDŻER BAZY DANYCH SQLite - GŁÓWNY MODUŁ ZARZĄDZANIA DANYMI
============================================================

Ten moduł zawiera klasę DatabaseManager, która jest centralnym punktem
zarządzania bazą danych SQLite w systemie rekomendacji tras turystycznych.

FUNKCJONALNOŚCI:
- Inicjalizacja i tworzenie struktur bazy danych
- Zarządzanie połączeniami z automatycznym zamykaniem
- Wykonywanie zapytań SQL (SELECT, INSERT, UPDATE, DELETE)
- Pobieranie statystyk i metryk bazy danych
- Operacje administracyjne (backup, restore, vacuum)
- Sprawdzanie integralności danych

ARCHITEKTURA:
- Wykorzystuje wzorzec Context Manager dla bezpiecznego zarządzania połączeniami
- Automatyczne tworzenie katalogów i inicjalizacja schematu
- Centralizowane logowanie wszystkich operacji
- Obsługa błędów z automatycznym rollback

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK
# ============================================================================
import sqlite3                                    # SQLite database engine
import os                                         # Operacje systemowe
import logging                                    # System logowania
from typing import Optional, List, Dict, Any     # Podpowiedzi typów
from contextlib import contextmanager            # Context manager dla połączeń
import json                                       # Obsługa JSON
from datetime import datetime                     # Operacje na datach

# ============================================================================
# KONFIGURACJA LOGOWANIA
# ============================================================================
logging.basicConfig(level=logging.INFO)          # Poziom logowania
logger = logging.getLogger(__name__)             # Logger dla tego modułu

# ============================================================================
# GŁÓWNA KLASA MENEDŻERA BAZY DANYCH
# ============================================================================

class DatabaseManager:
    """
    Główny menedżer bazy danych SQLite - centralny punkt zarządzania danymi.
    
    Ta klasa odpowiada za wszystkie operacje związane z bazą danych:
    - Tworzenie i inicjalizację struktur tabel
    - Zarządzanie połączeniami z automatycznym zamykaniem
    - Wykonywanie zapytań SQL z obsługą błędów
    - Administrację bazy (backup, restore, optymalizacja)
    - Pobieranie statystyk i metryk systemu
    
    Przykład użycia:
        db = DatabaseManager("data/routes.db")
        db.initialize_database()
        routes = db.execute_query("SELECT * FROM routes LIMIT 10")
        print(f"Znaleziono {len(routes)} tras")
    
    Uwaga: Używa wzorca Context Manager dla bezpiecznego zarządzania połączeniami.
    """
    
    def __init__(self, db_path: str = "data/database/routes.db"):
        """
        Inicjalizuje menedżer bazy danych z automatycznym tworzeniem katalogów.
        
        Args:
            db_path: Ścieżka do pliku bazy danych SQLite (domyślnie data/database/routes.db)
            
        Funkcja automatycznie:
        - Tworzy katalogi jeśli nie istnieją
        - Ustawia ścieżkę do pliku schematu SQL
        - Konfiguruje ścieżki dla operacji backup/restore
        - Loguje informacje o inicjalizacji
        """
        self.db_path = db_path                      # Ścieżka do pliku bazy danych
        self.schema_path = "sql/schema.sql"         # Ścieżka do pliku schematu
        
        # Automatycznie utwórz katalog dla bazy danych jeśli nie istnieje
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Zaloguj informację o inicjalizacji
        logger.info(f"🚀 Inicjalizacja DatabaseManager: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager dla połączeń z bazą danych.
        Automatycznie zamyka połączenie po użyciu.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwie
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Błąd bazy danych: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self) -> bool:
        """
        Inicjalizuje bazę danych, tworzy tabele i indeksy.
        
        Returns:
            bool: True jeśli inicjalizacja się powiodła
        """
        try:
            logger.info("Inicjalizacja bazy danych...")
            
            # Wczytaj schemat z pliku
            if not os.path.exists(self.schema_path):
                logger.error(f"Nie znaleziono pliku schematu: {self.schema_path}")
                return False
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Wykonaj schemat
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            
            logger.info("✅ Baza danych została zainicjalizowana pomyślnie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd podczas inicjalizacji bazy danych: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Wykonuje zapytanie SELECT i zwraca wyniki.
        
        Args:
            query: Zapytanie SQL
            params: Parametry zapytania
            
        Returns:
            Lista wyników jako sqlite3.Row
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Błąd wykonania zapytania: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Wykonuje zapytanie INSERT/UPDATE/DELETE.
        
        Args:
            query: Zapytanie SQL
            params: Parametry zapytania
            
        Returns:
            Liczba zmienionych wierszy
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Błąd wykonania aktualizacji: {e}")
            return 0
    
    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Wykonuje zapytanie INSERT i zwraca ID nowego rekordu.
        
        Args:
            query: Zapytanie SQL INSERT
            params: Parametry zapytania
            
        Returns:
            ID nowego rekordu lub None w przypadku błędu
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Błąd wykonania INSERT: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Pobiera statystyki bazy danych.
        
        Returns:
            Słownik ze statystykami
        """
        stats = {}
        
        try:
            # Liczba tras
            result = self.execute_query("SELECT COUNT(*) as count FROM routes")
            stats['routes_count'] = result[0]['count'] if result else 0
            
            # Liczba danych pogodowych
            result = self.execute_query("SELECT COUNT(*) as count FROM weather_data")
            stats['weather_records'] = result[0]['count'] if result else 0
            
            # Liczba recenzji
            result = self.execute_query("SELECT COUNT(*) as count FROM route_reviews")
            stats['reviews_count'] = result[0]['count'] if result else 0
            
            # Liczba preferencji użytkowników
            result = self.execute_query("SELECT COUNT(*) as count FROM user_preferences")
            stats['user_preferences'] = result[0]['count'] if result else 0
            
            # Rozmiar bazy danych
            if os.path.exists(self.db_path):
                stats['database_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats['database_size_mb'] = 0
            
            # Najpopularniejsze regiony
            result = self.execute_query("""
                SELECT region, COUNT(*) as count 
                FROM routes 
                WHERE region IS NOT NULL 
                GROUP BY region 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats['popular_regions'] = [dict(row) for row in result]
            
            # Rozkład trudności
            result = self.execute_query("""
                SELECT difficulty, COUNT(*) as count 
                FROM routes 
                WHERE difficulty IS NOT NULL 
                GROUP BY difficulty 
                ORDER BY difficulty
            """)
            stats['difficulty_distribution'] = [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk: {e}")
        
        return stats
    
    def check_database_integrity(self) -> bool:
        """
        Sprawdza integralność bazy danych.
        
        Returns:
            True jeśli baza jest w porządku
        """
        try:
            with self.get_connection() as conn:
                # Sprawdź integralność SQLite
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    logger.error(f"Błąd integralności bazy danych: {result[0]}")
                    return False
                
                # Sprawdź czy wszystkie tabele istnieją
                required_tables = ['routes', 'weather_data', 'user_preferences', 'route_reviews']
                existing_tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                existing_table_names = [row[0] for row in existing_tables]
                
                for table in required_tables:
                    if table not in existing_table_names:
                        logger.error(f"Brakuje tabeli: {table}")
                        return False
                
                logger.info("✅ Integralność bazy danych OK")
                return True
                
        except Exception as e:
            logger.error(f"Błąd sprawdzania integralności: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """
        Optymalizuje bazę danych (VACUUM).
        
        Returns:
            True jeśli operacja się powiodła
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            
            logger.info("✅ Baza danych została zoptymalizowana")
            return True
            
        except Exception as e:
            logger.error(f"Błąd optymalizacji bazy danych: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Tworzy kopię zapasową bazy danych.
        
        Args:
            backup_path: Ścieżka do pliku kopii zapasowej
            
        Returns:
            True jeśli kopia została utworzona
        """
        try:
            # Upewnij się, że katalog docelowy istnieje
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Skopiuj plik bazy danych
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"✅ Kopia zapasowa utworzona: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd tworzenia kopii zapasowej: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Przywraca bazę danych z kopii zapasowej.
        
        Args:
            backup_path: Ścieżka do pliku kopii zapasowej
            
        Returns:
            True jeśli przywracanie się powiodło
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Plik kopii zapasowej nie istnieje: {backup_path}")
                return False
            
            # Skopiuj plik kopii zapasowej
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # Sprawdź integralność przywróconej bazy
            if self.check_database_integrity():
                logger.info(f"✅ Baza danych przywrócona z: {backup_path}")
                return True
            else:
                logger.error("❌ Przywrócona baza danych jest uszkodzona")
                return False
                
        except Exception as e:
            logger.error(f"Błąd przywracania bazy danych: {e}")
            return False
    
    def close(self):
        """
        Zamyka połączenie z bazą danych.
        """
        logger.info("DatabaseManager zamknięty")


# Funkcja pomocnicza do konwersji sqlite3.Row na dict
def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Konwertuje sqlite3.Row na słownik.
    
    Args:
        row: Wiersz z bazy danych
        
    Returns:
        Słownik z danymi
    """
    return dict(row) if row else {}


def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """
    Konwertuje listę sqlite3.Row na listę słowników.
    
    Args:
        rows: Lista wierszy z bazy danych
        
    Returns:
        Lista słowników z danymi
    """
    return [dict(row) for row in rows] 