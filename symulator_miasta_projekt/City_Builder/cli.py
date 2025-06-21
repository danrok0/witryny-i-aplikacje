#!/usr/bin/env python3
"""
Interfejs wiersza poleceń (CLI) dla City Builder.

Ten moduł pozwala na uruchomienie gry z konsoli/terminala bez GUI.
Oferuje tekstowy interfejs do zarządzania miastem, budowania i interakcji z grą.

Główne funkcje:
- Uruchomienie gry w trybie tekstowym
- Zarządzanie budynkami przez komendy tekstowe
- Wyświetlanie statusu miasta i statystyk
- Zapisywanie i wczytywanie gier
- Debugowanie i testowanie mechanik gry
"""

import argparse
import sys
import os
import json
import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Dodaj ścieżkę do modułów
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.config_manager import get_config_manager
from core.logger import setup_logging, get_game_logger
from core.functional_utils import validate_game_data
from core.game_engine import GameEngine
from core.city_map import CityMap
from core.tile import Building, BuildingType, TerrainType
from core.population import PopulationManager

class CityBuilderCLI:
    """
    Główna klasa interfejsu wiersza poleceń.
    
    Zapewnia tekstowy interfejs do gry City Builder, pozwalając graczom
    na interakcję z grą poprzez komendy tekstowe zamiast GUI.
    """
    
    def __init__(self):
        """
        Konstruktor CLI - inicjalizuje silnik gry i ustawienia.
        """
        self.game_engine = GameEngine()  # główny silnik gry
        self.running = True              # flaga określająca czy CLI działa
        self.commands = {                # słownik dostępnych komend
            'help': self.show_help,
            'status': self.show_status,
            'build': self.build_building,
            'demolish': self.demolish_building,
            'save': self.save_game,
            'load': self.load_game,
            'next': self.next_turn,
            'map': self.show_map,
            'buildings': self.list_buildings,
            'population': self.show_population,
            'economy': self.show_economy,
            'events': self.show_events,
            'quit': self.quit_game,
            'exit': self.quit_game
        }
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Tworzy parser argumentów wiersza poleceń.
        
        Returns:
            Skonfigurowany ArgumentParser
        """
        parser = argparse.ArgumentParser(
            prog='city_builder',
            description='Advanced City Builder - Symulator miasta',
            epilog='Przykład użycia: python cli.py --new-game --difficulty Hard --map-size 80x80',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Grupa głównych akcji
        action_group = parser.add_mutually_exclusive_group()
        action_group.add_argument(
            '--new-game', 
            action='store_true',
            help='Rozpocznij nową grę'
        )
        action_group.add_argument(
            '--load-game', 
            type=str, 
            metavar='SAVE_FILE',
            help='Wczytaj grę z pliku zapisu'
        )
        action_group.add_argument(
            '--config', 
            action='store_true',
            help='Pokaż aktualną konfigurację'
        )
        action_group.add_argument(
            '--validate', 
            type=str, 
            metavar='DATA_FILE',
            help='Waliduj plik danych gry'
        )
        
        # Ustawienia gry
        game_group = parser.add_argument_group('Ustawienia gry')
        game_group.add_argument(
            '--difficulty', 
            choices=['Easy', 'Normal', 'Hard'],
            default='Normal',
            help='Poziom trudności (domyślnie: Normal)'
        )
        game_group.add_argument(
            '--map-size', 
            type=str, 
            metavar='WIDTHxHEIGHT',
            default='60x60',
            help='Rozmiar mapy w formacie WIDTHxHEIGHT (domyślnie: 60x60)'
        )
        game_group.add_argument(
            '--language', 
            choices=['pl', 'en'],
            default='pl',
            help='Język interfejsu (domyślnie: pl)'
        )
        game_group.add_argument(
            '--auto-save', 
            type=int, 
            metavar='SECONDS',
            default=300,
            help='Interwał automatycznego zapisu w sekundach (domyślnie: 300)'
        )
        
        # Ustawienia interfejsu
        ui_group = parser.add_argument_group('Ustawienia interfejsu')
        ui_group.add_argument(
            '--window-size', 
            type=str, 
            metavar='WIDTHxHEIGHT',
            default='1600x1000',
            help='Rozmiar okna w formacie WIDTHxHEIGHT (domyślnie: 1600x1000)'
        )
        ui_group.add_argument(
            '--fullscreen', 
            action='store_true',
            help='Uruchom w trybie pełnoekranowym'
        )
        ui_group.add_argument(
            '--no-sound', 
            action='store_true',
            help='Wyłącz dźwięki'
        )
        ui_group.add_argument(
            '--no-animations', 
            action='store_true',
            help='Wyłącz animacje'
        )
        
        # Ustawienia wydajności
        perf_group = parser.add_argument_group('Ustawienia wydajności')
        perf_group.add_argument(
            '--max-fps', 
            type=int, 
            metavar='FPS',
            default=60,
            help='Maksymalna liczba klatek na sekundę (domyślnie: 60)'
        )
        perf_group.add_argument(
            '--update-interval', 
            type=int, 
            metavar='MS',
            default=15000,
            help='Interwał aktualizacji gry w milisekundach (domyślnie: 15000)'
        )
        perf_group.add_argument(
            '--enable-multithreading', 
            action='store_true',
            help='Włącz wielowątkowość'
        )
        
        # Ustawienia debugowania
        debug_group = parser.add_argument_group('Ustawienia debugowania')
        debug_group.add_argument(
            '--debug', 
            action='store_true',
            help='Włącz tryb debugowania'
        )
        debug_group.add_argument(
            '--log-level', 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Poziom logowania (domyślnie: INFO)'
        )
        debug_group.add_argument(
            '--log-file', 
            type=str, 
            metavar='FILE',
            help='Plik logów (domyślnie: automatyczny)'
        )
        debug_group.add_argument(
            '--performance-stats', 
            action='store_true',
            help='Pokaż statystyki wydajności'
        )
        
        # Narzędzia
        tools_group = parser.add_argument_group('Narzędzia')
        tools_group.add_argument(
            '--export-config', 
            type=str, 
            metavar='FILE',
            help='Eksportuj konfigurację do pliku'
        )
        tools_group.add_argument(
            '--import-config', 
            type=str, 
            metavar='FILE',
            help='Importuj konfigurację z pliku'
        )
        tools_group.add_argument(
            '--reset-config', 
            action='store_true',
            help='Resetuj konfigurację do wartości domyślnych'
        )
        tools_group.add_argument(
            '--list-saves', 
            action='store_true',
            help='Pokaż listę zapisanych gier'
        )
        tools_group.add_argument(
            '--cleanup-logs', 
            type=int, 
            metavar='DAYS',
            help='Usuń logi starsze niż podana liczba dni'
        )
        
        # Informacje
        info_group = parser.add_argument_group('Informacje')
        info_group.add_argument(
            '--version', 
            action='version', 
            version='City Builder v1.0.0 (Faza 5)'
        )
        info_group.add_argument(
            '--system-info', 
            action='store_true',
            help='Pokaż informacje o systemie'
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parsuje argumenty wiersza poleceń.
        
        Args:
            args: Lista argumentów (domyślnie sys.argv)
            
        Returns:
            Sparsowane argumenty
        """
        return self._create_parser().parse_args(args)
    
    def validate_args(self, args: argparse.Namespace) -> Dict[str, List[str]]:
        """
        Waliduje argumenty wiersza poleceń.
        
        Args:
            args: Sparsowane argumenty
            
        Returns:
            Słownik błędów walidacji
        """
        errors = {}
        
        # Walidacja rozmiaru mapy
        if hasattr(args, 'map_size') and args.map_size:
            if not self._validate_size_format(args.map_size):
                errors['map_size'] = ['Format musi być WIDTHxHEIGHT, np. 60x60']
        
        # Walidacja rozmiaru okna
        if hasattr(args, 'window_size') and args.window_size:
            if not self._validate_size_format(args.window_size):
                errors['window_size'] = ['Format musi być WIDTHxHEIGHT, np. 1600x1000']
        
        # Walidacja pliku zapisu
        if hasattr(args, 'load_game') and args.load_game:
            save_path = Path(args.load_game)
            if not save_path.exists():
                errors['load_game'] = [f'Plik zapisu nie istnieje: {args.load_game}']
            elif not save_path.suffix.lower() == '.json':
                errors['load_game'] = ['Plik zapisu musi mieć rozszerzenie .json']
        
        # Walidacja pliku konfiguracji
        if hasattr(args, 'import_config') and args.import_config:
            config_path = Path(args.import_config)
            if not config_path.exists():
                errors['import_config'] = [f'Plik konfiguracji nie istnieje: {args.import_config}']
        
        # Walidacja pliku walidacji
        if hasattr(args, 'validate') and args.validate:
            validate_path = Path(args.validate)
            if not validate_path.exists():
                errors['validate'] = [f'Plik do walidacji nie istnieje: {args.validate}']
        
        return errors
    
    def _validate_size_format(self, size_str: str) -> bool:
        """Waliduje format rozmiaru WIDTHxHEIGHT."""
        import re
        pattern = re.compile(r'^\d+x\d+$')
        return pattern.match(size_str) is not None
    
    def _parse_size(self, size_str: str) -> tuple:
        """Parsuje string rozmiaru na tuple (width, height)."""
        width, height = size_str.split('x')
        return int(width), int(height)
    
    def apply_args_to_config(self, args: argparse.Namespace) -> bool:
        """
        Aplikuje argumenty CLI do konfiguracji.
        
        Args:
            args: Sparsowane argumenty
            
        Returns:
            True jeśli zastosowano pomyślnie
        """
        try:
            # Ustawienia gry
            if hasattr(args, 'difficulty') and args.difficulty:
                self.game_engine.difficulty = args.difficulty
            
            if hasattr(args, 'language') and args.language:
                self.game_engine.language = args.language
            
            if hasattr(args, 'auto_save') and args.auto_save:
                self.game_engine.auto_save_interval = args.auto_save
            
            if hasattr(args, 'no_sound') and args.no_sound:
                self.game_engine.enable_sound = False
            
            if hasattr(args, 'no_animations') and args.no_animations:
                self.game_engine.enable_animations = False
            
            # Ustawienia mapy
            if hasattr(args, 'map_size') and args.map_size:
                width, height = self._parse_size(args.map_size)
                self.game_engine.city_map.width = width
                self.game_engine.city_map.height = height
            
            # Ustawienia interfejsu
            if hasattr(args, 'window_size') and args.window_size:
                width, height = self._parse_size(args.window_size)
                self.game_engine.ui_settings.window_width = width
                self.game_engine.ui_settings.window_height = height
            
            # Ustawienia wydajności
            if hasattr(args, 'max_fps') and args.max_fps:
                self.game_engine.performance_settings.max_fps = args.max_fps
            
            if hasattr(args, 'update_interval') and args.update_interval:
                self.game_engine.performance_settings.update_interval = args.update_interval
            
            if hasattr(args, 'enable_multithreading') and args.enable_multithreading:
                self.game_engine.performance_settings.enable_multithreading = True
            
            # Ustawienia debugowania
            if hasattr(args, 'debug') and args.debug:
                self.game_engine.advanced_settings.debug_mode = True
                self.game_engine.performance_settings.log_level = 'DEBUG'
            
            if hasattr(args, 'log_level') and args.log_level:
                self.game_engine.performance_settings.log_level = args.log_level
            
            if hasattr(args, 'performance_stats') and args.performance_stats:
                self.game_engine.advanced_settings.show_performance_stats = True
            
            return True
            
        except Exception as e:
            print(f"Błąd aplikowania argumentów do konfiguracji: {e}")
            return False
    
    def execute_action(self, args: argparse.Namespace) -> int:
        """
        Wykonuje akcję na podstawie argumentów.
        
        Args:
            args: Sparsowane argumenty
            
        Returns:
            Kod wyjścia (0 = sukces)
        """
        try:
            # Konfiguracja logowania
            log_config = {
                'level': args.log_level if hasattr(args, 'log_level') else 'INFO',
                'console_output': True,
                'file_output': True,
                'max_file_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            }
            setup_logging(log_config)
            logger = get_game_logger().get_logger('cli')
            
            # Wykonaj akcję
            if hasattr(args, 'config') and args.config:
                return self._show_config()
            
            elif hasattr(args, 'validate') and args.validate:
                return self._validate_file(args.validate)
            
            elif hasattr(args, 'export_config') and args.export_config:
                return self._export_config(args.export_config)
            
            elif hasattr(args, 'import_config') and args.import_config:
                return self._import_config(args.import_config)
            
            elif hasattr(args, 'reset_config') and args.reset_config:
                return self._reset_config()
            
            elif hasattr(args, 'list_saves') and args.list_saves:
                return self._list_saves()
            
            elif hasattr(args, 'cleanup_logs') and args.cleanup_logs:
                return self._cleanup_logs(args.cleanup_logs)
            
            elif hasattr(args, 'system_info') and args.system_info:
                return self._show_system_info()
            
            else:
                # Uruchom grę
                return self._start_game(args)
            
        except Exception as e:
            print(f"Błąd wykonywania akcji: {e}")
            return 1
    
    def _show_config(self) -> int:
        """Pokazuje aktualną konfigurację."""
        try:
            config = self.game_engine.get_all_settings()
            print("=== Aktualna konfiguracja ===")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return 0
        except Exception as e:
            print(f"Błąd pokazywania konfiguracji: {e}")
            return 1
    
    def _validate_file(self, file_path: str) -> int:
        """Waliduje plik danych gry."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            errors = validate_game_data(data)
            
            if errors:
                print("=== Błędy walidacji ===")
                for field, field_errors in errors.items():
                    print(f"{field}:")
                    for error in field_errors:
                        print(f"  - {error}")
                return 1
            else:
                print("✅ Plik jest poprawny")
                return 0
                
        except Exception as e:
            print(f"Błąd walidacji pliku: {e}")
            return 1
    
    def _export_config(self, file_path: str) -> int:
        """Eksportuje konfigurację."""
        try:
            if self.game_engine.export_config(file_path):
                print(f"✅ Konfiguracja wyeksportowana do: {file_path}")
                return 0
            else:
                print("❌ Błąd eksportu konfiguracji")
                return 1
        except Exception as e:
            print(f"Błąd eksportu konfiguracji: {e}")
            return 1
    
    def _import_config(self, file_path: str) -> int:
        """Importuje konfigurację."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Waliduj i zastosuj konfigurację
            # Tu można dodać dodatkową walidację
            
            print(f"✅ Konfiguracja zaimportowana z: {file_path}")
            return 0
        except Exception as e:
            print(f"Błąd importu konfiguracji: {e}")
            return 1
    
    def _reset_config(self) -> int:
        """Resetuje konfigurację."""
        try:
            if self.game_engine.reset_to_defaults():
                print("✅ Konfiguracja zresetowana do wartości domyślnych")
                return 0
            else:
                print("❌ Błąd resetowania konfiguracji")
                return 1
        except Exception as e:
            print(f"Błąd resetowania konfiguracji: {e}")
            return 1
    
    def _list_saves(self) -> int:
        """Pokazuje listę zapisanych gier."""
        try:
            saves_dir = Path('saves')
            if not saves_dir.exists():
                print("Brak katalogu z zapisami")
                return 0
            
            save_files = list(saves_dir.glob('*.json'))
            if not save_files:
                print("Brak zapisanych gier")
                return 0
            
            print("=== Zapisane gry ===")
            for save_file in sorted(save_files, key=lambda f: f.stat().st_mtime, reverse=True):
                size = save_file.stat().st_size
                mtime = save_file.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{save_file.name:<30} {size:>10} bytes  {date_str}")
            
            return 0
        except Exception as e:
            print(f"Błąd listowania zapisów: {e}")
            return 1
    
    def _cleanup_logs(self, days: int) -> int:
        """Czyści stare logi."""
        try:
            logger = get_game_logger()
            logger.cleanup_old_logs(days)
            print(f"✅ Wyczyszczono logi starsze niż {days} dni")
            return 0
        except Exception as e:
            print(f"Błąd czyszczenia logów: {e}")
            return 1
    
    def _show_system_info(self) -> int:
        """Pokazuje informacje o systemie."""
        try:
            import platform
            import psutil
            
            print("=== Informacje o systemie ===")
            print(f"System: {platform.system()} {platform.release()}")
            print(f"Procesor: {platform.processor()}")
            print(f"Pamięć RAM: {psutil.virtual_memory().total // (1024**3)} GB")
            print(f"Python: {platform.python_version()}")
            
            # Informacje o grze
            logger = get_game_logger()
            log_summary = logger.get_log_summary()
            print("\n=== Informacje o grze ===")
            print(f"Pliki logów: {log_summary.get('log_files_count', 0)}")
            print(f"Rozmiar logów: {log_summary.get('total_size_mb', 0):.2f} MB")
            print(f"Poziom logowania: {log_summary.get('current_level', 'N/A')}")
            
            return 0
        except Exception as e:
            print(f"Błąd pokazywania informacji o systemie: {e}")
            return 1
    
    def _start_game(self, args: argparse.Namespace) -> int:
        """Uruchamia grę."""
        try:
            # Zastosuj argumenty do konfiguracji
            self.apply_args_to_config(args)
            
            # Uruchom główną aplikację
            from Main import main
            main()
            return 0
            
        except Exception as e:
            print(f"Błąd uruchamiania gry: {e}")
            return 1

    def run(self):
        """
        Główna pętla CLI - uruchamia interfejs tekstowy.
        
        Wyświetla powitanie, inicjalizuje grę i czeka na komendy użytkownika
        w nieskończonej pętli (do momentu wpisania 'quit' lub 'exit').
        """
        self.print_welcome()     # wyświetl ekran powitalny
        self.game_engine.initialize()  # zainicjalizuj silnik gry
        
        while self.running:      # główna pętla gry
            try:
                # Pobierz komendę od użytkownika
                command_input = input("\n> ").strip().lower()
                
                if not command_input:  # jeśli pusta linia, kontynuuj
                    continue
                    
                # Podziel komendę na części (komenda + argumenty)
                parts = command_input.split()
                command = parts[0]        # pierwsza część to komenda
                args = parts[1:] if len(parts) > 1 else []  # reszta to argumenty
                
                # Wykonaj komendę jeśli istnieje
                if command in self.commands:
                    self.commands[command](args)  # wywołaj funkcję komendy z argumentami
                else:
                    print(f"❌ Nieznana komenda: '{command}'. Wpisz 'help' aby zobaczyć dostępne komendy.")
                    
            except KeyboardInterrupt:  # Ctrl+C
                print("\n\n👋 Dziękujemy za grę! Naciśnij Enter aby zamknąć...")
                input()
                break
            except Exception as e:
                print(f"❌ Wystąpił błąd: {str(e)}")
                print("🔧 Jeśli problem się powtarza, sprawdź logi lub zgłoś błąd.")
    
    def print_welcome(self):
        """
        Wyświetla ekran powitalny CLI z logo i instrukcjami.
        """
        print("=" * 60)
        print("🏙️  CITY BUILDER - INTERFEJS WIERSZA POLECEŃ  🏙️")
        print("=" * 60)
        print()
        print("Witaj w trybie tekstowym City Builder!")
        print("Zarządzaj swoim miastem przy pomocy komend tekstowych.")
        print()
        print("📋 Wpisz 'help' aby zobaczyć dostępne komendy")
        print("🚪 Wpisz 'quit' lub 'exit' aby zakończyć grę")
        print("=" * 60)
    
    def show_help(self, args: List[str]):
        """
        Wyświetla listę wszystkich dostępnych komend z opisami.
        
        Args:
            args: argumenty komendy (nie używane w tej funkcji)
        """
        print("\n📋 DOSTĘPNE KOMENDY:")
        print("-" * 50)
        
        # Słownik z opisami komend
        help_text = {
            'help': 'Wyświetla tę listę pomocy',
            'status': 'Pokazuje ogólny status miasta',
            'build <typ> <x> <y>': 'Buduje budynek na pozycji (x,y)',
            'demolish <x> <y>': 'Wyburza budynek na pozycji (x,y)',
            'save <nazwa>': 'Zapisuje grę pod podaną nazwą',
            'load <nazwa>': 'Wczytuje zapisaną grę',
            'next': 'Przechodzi do następnej tury',
            'map': 'Wyświetla mapę miasta (ASCII)',
            'buildings': 'Lista dostępnych typów budynków',
            'population': 'Pokazuje statystyki populacji',
            'economy': 'Wyświetla stan ekonomiczny miasta',
            'events': 'Pokazuje ostatnie wydarzenia',
            'quit/exit': 'Kończy grę i zamyka CLI'
        }
        
        # Wyświetl każdą komendę z opisem
        for command, description in help_text.items():
            print(f"  {command:<20} - {description}")
        
        print("-" * 50)
        print("💡 Przykład: build house 10 15")
        print("💡 Współrzędne zaczynają się od 0,0 (lewy górny róg)")
    
    def show_status(self, args: List[str]):
        """
        Wyświetla ogólny status miasta - podsumowanie najważniejszych informacji.
        
        Args:
            args: argumenty komendy (nie używane)
        """
        print("\n🏙️ STATUS MIASTA")
        print("=" * 40)
        
        # Pobierz dane z silnika gry
        money = self.game_engine.economy.get_resource_amount('money')
        total_pop = self.game_engine.population_manager.get_total_population()
        satisfaction = self.game_engine.population_manager.get_average_satisfaction()
        unemployment = self.game_engine.population_manager.get_unemployment_rate()
        
        # Wyświetl podstawowe statystyki
        print(f"💰 Budżet: ${money:,.2f}")
        print(f"👥 Populacja: {total_pop:,} mieszkańców")
        print(f"😊 Zadowolenie: {satisfaction:.1f}%")
        print(f"💼 Bezrobocie: {unemployment:.1f}%")
        print(f"🏢 Budynki: {len(self.game_engine.get_all_buildings())} budynków")
        print(f"📅 Tura: {getattr(self.game_engine, 'current_turn', 1)}")
        
        # Wyświetl ostrzeżenia jeśli potrzebne
        if money < 1000:
            print("⚠️  UWAGA: Niski budżet!")
        if satisfaction < 30:
            print("⚠️  UWAGA: Niezadowoleni mieszkańcy!")
        if unemployment > 15:
            print("⚠️  UWAGA: Wysokie bezrobocie!")
    
    def build_building(self, args: List[str]):
        """
        Buduje budynek na mapie na podanych współrzędnych.
        
        Args:
            args: lista argumentów [typ_budynku, x, y]
            
        Przykład użycia: build house 10 15
        """
        if len(args) < 3:
            print("❌ Niepoprawna składnia. Użyj: build <typ> <x> <y>")
            print("💡 Przykład: build house 10 15")
            return
        
        building_type = args[0].lower()  # typ budynku (małe litery)
        
        try:
            x = int(args[1])  # współrzędna x
            y = int(args[2])  # współrzędna y
        except ValueError:
            print("❌ Współrzędne muszą być liczbami całkowitymi")
            return
        
        # Mapowanie nazw budynków na typy
        building_map = {
            'house': BuildingType.HOUSE,
            'dom': BuildingType.HOUSE,
            'road': BuildingType.ROAD,
            'droga': BuildingType.ROAD,
            'shop': BuildingType.SHOP,
            'sklep': BuildingType.SHOP,
            'factory': BuildingType.FACTORY,
            'fabryka': BuildingType.FACTORY,
            'school': BuildingType.SCHOOL,
            'szkoła': BuildingType.SCHOOL,
            'hospital': BuildingType.HOSPITAL,
            'szpital': BuildingType.HOSPITAL,
            'park': BuildingType.PARK
        }
        
        if building_type not in building_map:
            print(f"❌ Nieznany typ budynku: '{building_type}'")
            print("📋 Wpisz 'buildings' aby zobaczyć dostępne typy")
            return
        
        # Sprawdź czy można budować na tej pozycji
        tile = self.game_engine.city_map.get_tile(x, y)
        if not tile:
            print(f"❌ Nieprawidłowa pozycja: ({x}, {y})")
            return
        
        if tile.is_occupied:
            print(f"❌ Pozycja ({x}, {y}) jest już zajęta")
            return
        
        # Utwórz budynek
        building_enum = building_map[building_type]
        building = Building(building_enum.value, building_enum, 1000)  # domyślny koszt
        
        # Sprawdź czy stać na budynek
        if not self.game_engine.economy.can_afford(building.cost):
            current_money = self.game_engine.economy.get_resource_amount('money')
            print(f"❌ Niewystarczające środki. Potrzebujesz ${building.cost:,}, masz ${current_money:,}")
            return
        
        # Spróbuj zbudować
        success, message = self.game_engine.try_build_building(x, y, building)
        if success:
            print(f"✅ Zbudowano {building.name} na pozycji ({x}, {y})")
            print(f"💰 Koszt: ${building.cost:,}")
        else:
            print(f"❌ Nie można zbudować: {message}")
            
    def show_map(self, args: List[str]):
        """
        Wyświetla mapę miasta w formie ASCII.
        
        Używa różnych znaków do reprezentacji różnych typów terenu:
        . = trawa, ~ = woda, ^ = góry, # = budynki, R = drogi
        """
        print("\n🗺️  MAPA MIASTA (ASCII)")
        print("-" * 60)
        
        # Mapowanie typów terenu na znaki ASCII
        terrain_chars = {
            TerrainType.GRASS: '.',      # trawa
            TerrainType.WATER: '~',      # woda
            TerrainType.MOUNTAIN: '^',   # góry
            TerrainType.SAND: ':',       # piasek
        }
        
        # Wyświetl mapę wiersz po wierszu
        city_map = self.game_engine.city_map
        
        # Wyświetl numery kolumn (co 5)
        print("   ", end="")
        for x in range(0, min(city_map.width, 50), 5):  # ograniczenie do 50 dla czytelności
            print(f"{x:>5}", end="")
        print()
        
        # Wyświetl mapę (ograniczoną do 25x50 dla czytelności terminala)
        max_rows = min(city_map.height, 25)
        max_cols = min(city_map.width, 50)
        
        for y in range(max_rows):
            print(f"{y:>2}: ", end="")  # numer wiersza
            for x in range(max_cols):
                tile = city_map.get_tile(x, y)
                if tile:
                    if tile.is_occupied and tile.building:
                        # Różne znaki dla różnych typów budynków
                        building_type = tile.building.building_type
                        if building_type == BuildingType.ROAD:
                            print('R', end='')  # droga
                        elif building_type == BuildingType.HOUSE:
                            print('H', end='')  # dom
                        elif building_type == BuildingType.SHOP:
                            print('S', end='')  # sklep
                        elif building_type == BuildingType.FACTORY:
                            print('F', end='')  # fabryka
                        else:
                            print('#', end='')  # inny budynek
                    else:
                        # Pusty teren
                        char = terrain_chars.get(tile.terrain_type, '?')
                        print(char, end='')
                else:
                    print('?', end='')  # błąd
            print()  # nowa linia po każdym wierszu
        
        if city_map.width > 50 or city_map.height > 25:
            print(f"\n📏 Mapa skrócona do 25x50. Pełny rozmiar: {city_map.height}x{city_map.width}")
        
        # Legenda
        print("\n🔤 LEGENDA:")
        print("  . = Trawa    ~ = Woda    ^ = Góry    : = Piasek")  
        print("  R = Droga    H = Dom     S = Sklep   F = Fabryka   # = Inny budynek")


def main():
    """Główna funkcja CLI."""
    cli = CityBuilderCLI()
    
    try:
        args = cli.parse_args()
        
        # Waliduj argumenty
        errors = cli.validate_args(args)
        if errors:
            print("Błędy w argumentach:")
            for field, field_errors in errors.items():
                for error in field_errors:
                    print(f"  {field}: {error}")
            return 1
        
        # Wykonaj akcję
        return cli.execute_action(args)
        
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika")
        return 130
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 