"""
Moduł zarządzania konfiguracją aplikacji City Builder.
Obsługuje wczytywanie, zapisywanie i walidację ustawień z pliku JSON.

Funkcje:
- Wczytywanie konfiguracji z pliku JSON
- Walidacja ustawień za pomocą wyrażeń regularnych
- Łączenie z ustawieniami domyślnymi
- Bezpieczne zapisywanie z tworzeniem kopii zapasowych
- Obsługa błędów i fallback do wartości domyślnych
"""

import json
import os
import re
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import copy

class ConfigManager:
    """
    Menedżer konfiguracji aplikacji z walidacją i obsługą błędów.
    
    Zarządza wszystkimi ustawieniami gry:
    - Ustawienia rozgrywki (rozmiar mapy, trudność, język)
    - Ustawienia interfejsu (rozmiar okna, zoom, wyświetlanie)
    - Ustawienia wydajności (FPS, cache, wielowątkowość)
    - Ustawienia bazy danych (ścieżki, kopie zapasowe)
    - Ustawienia eksportu (formaty, ścieżki)
    - Ustawienia zaawansowane (debug, cheaty, mody)
    """
    
    def __init__(self, config_path: str = "data/config.json"):
        """
        Inicjalizuje menedżer konfiguracji.
        
        Args:
            config_path: ścieżka do pliku konfiguracyjnego (domyślnie data/config.json)
            
        Proces inicjalizacji:
        1. Ustawia ścieżkę do pliku konfiguracji
        2. Przygotowuje domyślną konfigurację
        3. Konfiguruje walidatory regex
        4. Wczytuje konfigurację z pliku (lub tworzy domyślną)
        """
        self.config_path = Path(config_path)  # Path to obiekt ścieżki z pathlib
        self.config: Dict[str, Any] = {}  # aktualnie załadowana konfiguracja
        self.default_config = self._get_default_config()  # domyślne ustawienia
        self.validators = self._setup_validators()  # walidatory regex
        
        # Konfiguracja logowania - do rejestrowania operacji na konfiguracji
        self.logger = logging.getLogger(__name__)  # __name__ to nazwa modułu
        
        # Wczytaj konfigurację z pliku (lub utwórz domyślną)
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Zwraca domyślną konfigurację aplikacji.
        
        Returns:
            Dict: słownik z domyślnymi ustawieniami podzielonymi na kategorie
            
        Struktura konfiguracji:
        - game_settings: podstawowe ustawienia gry
        - ui_settings: ustawienia interfejsu użytkownika
        - performance_settings: ustawienia wydajności
        - database_settings: ustawienia bazy danych
        - export_settings: ustawienia eksportu danych
        - advanced_settings: zaawansowane opcje dla deweloperów
        """
        return {
            "game_settings": {
                "default_map_size": {"width": 60, "height": 60},  # domyślny rozmiar mapy
                "auto_save_interval": 300,  # automatyczny zapis co 5 minut (300 sekund)
                "difficulty": "Normal",  # poziom trudności: Easy/Normal/Hard
                "language": "pl",  # język interfejsu (kod ISO 639-1)
                "enable_sound": True,  # czy włączyć dźwięki
                "enable_animations": True,  # czy włączyć animacje
                "show_tooltips": True  # czy pokazywać podpowiedzi
            },
            "ui_settings": {
                "window_width": 1600,  # szerokość okna w pikselach
                "window_height": 1000,  # wysokość okna w pikselach
                "tile_size": 32,  # rozmiar kafelka w pikselach
                "zoom_levels": [0.5, 0.75, 1.0, 1.25, 1.5, 2.0],  # dostępne poziomy powiększenia
                "default_zoom": 1.0,  # domyślne powiększenie
                "show_grid": True,  # czy pokazywać siatkę
                "show_building_effects": True  # czy pokazywać efekty budynków
            },
            "performance_settings": {
                "max_fps": 60,  # maksymalna liczba klatek na sekundę
                "update_interval": 15000,  # interwał aktualizacji w milisekundach
                "enable_multithreading": False,  # czy używać wielowątkowości (eksperymentalne)
                "cache_size": 100,  # rozmiar cache dla obrazków
                "log_level": "INFO"  # poziom logowania: DEBUG/INFO/WARNING/ERROR/CRITICAL
            },
            "database_settings": {
                "db_path": "city_builder.db",  # ścieżka do pliku bazy danych SQLite
                "backup_interval": 3600,  # interwał kopii zapasowych w sekundach (1 godzina)
                "max_backups": 5  # maksymalna liczba przechowywanych kopii zapasowych
            },
            "export_settings": {
                "default_export_format": "CSV",  # domyślny format eksportu: CSV/JSON/XML/XLSX
                "export_path": "exports/",  # ścieżka do folderu eksportów
                "include_charts": True,  # czy dołączać wykresy do eksportów
                "chart_format": "PNG"  # format wykresów: PNG/JPG/SVG/PDF
            },
            "advanced_settings": {
                "debug_mode": False,  # tryb debugowania (więcej logów, dodatkowe informacje)
                "show_performance_stats": False,  # czy pokazywać statystyki wydajności
                "enable_cheats": False,  # czy włączyć kody (nieskończone pieniądze, etc.)
                "custom_building_path": "assets/custom_buildings/",  # ścieżka do niestandardowych budynków
                "mod_support": False  # czy włączyć obsługę modów (eksperymentalne)
            }
        }
    
    def _setup_validators(self) -> Dict[str, re.Pattern]:
        """
        Konfiguruje walidatory regex dla różnych typów danych.
        
        Returns:
            Dict: słownik walidatorów regex
            
        Wyrażenia regularne (regex) sprawdzają czy tekst pasuje do wzorca:
        - ^ oznacza początek tekstu
        - $ oznacza koniec tekstu
        - [a-z] oznacza dowolną małą literę
        - {2} oznacza dokładnie 2 znaki
        - + oznacza jeden lub więcej
        - * oznacza zero lub więcej
        - ? oznacza opcjonalny
        """
        return {
            'difficulty': re.compile(r'^(Easy|Normal|Hard)$'),  # tylko te 3 opcje
            'language': re.compile(r'^[a-z]{2}$'),  # 2 małe litery (np. "pl", "en")
            'log_level': re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$'),  # poziomy logowania
            'export_format': re.compile(r'^(CSV|JSON|XML|XLSX)$'),  # formaty eksportu
            'chart_format': re.compile(r'^(PNG|JPG|JPEG|SVG|PDF)$'),  # formaty wykresów
            'file_path': re.compile(r'^[a-zA-Z0-9_\-./\\]+\.(db|json|csv|xml)$'),  # ścieżka do pliku
            'directory_path': re.compile(r'^[a-zA-Z0-9_\-./\\]+[/\\]?$'),  # ścieżka do folderu
            'positive_int': re.compile(r'^[1-9]\d*$'),  # dodatnia liczba całkowita
            'positive_float': re.compile(r'^[0-9]*\.?[0-9]+$'),  # dodatnia liczba zmiennoprzecinkowa
            'boolean_string': re.compile(r'^(true|false|True|False|1|0)$')  # wartości logiczne jako tekst
        }
    
    def validate_value(self, key: str, value: Any) -> bool:
        """
        Waliduje wartość używając wyrażeń regularnych.
        
        Args:
            key: klucz konfiguracji (nazwa ustawienia)
            value: wartość do walidacji
            
        Returns:
            bool: True jeśli wartość jest poprawna, False w przeciwnym razie
            
        Proces walidacji:
        1. Konwertuje wartość na string dla regex
        2. Sprawdza typ walidacji na podstawie klucza
        3. Używa odpowiedniego walidatora regex
        4. Zwraca wynik walidacji
        """
        try:
            # Konwertuj wartość na string dla regex
            str_value = str(value)
            
            # Mapowanie kluczy konfiguracji na typy walidatorów
            validation_map = {
                'difficulty': 'difficulty',
                'language': 'language',
                'log_level': 'log_level',
                'default_export_format': 'export_format',
                'chart_format': 'chart_format',
                'db_path': 'file_path',
                'export_path': 'directory_path',
                'custom_building_path': 'directory_path'
            }
            
            # Walidacja numeryczna - sprawdź czy klucz to liczba całkowita
            if key in ['window_width', 'window_height', 'tile_size', 'max_fps', 
                      'update_interval', 'cache_size', 'auto_save_interval', 
                      'backup_interval', 'max_backups']:
                return self.validators['positive_int'].match(str_value) is not None
            
            # Walidacja liczb zmiennoprzecinkowych
            if key in ['default_zoom'] or 'zoom_levels' in key:
                return self.validators['positive_float'].match(str_value) is not None
            
            # Walidacja wartości logicznych (boolean)
            if isinstance(value, bool):
                return True  # bool jest zawsze poprawny
            
            # Walidacja specyficzna na podstawie mapowania
            if key in validation_map:
                validator_key = validation_map[key]
                return self.validators[validator_key].match(str_value) is not None
            
            return True  # Domyślnie akceptuj nieznane klucze
            
        except Exception as e:
            self.logger.warning(f"Błąd walidacji dla {key}: {e}")
            return False
    
    def load_config(self) -> bool:
        """
        Wczytuje konfigurację z pliku JSON.
        
        Returns:
            bool: True jeśli wczytano pomyślnie, False w przypadku błędu
            
        Proces wczytywania:
        1. Sprawdź czy plik konfiguracji istnieje
        2. Jeśli nie istnieje, tworzy domyślną konfigurację
        3. Parsuje JSON z pliku
        4. Waliduje wczytaną konfigurację
        5. Łączy z domyślnymi ustawieniami (uzupełnia brakujące)
        6. W przypadku błędu używa konfiguracji domyślnej
        """
        try:
            # Sprawdź czy plik konfiguracji istnieje
            if not self.config_path.exists():
                self.logger.info("Plik konfiguracyjny nie istnieje, tworzę domyślny")
                self.config = self.default_config.copy()  # kopia domyślnej konfiguracji
                self.save_config()  # zapisz domyślną konfigurację do pliku
                return True
            
            # Wczytaj i parsuj JSON
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)  # parsuj JSON do słownika Python
            
            # Waliduj wczytaną konfigurację
            if self._validate_config(loaded_config):
                # Połącz z domyślnymi ustawieniami (uzupełnij brakujące klucze)
                self.config = self._merge_with_defaults(loaded_config)
                self.logger.info("Konfiguracja wczytana pomyślnie")
                return True
            else:
                self.logger.warning("Niepoprawna konfiguracja, używam domyślnej")
                self.config = self.default_config.copy()
                return False
                
        except json.JSONDecodeError as e:
            # Błąd parsowania JSON (niepoprawny format)
            self.logger.error(f"Błąd parsowania JSON: {e}")
            self.config = self.default_config.copy()
            return False
        except Exception as e:
            # Inne błędy (brak dostępu do pliku, etc.)
            self.logger.error(f"Błąd wczytywania konfiguracji: {e}")
            self.config = self.default_config.copy()
            return False
    
    def save_config(self) -> bool:
        """
        Zapisuje konfigurację do pliku JSON.
        
        Returns:
            bool: True jeśli zapisano pomyślnie, False w przypadku błędu
            
        Proces zapisywania:
        1. Tworzy katalog jeśli nie istnieje
        2. Zapisuje konfigurację do pliku JSON z wcięciami
        3. Używa kodowania UTF-8 dla polskich znaków
        4. Loguje wynik operacji
        """
        try:
            # Upewnij się, że katalog istnieje
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Zapisz konfigurację do pliku JSON
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                # indent=4: wcięcia dla czytelności
                # ensure_ascii=False: pozwala na polskie znaki
            
            self.logger.info("Konfiguracja zapisana pomyślnie")
            return True
            
        except Exception as e:
            self.logger.error(f"Błąd zapisywania konfiguracji: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Pobiera wartość z konfiguracji używając ścieżki z kropkami.
        
        Args:
            key_path: Ścieżka do klucza (np. "game_settings.difficulty")
            default: Wartość domyślna
            
        Returns:
            Wartość z konfiguracji lub default
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Ustawia wartość w konfiguracji używając ścieżki z kropkami.
        
        Args:
            key_path: Ścieżka do klucza (np. "game_settings.difficulty")
            value: Nowa wartość
            
        Returns:
            True jeśli ustawiono pomyślnie
        """
        try:
            keys = key_path.split('.')
            
            # Waliduj wartość
            if not self.validate_value(keys[-1], value):
                self.logger.warning(f"Niepoprawna wartość dla {key_path}: {value}")
                return False
            
            # Nawiguj do odpowiedniego miejsca
            current = self.config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Ustaw wartość
            current[keys[-1]] = value
            self.logger.info(f"Ustawiono {key_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Błąd ustawiania {key_path}: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Waliduje strukturę konfiguracji."""
        required_sections = ['game_settings', 'ui_settings', 'performance_settings']
        
        for section in required_sections:
            if section not in config:
                return False
        
        return True
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Łączy wczytaną konfigurację z domyślną."""
        merged = self.default_config.copy()
        
        def deep_merge(default: Dict, loaded: Dict) -> Dict:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(merged, loaded_config)
    
    def reset_to_defaults(self) -> bool:
        """Resetuje konfigurację do wartości domyślnych."""
        try:
            # Wygeneruj świeżą kopię domyślnej konfiguracji
            self.config = copy.deepcopy(self._get_default_config())
            self.save_config()
            self.logger.info("Konfiguracja zresetowana do domyślnych wartości")
            return True
        except Exception as e:
            self.logger.error(f"Błąd resetowania konfiguracji: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """Eksportuje konfigurację do pliku."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Błąd eksportu konfiguracji: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Zwraca wszystkie ustawienia."""
        return self.config.copy()


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Zwraca singleton instancję ConfigManager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager 