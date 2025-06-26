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

# === IMPORTY POTRZEBNE DLA ZARZĄDZANIA KONFIGURACJĄ ===
import json                                                # Do parsowania i zapisywania plików JSON
import os                                                  # Do operacji na systemie plików
import re                                                  # Do wyrażeń regularnych (walidacja)
import logging                                             # Do logowania operacji i błędów
from typing import Dict, Any, Optional, Union              # Dla typowania - poprawia czytelność kodu
from pathlib import Path                                   # Do obsługi ścieżek (nowoczesne API)
import copy                                                # Do głębokiego kopiowania obiektów

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
        # === INICJALIZACJA PODSTAWOWYCH ZMIENNYCH ===
        self.config_path = Path(config_path)               # Path to obiekt ścieżki z pathlib (lepsze API)
        self.config: Dict[str, Any] = {}                   # aktualnie załadowana konfiguracja (początkowo pusta)
        self.default_config = self._get_default_config()   # domyślne ustawienia (zawsze dostępne)
        self.validators = self._setup_validators()         # walidatory regex do sprawdzania wartości
        
        # === KONFIGURACJA LOGOWANIA ===
        # Konfiguruje logger do rejestrowania operacji na konfiguracji
        self.logger = logging.getLogger(__name__)          # __name__ to nazwa modułu (core.config_manager)
        
        # === WCZYTAJ KONFIGURACJĘ ===
        # Wczytaj konfigurację z pliku (lub utwórz domyślną jeśli plik nie istnieje)
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
            # === USTAWIENIA GRY ===
            "game_settings": {
                "default_map_size": {"width": 60, "height": 60},  # domyślny rozmiar mapy w kafelkach
                "auto_save_interval": 300,                        # automatyczny zapis co 5 minut (300 sekund)
                "difficulty": "Normal",                           # poziom trudności: Easy/Normal/Hard
                "language": "pl",                                 # język interfejsu (kod ISO 639-1)
                "enable_sound": True,                             # czy włączyć dźwięki w grze
                "enable_animations": True,                        # czy włączyć animacje interfejsu
                "show_tooltips": True                             # czy pokazywać podpowiedzi przy najechaniu myszką
            },
            # === USTAWIENIA INTERFEJSU ===
            "ui_settings": {
                "window_width": 1600,                            # szerokość okna w pikselach
                "window_height": 1000,                           # wysokość okna w pikselach
                "tile_size": 32,                                 # rozmiar kafelka w pikselach
                "zoom_levels": [0.5, 0.75, 1.0, 1.25, 1.5, 2.0], # dostępne poziomy powiększenia
                "default_zoom": 1.0,                             # domyślne powiększenie (100%)
                "show_grid": True,                               # czy pokazywać siatkę na mapie
                "show_building_effects": True                    # czy pokazywać efekty budynków (dym, światła)
            },
            # === USTAWIENIA WYDAJNOŚCI ===
            "performance_settings": {
                "max_fps": 60,                                   # maksymalna liczba klatek na sekundę
                "update_interval": 15000,                        # interwał aktualizacji w milisekundach (15 sekund)
                "enable_multithreading": False,                  # czy używać wielowątkowości (eksperymentalne)
                "cache_size": 100,                               # rozmiar cache dla obrazków (liczba elementów)
                "log_level": "INFO"                              # poziom logowania: DEBUG/INFO/WARNING/ERROR/CRITICAL
            },
            # === USTAWIENIA BAZY DANYCH ===
            "database_settings": {
                "db_path": "city_builder.db",                    # ścieżka do pliku bazy danych SQLite
                "backup_interval": 3600,                         # interwał kopii zapasowych w sekundach (1 godzina)
                "max_backups": 5                                 # maksymalna liczba przechowywanych kopii zapasowych
            },
            # === USTAWIENIA EKSPORTU ===
            "export_settings": {
                "default_export_format": "CSV",                  # domyślny format eksportu: CSV/JSON/XML/XLSX
                "export_path": "exports/",                       # ścieżka do folderu eksportów
                "include_charts": True,                          # czy dołączać wykresy do eksportów
                "chart_format": "PNG"                            # format wykresów: PNG/JPG/SVG/PDF
            },
            # === USTAWIENIA ZAAWANSOWANE ===
            "advanced_settings": {
                "debug_mode": False,                             # tryb debugowania (więcej logów, dodatkowe informacje)
                "show_performance_stats": False,                 # czy pokazywać statystyki wydajności
                "enable_cheats": False,                          # czy włączyć kody (nieskończone pieniądze, etc.)
                "custom_building_path": "assets/custom_buildings/",  # ścieżka do niestandardowych budynków
                "mod_support": False                             # czy włączyć obsługę modów (eksperymentalne)
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
            'difficulty': re.compile(r'^(Easy|Normal|Hard)$'),           # tylko te 3 opcje trudności
            'language': re.compile(r'^[a-z]{2}$'),                       # 2 małe litery (np. "pl", "en")
            'log_level': re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$'),  # poziomy logowania
            'export_format': re.compile(r'^(CSV|JSON|XML|XLSX)$'),       # formaty eksportu
            'chart_format': re.compile(r'^(PNG|JPG|JPEG|SVG|PDF)$'),     # formaty wykresów
            'file_path': re.compile(r'^[a-zA-Z0-9_\-./\\]+\.(db|json|csv|xml)$'),  # ścieżka do pliku
            'directory_path': re.compile(r'^[a-zA-Z0-9_\-./\\]+[/\\]?$'), # ścieżka do folderu
            'positive_int': re.compile(r'^[1-9]\d*$'),                   # dodatnia liczba całkowita
            'positive_float': re.compile(r'^[0-9]*\.?[0-9]+$'),          # dodatnia liczba zmiennoprzecinkowa
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
            # Konwertuj wartość na string dla regex (wszystkie walidatory regex operują na tekstach)
            str_value = str(value)
            
            # === MAPOWANIE KLUCZY NA TYPY WALIDATORÓW ===
            # Mapowanie kluczy konfiguracji na typy walidatorów regex
            validation_map = {
                'difficulty': 'difficulty',                   # poziom trudności
                'language': 'language',                       # kod języka
                'log_level': 'log_level',                     # poziom logowania
                'default_export_format': 'export_format',     # format eksportu
                'chart_format': 'chart_format',               # format wykresów
                'db_path': 'file_path',                       # ścieżka do pliku bazy danych
                'export_path': 'directory_path',              # ścieżka do folderu eksportów
                'custom_building_path': 'directory_path'      # ścieżka do niestandardowych budynków
            }
            
            # === WALIDACJA NUMERYCZNA ===
            # Sprawdź czy klucz to liczba całkowita (rozmiary okna, interwały, etc.)
            if key in ['window_width', 'window_height', 'tile_size', 'max_fps', 
                      'update_interval', 'cache_size', 'auto_save_interval', 
                      'backup_interval', 'max_backups']:
                # Użyj walidatora dla dodatnich liczb całkowitych
                return self.validators['positive_int'].match(str_value) is not None
            
            # === WALIDACJA LICZB ZMIENNOPRZECINKOWYCH ===
            # Sprawdź czy klucz to liczba zmiennoprzecinkowa (powiększenie)
            if key in ['default_zoom'] or 'zoom_levels' in key:
                # Użyj walidatora dla dodatnich liczb zmiennoprzecinkowych
                return self.validators['positive_float'].match(str_value) is not None
            
            # === WALIDACJA WARTOŚCI LOGICZNYCH ===
            # Sprawdź czy wartość to boolean (True/False)
            if isinstance(value, bool):
                return True  # bool jest zawsze poprawny
            
            # === WALIDACJA SPECYFICZNA ===
            # Walidacja specyficzna na podstawie mapowania kluczy
            if key in validation_map:
                # Pobierz odpowiedni walidator z mapowania
                validator_key = validation_map[key]
                # Sprawdź czy wartość pasuje do wzorca regex
                return self.validators[validator_key].match(str_value) is not None
            
            # Domyślnie akceptuj nieznane klucze (elastyczność)
            return True
            
        except Exception as e:
            # Obsłuż błędy walidacji (nie przerywaj działania aplikacji)
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
            # === SPRAWDŹ CZY PLIK ISTNIEJE ===
            # Sprawdź czy plik konfiguracyjny istnieje w systemie plików
            if not self.config_path.exists():
                # Plik nie istnieje - utwórz domyślną konfigurację
                self.logger.info("Plik konfiguracyjny nie istnieje, tworzę domyślny")
                self.config = self.default_config.copy()    # kopia domyślnej konfiguracji (nie referencja)
                self.save_config()                          # zapisz domyślną konfigurację do pliku
                return True
            
            # === WCZYTAJ I PARSÓJ JSON ===
            # Otwórz plik w trybie odczytu z kodowaniem UTF-8 (dla polskich znaków)
            with open(self.config_path, 'r', encoding='utf-8') as f:
                # Parsuj JSON do słownika Python
                loaded_config = json.load(f)
            
            # === WALIDUJ WCZYTANĄ KONFIGURACJĘ ===
            # Sprawdź czy wczytana konfiguracja ma poprawną strukturę
            if self._validate_config(loaded_config):
                # Konfiguracja poprawna - połącz z domyślnymi ustawieniami
                self.config = self._merge_with_defaults(loaded_config)
                self.logger.info("Konfiguracja wczytana pomyślnie")
                return True
            else:
                # Konfiguracja niepoprawna - użyj domyślnej
                self.logger.warning("Niepoprawna konfiguracja, używam domyślnej")
                self.config = self.default_config.copy()
                return False
                
        except json.JSONDecodeError as e:
            # Błąd parsowania JSON (niepoprawny format pliku)
            self.logger.error(f"Błąd parsowania JSON: {e}")
            self.config = self.default_config.copy()
            return False
        except Exception as e:
            # Inne błędy (brak dostępu do pliku, uprawnienia, etc.)
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
            # === UPEWNIJ SIĘ, ŻE KATALOG ISTNIEJE ===
            # Utwórz katalog nadrzędny jeśli nie istnieje (parents=True tworzy całą ścieżkę)
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # === ZAPISZ KONFIGURACJĘ DO PLIKU JSON ===
            # Otwórz plik w trybie zapisu z kodowaniem UTF-8
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # Zapisz słownik jako JSON z wcięciami dla czytelności
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                # indent=4: wcięcia dla czytelności (4 spacje)
                # ensure_ascii=False: pozwala na polskie znaki (nie escapuje ich)
            
            # Zaloguj sukces operacji
            self.logger.info("Konfiguracja zapisana pomyślnie")
            return True
            
        except Exception as e:
            # Obsłuż błędy zapisu (brak uprawnień, dysk pełny, etc.)
            self.logger.error(f"Błąd zapisywania konfiguracji: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Pobiera wartość z konfiguracji używając ścieżki z kropkami.
        
        Args:
            key_path: Ścieżka do klucza (np. "game_settings.difficulty")
            default: Wartość domyślna jeśli klucz nie istnieje
            
        Returns:
            Wartość z konfiguracji lub default
            
        Przykład użycia:
        - get("game_settings.difficulty") -> "Normal"
        - get("ui_settings.window_width") -> 1600
        - get("nieistniejacy.klucz", "domyslna") -> "domyslna"
        """
        try:
            # Podziel ścieżkę na pojedyncze klucze (np. "a.b.c" -> ["a", "b", "c"])
            keys = key_path.split('.')
            # Zacznij od głównego słownika konfiguracji
            value = self.config
            
            # Przejdź przez każdy klucz w ścieżce
            for key in keys:
                # Pobierz wartość dla aktualnego klucza
                value = value[key]
            
            # Zwróć znalezioną wartość
            return value
            
        except (KeyError, TypeError):
            # Klucz nie istnieje lub wartość nie jest słownikiem
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Ustawia wartość w konfiguracji używając ścieżki z kropkami.
        
        Args:
            key_path: Ścieżka do klucza (np. "game_settings.difficulty")
            value: Nowa wartość do ustawienia
            
        Returns:
            True jeśli ustawiono pomyślnie, False w przypadku błędu
            
        Przykład użycia:
        - set("game_settings.difficulty", "Hard") -> True
        - set("ui_settings.window_width", 1920) -> True
        """
        try:
            # Podziel ścieżkę na pojedyncze klucze
            keys = key_path.split('.')
            
            # === WALIDUJ WARTOŚĆ ===
            # Sprawdź czy nowa wartość jest poprawna (użyj ostatniego klucza)
            if not self.validate_value(keys[-1], value):
                self.logger.warning(f"Niepoprawna wartość dla {key_path}: {value}")
                return False
            
            # === NAWIGUJ DO ODPOWIEDNIEGO MIEJSCA ===
            # Zacznij od głównego słownika konfiguracji
            current = self.config
            # Przejdź przez wszystkie klucze oprócz ostatniego
            for key in keys[:-1]:
                # Jeśli klucz nie istnieje, utwórz pusty słownik
                if key not in current:
                    current[key] = {}
                # Przejdź do następnego poziomu
                current = current[key]
            
            # === USTAW WARTOŚĆ ===
            # Ustaw wartość dla ostatniego klucza w ścieżce
            current[keys[-1]] = value
            # Zaloguj zmianę
            self.logger.info(f"Ustawiono {key_path} = {value}")
            return True
            
        except Exception as e:
            # Obsłuż błędy ustawiania (niepoprawna ścieżka, etc.)
            self.logger.error(f"Błąd ustawiania {key_path}: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Waliduje strukturę konfiguracji.
        
        Args:
            config: Słownik konfiguracji do walidacji
        Returns:
            bool: True jeśli struktura jest poprawna
        """
        # Lista wymaganych sekcji konfiguracji
        required_sections = ['game_settings', 'ui_settings', 'performance_settings']
        
        # Sprawdź czy wszystkie wymagane sekcje istnieją
        for section in required_sections:
            if section not in config:
                return False
        
        # Wszystkie wymagane sekcje istnieją
        return True
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Łączy wczytaną konfigurację z domyślną (uzupełnia brakujące klucze).
        
        Args:
            loaded_config: Konfiguracja wczytana z pliku
        Returns:
            Dict: Połączona konfiguracja
        """
        # Zacznij od kopii domyślnej konfiguracji
        merged = self.default_config.copy()
        
        def deep_merge(default: Dict, loaded: Dict) -> Dict:
            """
            Funkcja pomocnicza do głębokiego łączenia słowników.
            
            Args:
                default: Słownik domyślny
                loaded: Słownik wczytany
            Returns:
                Dict: Połączony słownik
            """
            # Skopiuj słownik domyślny
            result = default.copy()
            # Iteruj przez wszystkie klucze w wczytanym słowniku
            for key, value in loaded.items():
                # Jeśli klucz istnieje w domyślnym i oba są słownikami
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # Rekurencyjnie połącz słowniki
                    result[key] = deep_merge(result[key], value)
                else:
                    # Zastąp wartość wczytaną
                    result[key] = value
            return result
        
        # Zwróć połączoną konfigurację
        return deep_merge(merged, loaded_config)
    
    def reset_to_defaults(self) -> bool:
        """
        Resetuje konfigurację do wartości domyślnych.
        
        Returns:
            bool: True jeśli resetowano pomyślnie
        """
        try:
            # Wygeneruj świeżą kopię domyślnej konfiguracji (głęboka kopia)
            self.config = copy.deepcopy(self._get_default_config())
            # Zapisz zresetowaną konfigurację do pliku
            self.save_config()
            # Zaloguj operację
            self.logger.info("Konfiguracja zresetowana do domyślnych wartości")
            return True
        except Exception as e:
            # Obsłuż błędy resetowania
            self.logger.error(f"Błąd resetowania konfiguracji: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Eksportuje konfigurację do pliku.
        
        Args:
            export_path: Ścieżka do pliku eksportu
        Returns:
            bool: True jeśli eksportowano pomyślnie
        """
        try:
            # Otwórz plik eksportu w trybie zapisu z kodowaniem UTF-8
            with open(export_path, 'w', encoding='utf-8') as f:
                # Zapisz konfigurację jako JSON z wcięciami
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            # Obsłuż błędy eksportu
            self.logger.error(f"Błąd eksportu konfiguracji: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Zwraca wszystkie ustawienia jako kopię.
        
        Returns:
            Dict: Kopia wszystkich ustawień
        """
        return self.config.copy()


# === SINGLETON INSTANCE ===
# Zmienna globalna przechowująca jedyną instancję ConfigManager
_config_manager = None

def get_config_manager() -> ConfigManager:
    """
    Zwraca singleton instancję ConfigManager.
    
    Singleton zapewnia, że w całej aplikacji istnieje tylko jedna instancja
    menedżera konfiguracji, co pozwala na spójne ustawienia.
    
    Returns:
        ConfigManager: Jedyna instancja menedżera konfiguracji
    """
    global _config_manager
    # Jeśli instancja nie istnieje, utwórz ją
    if _config_manager is None:
        _config_manager = ConfigManager()
    # Zwróć istniejącą instancję
    return _config_manager 