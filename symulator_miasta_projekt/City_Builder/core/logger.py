"""
System logowania dla aplikacji City Builder.
Obsługuje różne poziomy logowania, formatowanie i zapis do plików.

Funkcje:
- Kolorowe logi w konsoli
- Rotacja plików logów
- Różne poziomy logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Specjalistyczne loggery dla różnych modułów
- Analiza logów i statystyki
- Czyszczenie starych plików logów
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import reduce

class ColoredFormatter(logging.Formatter):
    """
    Formatter z kolorami dla konsoli.
    
    Dodaje kolory ANSI do różnych poziomów logowania:
    - DEBUG: niebieski (cyan)
    - INFO: zielony
    - WARNING: żółty  
    - ERROR: czerwony
    - CRITICAL: fioletowy (magenta)
    """
    
    # Kody kolorów ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan - niebieski
        'INFO': '\033[32m',     # Green - zielony
        'WARNING': '\033[33m',  # Yellow - żółty
        'ERROR': '\033[31m',    # Red - czerwony
        'CRITICAL': '\033[35m', # Magenta - fioletowy
        'RESET': '\033[0m'      # Reset - powrót do domyślnego koloru
    }
    
    def format(self, record):
        """
        Formatuje rekord loga dodając odpowiedni kolor.
        
        Args:
            record: rekord loga do sformatowania
        """
        # Dodaj kolor do poziomu logowania jeśli istnieje
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)  # wywołaj formatowanie bazowe

class GameLogger:
    """
    Główna klasa systemu logowania gry.
    
    Zarządza wszystkimi aspektami logowania:
    - Konfiguracja różnych loggerów
    - Ustawienia poziomów logowania
    - Rotacja i czyszczenie plików
    - Analiza i statystyki logów
    """
    
    def __init__(self, log_dir: str = "logs", config: Optional[Dict[str, Any]] = None):
        """
        Inicjalizuje system logowania.
        
        Args:
            log_dir (str): katalog na pliki logów (domyślnie "logs")
            config (Dict): konfiguracja logowania (opcjonalna)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)  # utwórz folder jeśli nie istnieje
        
        # Domyślna konfiguracja logowania
        self.config = config or {
            'level': 'INFO',                        # poziom logowania
            'console_output': True,                 # czy logować do konsoli
            'file_output': True,                    # czy logować do pliku
            'max_file_size': 10 * 1024 * 1024,    # maksymalny rozmiar pliku (10MB)
            'backup_count': 5,                      # liczba backupów do zachowania
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # format logów
            'date_format': '%Y-%m-%d %H:%M:%S'     # format daty
        }
        
        # Regex do walidacji poziomów logowania (tylko poprawne poziomy)
        self.level_validator = re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
        
        # Słownik przechowujący wszystkie loggery
        self.loggers: Dict[str, logging.Logger] = {}
        
        # Konfiguracja głównego loggera i specjalistycznych
        self._setup_root_logger()      # główny logger
        self._setup_game_loggers()     # loggery modułów gry
    
    def _setup_root_logger(self):
        """
        Konfiguruje główny logger aplikacji.
        
        Ustawia handlery dla konsoli i pliku z odpowiednim formatowaniem.
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level']))
        
        # Usuń istniejące handlery aby uniknąć duplikowania
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler konsoli (jeśli włączony w konfiguracji)
        if self.config['console_output']:
            console_handler = logging.StreamHandler()
            console_formatter = ColoredFormatter(
                self.config['format'],
                datefmt=self.config['date_format']
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Handler pliku (jeśli włączony w konfiguracji)
        if self.config['file_output']:
            # Nazwa pliku z datą
            log_file = self.log_dir / f"city_builder_{datetime.now().strftime('%Y%m%d')}.log"
            
            # RotatingFileHandler automatycznie rotuje pliki gdy osiągną maksymalny rozmiar
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count'],
                encoding='utf-8'  # kodowanie UTF-8 dla polskich znaków
            )
            
            # Formatter dla pliku (bez kolorów)
            file_formatter = logging.Formatter(
                self.config['format'],
                datefmt=self.config['date_format']
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def _setup_game_loggers(self):
        """
        Konfiguruje specjalistyczne loggery dla różnych modułów gry.
        
        Każdy moduł ma własny plik logów z odpowiednim poziomem szczegółowości.
        """
        # Konfiguracja loggerów dla różnych modułów
        logger_configs = {
            'game_engine': {'level': 'INFO', 'file': 'game_engine.log'},      # silnik gry
            'ui': {'level': 'WARNING', 'file': 'ui.log'},                     # interfejs użytkownika
            'database': {'level': 'INFO', 'file': 'database.log'},            # baza danych
            'events': {'level': 'INFO', 'file': 'events.log'},                # wydarzenia w grze
            'trade': {'level': 'INFO', 'file': 'trade.log'},                  # handel
            'achievements': {'level': 'INFO', 'file': 'achievements.log'},    # osiągnięcia
            'performance': {'level': 'DEBUG', 'file': 'performance.log'},     # wydajność
            'errors': {'level': 'ERROR', 'file': 'errors.log'}                # błędy
        }
        
        # Utwórz logger dla każdego modułu
        for logger_name, config in logger_configs.items():
            logger = logging.getLogger(f'city_builder.{logger_name}')
            logger.setLevel(getattr(logging, config['level']))
            
            # Dodaj handler pliku dla każdego loggera
            log_file = self.log_dir / config['file']
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_file_size'] // 2,  # mniejsze pliki dla modułów
                backupCount=3,                               # mniej backupów
                encoding='utf-8'
            )
            
            # Prostszy format dla loggerów modułów
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # Zapisz logger w słowniku
            self.loggers[logger_name] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Zwraca logger o podanej nazwie.
        
        Args:
            name: Nazwa loggera
            
        Returns:
            Logger instance
        """
        if name in self.loggers:
            return self.loggers[name]
        return logging.getLogger(f'city_builder.{name}')
    
    def set_level(self, level: str) -> bool:
        """
        Ustawia poziom logowania.
        
        Args:
            level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            True jeśli ustawiono pomyślnie
        """
        if not self.level_validator.match(level):
            return False
        
        try:
            logging.getLogger().setLevel(getattr(logging, level))
            self.config['level'] = level
            return True
        except AttributeError:
            return False
    
    def log_game_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """
        Loguje wydarzenie w grze.
        
        Args:
            event_type: Typ wydarzenia
            message: Wiadomość
            data: Dodatkowe dane
        """
        logger = self.get_logger('events')
        log_message = f"[{event_type}] {message}"
        
        if data:
            # Użyj funkcji wyższego rzędu do formatowania danych
            formatted_data = list(map(lambda item: f"{item[0]}={item[1]}", data.items()))
            log_message += f" | Data: {', '.join(formatted_data)}"
        
        logger.info(log_message)
    
    def log_performance(self, operation: str, duration: float, details: Optional[Dict] = None):
        """
        Loguje informacje o wydajności.
        
        Args:
            operation: Nazwa operacji
            duration: Czas trwania w sekundach
            details: Dodatkowe szczegóły
        """
        logger = self.get_logger('performance')
        message = f"Operation '{operation}' took {duration:.4f}s"
        
        if details:
            detail_strings = list(map(lambda x: f"{x[0]}={x[1]}", details.items()))
            message += f" | {', '.join(detail_strings)}"
        
        logger.debug(message)
    
    def log_error(self, error: Exception, context: str = "", additional_info: Optional[Dict] = None):
        """
        Loguje błąd z kontekstem.
        
        Args:
            error: Wyjątek
            context: Kontekst błędu
            additional_info: Dodatkowe informacje
        """
        logger = self.get_logger('errors')
        message = f"Error in {context}: {str(error)}"
        
        if additional_info:
            info_strings = list(map(lambda x: f"{x[0]}={x[1]}", additional_info.items()))
            message += f" | Info: {', '.join(info_strings)}"
        
        logger.error(message, exc_info=True)
    
    def analyze_logs(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Analizuje logi używając wyrażeń regularnych.
        
        Args:
            log_file: Ścieżka do pliku logów (domyślnie najnowszy)
            
        Returns:
            Statystyki logów
        """
        if not log_file:
            # Znajdź najnowszy plik logów
            log_files = list(self.log_dir.glob("city_builder_*.log"))
            if not log_files:
                return {}
            log_file = max(log_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex patterns dla analizy
            patterns = {
                'errors': re.compile(r'ERROR.*', re.MULTILINE),
                'warnings': re.compile(r'WARNING.*', re.MULTILINE),
                'game_events': re.compile(r'\[(\w+)\].*', re.MULTILINE),
                'performance': re.compile(r'Operation \'(\w+)\' took ([\d.]+)s', re.MULTILINE),
                'timestamps': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', re.MULTILINE)
            }
            
            stats = {}
            
            # Zlicz błędy i ostrzeżenia
            stats['error_count'] = len(patterns['errors'].findall(content))
            stats['warning_count'] = len(patterns['warnings'].findall(content))
            
            # Analizuj wydarzenia gry
            game_events = patterns['game_events'].findall(content)
            event_counts = {}
            for event in game_events:
                event_counts[event] = event_counts.get(event, 0) + 1
            stats['event_counts'] = event_counts
            
            # Analizuj wydajność
            performance_data = patterns['performance'].findall(content)
            if performance_data:
                # Użyj reduce do obliczenia średniego czasu
                times = list(map(lambda x: float(x[1]), performance_data))
                avg_time = reduce(lambda a, b: a + b, times) / len(times)
                stats['average_operation_time'] = avg_time
                
                # Grupuj operacje
                operations = {}
                for op, time in performance_data:
                    if op not in operations:
                        operations[op] = []
                    operations[op].append(float(time))
                
                # Oblicz statystyki dla każdej operacji
                for op, times in operations.items():
                    avg = reduce(lambda a, b: a + b, times) / len(times)
                    operations[op] = {
                        'count': len(times),
                        'average_time': avg,
                        'total_time': reduce(lambda a, b: a + b, times)
                    }
                
                stats['operations'] = operations
            
            # Analizuj aktywność w czasie
            timestamps = patterns['timestamps'].findall(content)
            if timestamps:
                stats['log_entries'] = len(timestamps)
                stats['first_entry'] = timestamps[0] if timestamps else None
                stats['last_entry'] = timestamps[-1] if timestamps else None
            
            return stats
            
        except Exception as e:
            logging.error(f"Błąd analizy logów: {e}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Usuwa stare pliki logów.
        
        Args:
            days_to_keep: Liczba dni do zachowania
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Znajdź stare pliki logów używając regex
            log_pattern = re.compile(r'city_builder_(\d{8})\.log')
            
            for log_file in self.log_dir.glob("*.log"):
                match = log_pattern.match(log_file.name)
                if match:
                    date_str = match.group(1)
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logging.info(f"Usunięto stary plik logów: {log_file.name}")
            
        except Exception as e:
            logging.error(f"Błąd czyszczenia logów: {e}")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie logów."""
        try:
            log_files = list(self.log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)
            
            return {
                'log_files_count': len(log_files),
                'total_size_mb': total_size / (1024 * 1024),
                'log_directory': str(self.log_dir),
                'current_level': self.config['level'],
                'active_loggers': list(self.loggers.keys())
            }
        except Exception as e:
            logging.error(f"Błąd pobierania podsumowania logów: {e}")
            return {}


# Singleton instance
_game_logger = None

def get_game_logger() -> GameLogger:
    """Zwraca singleton instancję GameLogger."""
    global _game_logger
    if _game_logger is None:
        _game_logger = GameLogger()
    return _game_logger

def setup_logging(config: Optional[Dict[str, Any]] = None):
    """Konfiguruje system logowania."""
    global _game_logger
    _game_logger = GameLogger(config=config) 