import sys
import os
import logging
import time

# Dodaj aktualny katalog do ścieżki Pythona
# os.path.dirname() - pobiera katalog z pełnej ścieżki pliku
# os.path.abspath() - konwertuje względną ścieżkę na bezwzględną
# __file__ - specjalna zmienna zawierająca ścieżkę do aktualnego pliku
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:    # sprawdź czy katalog nie jest już w ścieżce
    sys.path.append(current_dir)   # dodaj katalog do sys.path aby Python mógł importować moduły

# Inicjalizuj systemy konfiguracji i logowania
from core.config_manager import get_config_manager
from core.logger import setup_logging, get_game_logger
from core.functional_utils import performance_monitor, safe_map, safe_filter

# Konfiguruj system logowania (zapisywania zdarzeń do plików)
config_manager = get_config_manager()  # pobierz menedżer konfiguracji
log_config = {
    # Pobierz poziom logowania z konfiguracji (domyślnie INFO)
    'level': config_manager.get('advanced_settings.log_level', 'INFO'),
    'console_output': True,                                    # wyświetlaj logi w konsoli
    'file_output': True,                                       # zapisuj logi do pliku
    'max_file_size': 10 * 1024 * 1024,                       # maksymalny rozmiar pliku (10MB)
    'backup_count': 5,                                         # liczba plików kopii zapasowych
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # format wiadomości
    'date_format': '%Y-%m-%d %H:%M:%S'                        # format daty i czasu
}
setup_logging(log_config)
game_logger = get_game_logger()

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QMenuBar, QStatusBar, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QTimer
from core.game_engine import GameEngine
from gui.map_canvas import MapCanvas
from gui.build_panel import BuildPanel
from core.events import EventManager
from gui.event_dialog import EventDialog
from gui.reports_panel import ReportsPanel
from core.technology import TechnologyManager
from gui.technology_panel import TechnologyPanel
from db.database import Database
from core.objectives import ObjectiveManager
from gui.objectives_panel import ObjectivesPanel
from gui.finance_panel import FinancePanel
from gui.scenarios_panel import ScenariosPanel

# Włącz skalowanie dla ekranów wysokiej rozdzielczości (4K, Retina itp.)
# os.environ - słownik zmiennych środowiskowych systemu operacyjnego
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"      # włącz automatyczne skalowanie Qt
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"    # automatycznie dostosuj skalę do ekranu

class MainWindow(QMainWindow):
    """
    Główne okno aplikacji City Builder.
    
    Dziedziczy po QMainWindow - podstawowej klasie okna w PyQt6.
    Zawiera wszystkie elementy interfejsu użytkownika:
    - Canvas z mapą miasta
    - Panel budowania
    - Menu i paski narzędzi
    - System zdarzeń i powiadomień
    """
    
    @performance_monitor  # dekorator monitorujący wydajność - mierzy czas wykonania
    def __init__(self):
        """
        Konstruktor głównego okna aplikacji.
        
        Inicjalizuje wszystkie komponenty interfejsu użytkownika:
        - Okno główne i jego geometrię
        - Silnik gry i ekonomię
        - Canvas z mapą
        - Panele boczne
        - Menu i paski stanu
        - Timery i eventy
        """
        super().__init__()  # wywołaj konstruktor klasy nadrzędnej (QMainWindow)
        
        # Pobierz ustawienia z konfiguracji (config.json)
        # get() zwraca wartość z konfiguracji lub domyślną jeśli klucz nie istnieje
        window_width = config_manager.get('ui_settings.window_width', 1600)      # szerokość okna
        window_height = config_manager.get('ui_settings.window_height', 1000)    # wysokość okna
        map_width = config_manager.get('game_settings.default_map_size.width', 60)   # szerokość mapy
        map_height = config_manager.get('game_settings.default_map_size.height', 60) # wysokość mapy
        
        # Ustaw tytuł okna i jego pozycję/rozmiar
        self.setWindowTitle("City Builder - Advanced City Simulator")
        # setGeometry(x, y, width, height) - pozycja i rozmiar okna
        self.setGeometry(100, 100, window_width, window_height)
        
        # Loguj inicjalizację do systemu logowania
        logger = game_logger.get_logger('ui')    # pobierz logger dla interfejsu użytkownika
        logger.info(f"Inicjalizacja okna głównego {window_width}x{window_height}")
        # Zapisz wydarzenie gry do specjalnego loggera
        game_logger.log_game_event('INIT', 'Uruchomienie aplikacji', {
            'window_size': f"{window_width}x{window_height}",  # rozmiar okna
            'map_size': f"{map_width}x{map_height}"           # rozmiar mapy
        })
        
        # Utwórz silnik gry - główny system zarządzający logiką gry
        self.game_engine = GameEngine(map_width=map_width, map_height=map_height)
        
        # Utwórz główny widget i układ (layout) interfejsu
        central_widget = QWidget()                    # główny widget zawierający wszystkie elementy
        self.setCentralWidget(central_widget)         # ustaw jako centralny widget okna
        main_layout = QHBoxLayout(central_widget)     # poziomy układ (elementy obok siebie)
        
        # Utwórz canvas (płótno) z mapą miasta
        self.map_canvas = MapCanvas(self.game_engine.city_map)  # przekaż mapę z silnika gry
        # Zainicjalizuj zasoby w map_canvas (potrzebne do wyświetlania)
        self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
        # Dodaj canvas do układu z stretch=3 (zajmie 3/5 szerokości okna)
        main_layout.addWidget(self.map_canvas, stretch=3)
        
        # Create build panel
        self.build_panel = BuildPanel(self.game_engine)
        # Initialize resources display
        self.build_panel.update_resources(self.game_engine.economy)
        
        # Initialize economy panel
        buildings = self.game_engine.get_all_buildings()
        income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
        expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
        tax_rates = self.game_engine.economy.tax_rates
        self.build_panel.update_economy_panel(income, expenses, tax_rates)
        
        main_layout.addWidget(self.build_panel, stretch=2)
        
        # Connect signals
        self.build_panel.building_selected.connect(self.map_canvas.select_building)
        self.build_panel.clear_selection.connect(self.on_clear_selection)
        self.map_canvas.building_placed.connect(self.on_building_placed)
        self.build_panel.rotate_btn.clicked.connect(self.map_canvas.rotate_building)
        self.map_canvas.building_sell_requested.connect(self.on_building_sell_requested)
        self.build_panel.sell_building_clicked.connect(self.on_building_sell_button)
        
        # Set focus on map canvas for keyboard events
        self.map_canvas.setFocus()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
        # Game loop timer - wolniejsze aktualizacje
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_game)
        self.game_timer.start(15000)  # Update every 15 seconds
        
        # Create event manager
        self.event_manager = EventManager()
        
        # Create reports panel
        self.reports_panel = ReportsPanel()
        
        # Create technology tree and panel
        self.technology_tree = TechnologyManager()
        self.technology_panel = TechnologyPanel(self.technology_tree, self.game_engine)
        
        # Create database instance
        self.database = Database()
        
        # Create objectives system
        self.objective_manager = ObjectiveManager()
        self.objectives_panel = ObjectivesPanel(self.objective_manager)
        
        # Create finance panel
        self.finance_panel = FinancePanel(self.game_engine.finance_manager)
        self.finance_panel.loan_requested.connect(self.on_loan_requested)
        
        # Create scenarios panel
        self.scenarios_panel = ScenariosPanel(self.game_engine.scenario_manager)
        self.scenarios_panel.scenario_started.connect(self.on_scenario_started)
        
        # Connect objective completion signal
        self.objectives_panel.objective_completed.connect(self.on_objective_completed)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        new_game_action = file_menu.addAction("New Game")
        load_game_action = file_menu.addAction("Load Game")
        save_game_action = file_menu.addAction("Save Game")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        
        # Game menu
        game_menu = menubar.addMenu("Game")
        pause_action = game_menu.addAction("Pause/Resume")
        game_menu.addSeparator()
        
        difficulty_menu = game_menu.addMenu("Difficulty")
        easy_action = difficulty_menu.addAction("Easy")
        normal_action = difficulty_menu.addAction("Normal")
        hard_action = difficulty_menu.addAction("Hard")
        
        # View menu
        view_menu = menubar.addMenu("View")
        reports_action = view_menu.addAction("Reports")
        alerts_action = view_menu.addAction("Alerts")
        finance_action = view_menu.addAction("Finance & Loans")
        scenarios_action = view_menu.addAction("Game Scenarios")
        
        # Technology menu
        technology_action = menubar.addAction("Technologie")
        
        # Objectives menu
        objectives_action = menubar.addAction("Cele")
        
        # Trade menu
        trade_action = menubar.addAction("Handel")
        
        # Achievements menu
        achievements_action = menubar.addAction("Osiągnięcia")
        
        # Diplomacy menu
        diplomacy_action = menubar.addAction("Dyplomacja")
        
        # Connect actions
        exit_action.triggered.connect(self.close)
        new_game_action.triggered.connect(self.new_game)
        save_game_action.triggered.connect(self.save_game)
        load_game_action.triggered.connect(self.load_game)
        pause_action.triggered.connect(self.toggle_pause)
        
        # Difficulty actions
        easy_action.triggered.connect(lambda: self.set_difficulty("Easy"))
        normal_action.triggered.connect(lambda: self.set_difficulty("Normal"))
        hard_action.triggered.connect(lambda: self.set_difficulty("Hard"))
        
        # Reports action
        reports_action.triggered.connect(self.show_reports)
        
        # Alerts action
        alerts_action.triggered.connect(self.show_alerts)
        
        # Finance action
        finance_action.triggered.connect(self.show_finance)
        
        # Scenarios action
        scenarios_action.triggered.connect(self.show_scenarios)
        
        # Technology action
        technology_action.triggered.connect(self.show_technology)
        
        # Objectives action
        objectives_action.triggered.connect(self.show_objectives)
        
        # Trade action
        trade_action.triggered.connect(self.show_trade)
        
        # Achievements action
        achievements_action.triggered.connect(self.show_achievements)
        
        # Diplomacy action
        diplomacy_action.triggered.connect(self.show_diplomacy)
    
    def new_game(self):
        """Start a new game"""
        reply = QMessageBox.question(self, 'New Game', 
                                   'Are you sure you want to start a new game? Current progress will be lost.',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.game_engine = GameEngine(map_width=60, map_height=60)
            self.map_canvas.city_map = self.game_engine.city_map
            self.map_canvas.draw_map()
            
            # Update city level info for new game
            current_pop = self.game_engine.population.get_total_population()
            next_level_pop = self.game_engine.get_next_level_requirement()
            self.build_panel.update_city_level_info(
                self.game_engine.city_level,
                current_pop,
                next_level_pop
            )
            
            # Update other UI elements
            self.build_panel.update_resources(self.game_engine.economy)
            self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
            
            # Update building availability
            self.build_panel.refresh_building_availability()
            
            self.update_status_bar()
    
    def save_game(self):
        """Save current game with validation"""
        from PyQt6.QtWidgets import QInputDialog, QFileDialog
        from core.validation_system import get_validation_system
        import os
        
        # Ensure saves directory exists
        saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
        os.makedirs(saves_dir, exist_ok=True)
        
        validator = get_validation_system()
        
        while True:
            filename, ok = QInputDialog.getText(self, 'Zapisz Grę', 'Podaj nazwę zapisu:')
            if not ok:
                return
            
            if not filename.strip():
                QMessageBox.warning(self, 'Błąd walidacji', 'Nazwa pliku nie może być pusta!')
                continue
            
            # Walidacja nazwy pliku
            validation_result = validator.validate_save_filename(filename)
            
            if not validation_result.is_valid:
                error_msg = "Błędy w nazwie pliku:\n" + "\n".join(validation_result.errors)
                QMessageBox.warning(self, 'Błąd walidacji', error_msg)
                continue
            
            # Użyj oczyszczonej nazwy
            clean_filename = validation_result.cleaned_data
            
            # Add .json extension if not present
            if not clean_filename.endswith('.json'):
                clean_filename += '.json'
            
            # Sprawdzenie czy plik już istnieje
            filepath = os.path.join(saves_dir, clean_filename)
            if os.path.exists(filepath):
                reply = QMessageBox.question(
                    self, 
                    'Plik istnieje', 
                    f'Plik "{clean_filename}" już istnieje. Czy zastąpić?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    continue
            
            # Pokaż ostrzeżenia jeśli są
            if validation_result.warnings:
                warning_msg = "Ostrzeżenia:\n" + "\n".join(validation_result.warnings)
                QMessageBox.information(self, 'Ostrzeżenia', warning_msg)
            
            # Zapisz grę
            success = self.game_engine.save_game(filepath)
            if success:
                QMessageBox.information(self, 'Zapisz Grę', f'Gra zapisana jako {clean_filename}')
            else:
                QMessageBox.warning(self, 'Zapisz Grę', 'Nie udało się zapisać gry')
            
            break
    
    def load_game(self):
        """
        Wczytuje zapisaną grę z walidacją pliku i danych.
        
        Proces wczytywania:
        1. Wybór pliku zapisu przez dialog
        2. Walidacja struktury pliku JSON
        3. Walidacja danych gry
        4. Aktualizacja wszystkich komponentów UI
        5. Reset systemów gry (cele, raporty)
        """
        from PyQt6.QtWidgets import QFileDialog
        from core.validation_system import get_validation_system
        import os
        
        saves_dir = os.path.join(os.path.dirname(__file__), 'saves')
        if not os.path.exists(saves_dir):
            QMessageBox.warning(self, 'Wczytaj Grę', 'Brak zapisanych gier')
            return
        
        # Show file dialog to select save file
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            'Wybierz zapis gry', 
            saves_dir, 
            'Pliki zapisów (*.json);;Wszystkie pliki (*)'
        )
        
        if filepath:
            validator = get_validation_system()
            
            # Walidacja pliku JSON przed wczytaniem
            file_validation = validator.validate_json_file(filepath)
            
            if not file_validation.is_valid:
                error_msg = "Błędy w pliku zapisu:\n" + "\n".join(file_validation.errors)
                QMessageBox.critical(self, 'Błąd walidacji pliku', error_msg)
                return
            
            # Pokaż ostrzeżenia jeśli są
            if file_validation.warnings:
                warning_msg = "Ostrzeżenia dotyczące pliku:\n" + "\n".join(file_validation.warnings)
                reply = QMessageBox.question(
                    self,
                    'Ostrzeżenia pliku',
                    warning_msg + f"\n\nCzy kontynuować wczytywanie?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Walidacja danych zapisu gry
            save_data = file_validation.cleaned_data
            save_validation = validator.validate_game_save_data(save_data)
            
            if not save_validation.is_valid:
                error_msg = "Błędy w danych zapisu:\n" + "\n".join(save_validation.errors)
                QMessageBox.critical(self, 'Błąd walidacji danych', error_msg)
                return
            
            # Pokaż ostrzeżenia dotyczące danych
            if save_validation.warnings:
                warning_msg = "Ostrzeżenia dotyczące danych:\n" + "\n".join(save_validation.warnings)
                QMessageBox.information(self, 'Ostrzeżenia danych', warning_msg)
            
            success = self.game_engine.load_game(filepath)
            if success:
                # Update all UI elements after loading
                self.map_canvas.city_map = self.game_engine.city_map
                self.map_canvas.draw_map()
                
                # Update resources display
                self.build_panel.update_resources(self.game_engine.economy)
                self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
                
                # Update economy panel
                buildings = self.game_engine.get_all_buildings()
                income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
                expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
                tax_rates = self.game_engine.economy.tax_rates
                self.build_panel.update_economy_panel(income, expenses, tax_rates)
                
                # Update building availability
                self.build_panel.refresh_building_availability()
                
                # Update city level info
                current_pop = self.game_engine.population.get_total_population()
                next_level_pop = self.game_engine.get_next_level_requirement()
                self.build_panel.update_city_level_info(
                    self.game_engine.city_level,
                    current_pop,
                    next_level_pop
                )
                
                # Reset objectives for loaded game
                from core.objectives import ObjectiveManager
                from gui.objectives_panel import ObjectivesPanel
                
                self.objective_manager = ObjectiveManager()
                
                # Close old objectives panel if exists
                if hasattr(self, 'objectives_panel') and self.objectives_panel:
                    try:
                        self.objectives_panel.close()
                    except:
                        pass
                
                self.objectives_panel = ObjectivesPanel(self.objective_manager)
                self.objectives_panel.objective_completed.connect(self.on_objective_completed)
                
                # Clear reports history for loaded game
                self.reports_panel.history_data = {
                    'turns': [],
                    'population': [],
                    'budget': [],
                    'satisfaction': [],
                    'unemployment': [],
                    'income': [],
                    'expenses': []
                }
                self.reports_panel.update_charts()
                
                self.update_status_bar()
                QMessageBox.information(self, 'Wczytaj Grę', 'Gra wczytana pomyślnie')
            else:
                QMessageBox.warning(self, 'Wczytaj Grę', 'Nie udało się wczytać gry')
    
    def toggle_pause(self):
        """Toggle game pause state"""
        if self.game_engine.paused:
            self.game_engine.resume_game()
        else:
            self.game_engine.pause_game()
        self.update_status_bar()
    
    def set_difficulty(self, difficulty: str):
        """Set game difficulty"""
        self.game_engine.set_difficulty(difficulty)
        self.update_status_bar()
    
    def on_building_placed(self, x: int, y: int, building):
        """Handles building placement with validation"""
        from core.validation_system import get_validation_system
        
        validator = get_validation_system()
        
        # Walidacja współrzędnych
        coord_validation = validator.validate_coordinates(x, y, 
                                                        self.game_engine.city_map.width, 
                                                        self.game_engine.city_map.height)
        
        if not coord_validation.is_valid:
            error_msg = "Błędy współrzędnych:\n" + "\n".join(coord_validation.errors)
            QMessageBox.warning(self, 'Błąd walidacji', error_msg)
            self.map_canvas.draw_map()
            return
        
        # Walidacja danych budynku
        building_data = {
            'name': getattr(building, 'name', ''),
            'building_type': getattr(building, 'building_type', ''),
            'cost': getattr(building, 'cost', 0),
            'effects': getattr(building, 'effects', {})
        }
        
        building_validation = validator.validate_building_data(building_data)
        
        if not building_validation.is_valid:
            error_msg = "Błędy danych budynku:\n" + "\n".join(building_validation.errors)
            QMessageBox.warning(self, 'Błąd walidacji budynku', error_msg)
            self.map_canvas.draw_map()
            return
        
        # Pokaż ostrzeżenia jeśli są
        if building_validation.warnings:
            warning_msg = "Ostrzeżenia dotyczące budynku:\n" + "\n".join(building_validation.warnings)
            QMessageBox.information(self, 'Ostrzeżenia budynku', warning_msg)
        
        # Use game engine to place building
        success = self.game_engine.place_building(x, y, building)
        if success:
            # Update resources display
            self.build_panel.update_resources(self.game_engine.economy)
            self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
            self.update_status_bar()
            
            # --- Nowy kod: aktualizacja panelu ekonomii ---
            buildings = self.game_engine.get_all_buildings()
            income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
            expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
            tax_rates = self.game_engine.economy.tax_rates
            self.build_panel.update_economy_panel(income, expenses, tax_rates)
        
        # Always redraw map after placement attempt
        self.map_canvas.draw_map()
    
    def on_clear_selection(self):
        """Handles clearing building selection"""
        self.map_canvas.select_building(None)
    
    @performance_monitor
    def update_game(self):
        """Main game loop - updates all city systems with validation"""
        start_time = time.time()
        logger = game_logger.get_logger('game_engine')
        
        try:
            # Walidacja stanu gry przed aktualizacją
            if not self._validate_game_state():
                logger.error("Game state validation failed, skipping update")
                return
            
            # Update game engine (handles economy, population, etc.)
            self.game_engine.update_turn()
            
            # Update diplomacy system if exists
            if hasattr(self.game_engine, 'diplomacy_manager'):
                # Process diplomatic missions
                mission_results = self.game_engine.diplomacy_manager.update_missions(self.game_engine.turn)
                for result in mission_results:
                    if result['success']:
                        self.game_engine.add_alert(f"✅ {result['message']}", priority="info")
                    else:
                        self.game_engine.add_alert(f"❌ {result['message']}", priority="warning")
                
                # Process wars and their costs
                war_results = self.game_engine.diplomacy_manager.process_wars(self.game_engine.turn)
                for result in war_results:
                    if 'ended' in result:
                        if result['reason'] == 'exhaustion':
                            self.game_engine.add_alert(f"🏳️ Wojna z {result['war'].enemy_city} zakończona z wyczerpania", priority="info")
                        else:
                            self.game_engine.add_alert(f"🏳️ Wojna z {result['war'].enemy_city} zakończona", priority="info")
                    elif 'battle_result' in result:
                        self.game_engine.add_alert(f"⚔️ Bitwa z {result['city_name']}: {result['battle_result']}", priority="warning")
                
                # Apply war costs
                active_wars = self.game_engine.diplomacy_manager.active_wars
                if active_wars:
                    total_war_cost = len(active_wars) * 100  # Zmniejszone z 2000 na 100 za wojnę na turę
                    self.game_engine.economy.spend_money(total_war_cost)
                    self.game_engine.add_alert(f"💰 Koszty wojenne: ${total_war_cost:,}", priority="warning")
                    
                    # Automatyczne zakończenie długich wojen
                    for war in active_wars[:]:  # Kopia listy bo będziemy modyfikować
                        war_duration = self.game_engine.turn - war.started_turn
                        
                        # Zakończ wojnę po 20 turach lub gdy wyczerpanie > 0.8
                        if war_duration >= 20 or war.war_exhaustion >= 0.8:
                            city = self.game_engine.diplomacy_manager.cities[war.enemy_city]
                            self.game_engine.diplomacy_manager._end_war(war.enemy_city, self.game_engine.turn)
                            
                            if war_duration >= 20:
                                self.game_engine.add_alert(f"🏳️ Wojna z {city.name} zakończona - zbyt długo trwała", priority="info")
                            else:
                                self.game_engine.add_alert(f"🏳️ Wojna z {city.name} zakończona - wyczerpanie wojenne", priority="info")
            
            # Update UI elements
            self.update_status_bar()
            
            # Update build panel resources
            self.build_panel.update_resources(self.game_engine.economy)
            self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
            
            # Update building availability
            self.build_panel.refresh_building_availability()
            
            # Update city level information
            current_pop = self.game_engine.population.get_total_population()
            next_level_pop = self.game_engine.get_next_level_requirement()
            self.build_panel.update_city_level_info(
                self.game_engine.city_level,
                current_pop,
                next_level_pop
            )
            
            # Update economy panel
            buildings = self.game_engine.get_all_buildings()
            income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
            expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
            tax_rates = self.game_engine.economy.tax_rates
            self.build_panel.update_economy_panel(income, expenses, tax_rates)
            
            # Update objectives system
            game_state = {
                'turn': self.game_engine.turn,
                'population': self.game_engine.population.get_total_population(),
                'money': self.game_engine.economy.get_resource_amount('money'),
                'satisfaction': self.game_engine.population.get_average_satisfaction(),
                'buildings': self.game_engine.get_all_buildings(),
                'unlocked_technologies': [tech.name for tech in self.technology_tree.technologies.values() if tech.is_researched]
            }
            self.objectives_panel.update_objectives(game_state)
            
            # Update reports with proper data including loan payments
            buildings = self.game_engine.get_all_buildings()
            income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
            expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
            
            # Include loan payments in expenses
            monthly_payments = sum(loan.monthly_payment for loan in self.game_engine.finance_manager.active_loans)
            actual_expenses = expenses + monthly_payments
            
            self.reports_panel.add_data_point(
                turn=self.game_engine.turn,
                population=self.game_engine.population.get_total_population(),
                budget=self.game_engine.economy.get_resource_amount('money'),
                satisfaction=self.game_engine.population.get_average_satisfaction(),
                unemployment=self.game_engine.population.get_unemployment_rate(),
                income=income,
                expenses=actual_expenses
            )
            self.reports_panel.update_charts()
            
            # Trigger random event (zmieniam częstotliwość i dodaję kontekst)
            if self.game_engine.turn % 8 == 0 and self.game_engine.turn > 0:  # Co 8 tur
                event = self.event_manager.trigger_random_event(game_state)
                game_logger.log_game_event('EVENT', f'Wydarzenie: {event.title}')
                dialog = EventDialog(event, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_option = dialog.selected_option
                    
                    # Apply decision-specific effects using functional programming
                    effects = self.event_manager.apply_decision_effects(event, selected_option)
                    
                    # Użyj map do przetworzenia efektów
                    effect_results = list(safe_map(
                        lambda effect_item: self._apply_event_effect(effect_item[0], effect_item[1]),
                        effects.items()
                    ))
                    
                    # Show event result
                    self.game_engine.add_alert(f"Wydarzenie: {event.title} - Wybrano: {selected_option}")
            
            # Save game state - naprawiam odwołania
            self.database.save_game_state(
                self.game_engine.population.get_total_population(),
                self.game_engine.economy.get_resource_amount('money'),
                int(self.game_engine.population.get_average_satisfaction()),
                str(self.game_engine.economy.get_resource_amount('money'))  # Konwertuję na string
            )

            # Save history - naprawiam odwołania
            self.database.save_history(
                self.game_engine.turn,
                self.game_engine.population.get_total_population(),
                self.game_engine.economy.get_resource_amount('money'),
                int(self.game_engine.population.get_average_satisfaction()),
                str(self.game_engine.economy.get_resource_amount('money'))  # Konwertuję na string
            )

            # Save statistics - naprawiam odwołania
            self.database.save_statistics('population', self.game_engine.population.get_total_population())
            self.database.save_statistics('money', self.game_engine.economy.get_resource_amount('money'))
            self.database.save_statistics('satisfaction', int(self.game_engine.population.get_average_satisfaction()))
            self.database.save_statistics('resources', self.game_engine.economy.get_resource_amount('money'))

            # Check for bankruptcy and end game if needed
            if self.game_engine.economy.is_bankrupt(game_engine=self.game_engine):
                self.handle_bankruptcy()
                return
            
            # Redraw map if needed
            self.map_canvas.draw_map()
            
            # Loguj wydajność aktualizacji
            update_time = time.time() - start_time
            game_logger.log_performance('game_update', update_time, {
                'population': current_pop,
                'buildings': len(self.game_engine.get_all_buildings())
            })
            
        except Exception as e:
            logger.error(f"Error in update_game: {e}")
            game_logger.log_error(e, 'update_game', {
                'turn': getattr(self.game_engine, 'turn', 0)
            })
    
    def _apply_event_effect(self, effect_type: str, effect_value: float) -> bool:
        """
        Aplikuje efekt wydarzenia.
        
        Args:
            effect_type: Typ efektu
            effect_value: Wartość efektu
            
        Returns:
            True jeśli efekt został zastosowany
        """
        try:
            if effect_type == "population":
                self.game_engine.population.add_instant_population(effect_value)
                if effect_value > 0:
                    self.game_engine.add_alert(f"📈 Populacja wzrosła o {effect_value:+.0f} mieszkańców", priority="info")
                else:
                    self.game_engine.add_alert(f"📉 Populacja spadła o {abs(effect_value):.0f} mieszkańców", priority="warning")
                return True
            elif effect_type == "satisfaction":
                # Dodaję wpływ na zadowolenie wszystkich grup
                for group in self.game_engine.population.groups.values():
                    group.satisfaction = max(0, min(100, group.satisfaction + effect_value))
                if effect_value > 0:
                    self.game_engine.add_alert(f"😊 Zadowolenie mieszkańców wzrosło o {effect_value:+.1f}%", priority="info")
                else:
                    self.game_engine.add_alert(f"😞 Zadowolenie mieszkańców spadło o {abs(effect_value):.1f}%", priority="warning")
                return True
            elif effect_type == "money":
                if effect_value > 0:
                    self.game_engine.economy.earn_money(effect_value)
                    self.game_engine.add_alert(f"💰 Budżet zwiększył się o ${effect_value:,.0f}", priority="info")
                else:
                    self.game_engine.economy.spend_money(abs(effect_value))
                    self.game_engine.add_alert(f"💸 Wydatki dodatkowe: ${abs(effect_value):,.0f}", priority="warning")
                return True
            return False
        except Exception as e:
            game_logger.log_error(e, f'apply_event_effect_{effect_type}')
            return False
    
    def update_status_bar(self):
        """Update status bar with current city information"""
        summary = self.game_engine.get_city_summary()
        
        # Format money display for debt
        money = summary['money']
        if money < 0:
            money_text = f"💰 -${abs(money):,.0f} (DŁUG)"
        else:
            money_text = f"💰 ${money:,.0f}"
        
        status_text = (
            f"Turn: {summary['turn']} | "
            f"{money_text} | "
            f"👥 Pop: {summary['population']:,} | "
            f"😊 Satisfaction: {summary['satisfaction']:.1f}% | "
            f"📈 Unemployment: {summary['unemployment_rate']:.1f}%"
        )
        
        self.status_bar.showMessage(status_text)

    def on_tax_slider_changed(self, tax_key, value):
        """Obsługuje zmianę podatku przez slider z walidacją"""
        from core.validation_system import get_validation_system
        
        validator = get_validation_system()
        
        # Walidacja stawki podatkowej
        tax_validation = validator.validate_tax_rate(value)
        
        if not tax_validation.is_valid:
            # Loguj błąd i użyj bezpiecznej wartości
            import logging
            logger = logging.getLogger('ui')
            logger.warning(f"Invalid tax rate for {tax_key}: {tax_validation.errors}")
            
            # Użyj poprzedniej wartości lub domyślną
            safe_value = self.game_engine.economy.tax_rates.get(tax_key, 0.05)
            self.game_engine.economy.tax_rates[tax_key] = safe_value
            
            # Pokaż ostrzeżenie użytkownikowi
            QMessageBox.warning(
                self, 
                'Błąd walidacji podatku',
                f"Nieprawidłowa stawka podatkowa dla {tax_key}:\n" + 
                "\n".join(tax_validation.errors) +
                f"\n\nUżyto poprzedniej wartości: {safe_value:.2%}"
            )
        else:
            # Użyj zwalidowanej wartości
            validated_value = tax_validation.cleaned_data
            self.game_engine.economy.tax_rates[tax_key] = validated_value
        
        # Natychmiast odśwież panel ekonomii
        buildings = self.game_engine.get_all_buildings()
        income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
        expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
        tax_rates = self.game_engine.economy.tax_rates
        self.build_panel.update_economy_panel(income, expenses, tax_rates)
        self.update_status_bar()

    def on_building_sell_requested(self, x, y, building):
        """Obsługuje sprzedaż budynku po PPM na mapie"""
        success = self.game_engine.remove_building(x, y)
        if success:
            self.build_panel.update_resources(self.game_engine.economy)
            self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
            self.update_status_bar()
            # Przelicz koszty i dochody po usunięciu budynku
            buildings = self.game_engine.get_all_buildings()
            income = self.game_engine.economy.calculate_taxes(buildings, self.game_engine.population)
            expenses = self.game_engine.economy.calculate_expenses(buildings, self.game_engine.population)
            tax_rates = self.game_engine.economy.tax_rates
            self.build_panel.update_economy_panel(income, expenses, tax_rates)
            self.map_canvas.draw_map()

    def on_building_sell_button(self):
        """Obsługuje sprzedaż budynku po kliknięciu przycisku w panelu"""
        tile = self.map_canvas.city_map.get_selected_tile()
        if tile and tile.building:
            x, y = tile.x, tile.y
            self.on_building_sell_requested(x, y, tile.building)

    def show_reports(self):
        self.reports_panel.show()

    def show_technology(self):
        self.technology_panel.show()

    def show_objectives(self):
        self.objectives_panel.show()
    
    def show_trade(self):
        """Show trade panel"""
        if not hasattr(self, 'trade_panel'):
            from gui.trade_panel import TradePanel
            self.trade_panel = TradePanel(self.game_engine)
            
            # Connect signals
            self.trade_panel.offer_accepted.connect(self.on_trade_offer_accepted)
            self.trade_panel.contract_created.connect(self.on_trade_contract_created)
        
        self.trade_panel.refresh_data()
        self.trade_panel.show()
    
    def show_achievements(self):
        """Show achievements panel"""
        if not hasattr(self, 'achievements_panel'):
            from gui.achievements_panel import AchievementsPanel
            self.achievements_panel = AchievementsPanel(self.game_engine)
        
        self.achievements_panel.refresh_data()
        self.achievements_panel.show()
    
    def on_trade_offer_accepted(self, offer_id):
        """Handle trade offer acceptance"""
        success, message = self.game_engine.accept_trade_offer(offer_id)
        if success:
            # Update resources after trade
            self.build_panel.update_resources(self.game_engine.economy)
            self.update_status_bar()
            QMessageBox.information(self, "Handel", f"Oferta handlowa zaakceptowana!\n{message}")
        else:
            QMessageBox.warning(self, "Handel", f"Nie można zaakceptować oferty:\n{message}")
    
    def on_trade_contract_created(self, city_id, good_type, quantity, price, duration, is_buying):
        """Handle trade contract creation"""
        success, message = self.game_engine.create_trade_contract(
            city_id, good_type, quantity, price, duration, is_buying
        )
        if success:
            # Update resources after contract creation
            self.build_panel.update_resources(self.game_engine.economy)
            self.update_status_bar()
            QMessageBox.information(self, "Handel", f"Kontrakt handlowy utworzony!\n{message}")
        else:
            QMessageBox.warning(self, "Handel", f"Nie można utworzyć kontraktu:\n{message}")
    
    def on_objective_completed(self, obj_id):
        """Handle objective completion"""
        objective = self.objective_manager.objectives.get(obj_id)
        if objective:
            # Apply rewards
            if objective.reward_money > 0:
                self.game_engine.economy.earn_money(objective.reward_money)
                self.build_panel.update_resources(self.game_engine.economy)
                
            if objective.reward_satisfaction > 0:
                # Apply satisfaction bonus to all population groups
                for group in self.game_engine.population.groups.values():
                    group.satisfaction = min(100, group.satisfaction + objective.reward_satisfaction)
            
            # Show completion message
            reward_text = []
            if objective.reward_money > 0:
                reward_text.append(f"${objective.reward_money:,}")
            if objective.reward_satisfaction > 0:
                reward_text.append(f"+{objective.reward_satisfaction} zadowolenia")
            
            reward_str = " i ".join(reward_text) if reward_text else "brak nagród"
            
            QMessageBox.information(
                self, 
                "Cel ukończony!", 
                f"🎉 Gratulacje!\n\n"
                f"Ukończono cel: {objective.title}\n"
                f"Nagroda: {reward_str}\n\n"
                f"{objective.reward_description}"
            )
            
            self.update_status_bar()
    
    def _validate_game_state(self) -> bool:
        """Waliduje stan gry przed każdą aktualizacją"""
        from core.validation_system import get_validation_system
        
        try:
            validator = get_validation_system()
            
            # Sprawdzenie podstawowych obiektów
            if not hasattr(self, 'game_engine') or self.game_engine is None:
                return False
            
            if not hasattr(self.game_engine, 'economy') or self.game_engine.economy is None:
                return False
            
            if not hasattr(self.game_engine, 'population') or self.game_engine.population is None:
                return False
            
            # Walidacja stanu ekonomii
            current_money = self.game_engine.economy.get_resource_amount('money')
            money_validation = validator.validate_money_amount(current_money)
            
            if not money_validation.is_valid:
                logger = game_logger.get_logger('validation')
                logger.error(f"Invalid money state: {money_validation.errors}")
                # Próba naprawy - ustaw bezpieczną wartość
                self.game_engine.economy.resources['money'].amount = 0.0
            
            # Walidacja populacji
            current_population = self.game_engine.population.get_total_population()
            pop_validation = validator.validate_population(current_population)
            
            if not pop_validation.is_valid:
                logger = game_logger.get_logger('validation')
                logger.error(f"Invalid population state: {pop_validation.errors}")
                return False
            
            # Walidacja stawek podatkowych
            for tax_type, rate in self.game_engine.economy.tax_rates.items():
                tax_validation = validator.validate_tax_rate(rate)
                if not tax_validation.is_valid:
                    logger = game_logger.get_logger('validation')
                    logger.warning(f"Invalid tax rate {tax_type}: {tax_validation.errors}")
                    # Napraw stawkę podatkową
                    self.game_engine.economy.tax_rates[tax_type] = 0.05  # Domyślna 5%
            
            # Sprawdzenie czy gra nie jest w nieprawidłowym stanie
            if hasattr(self.game_engine, 'turn') and self.game_engine.turn < 0:
                logger = game_logger.get_logger('validation')
                logger.error("Invalid turn number")
                self.game_engine.turn = 0
            
            return True
            
        except Exception as e:
            logger = game_logger.get_logger('validation')
            logger.error(f"Game state validation error: {str(e)}")
            return False
    
    def handle_bankruptcy(self):
        """Handle bankruptcy - end game and show game over dialog"""
        # Stop the game timer to prevent further updates
        self.game_timer.stop()
        
        # Pause the game
        self.game_engine.pause_game()
        
        # Show GAME OVER dialog with custom buttons
        current_debt = self.game_engine.economy.get_resource_amount('money')
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🎮 GAME OVER")
        msg_box.setIcon(QMessageBox.Icon.Critical)
        
        # Set the main message with HTML formatting
        msg_box.setText(
            f"<div style='text-align: center;'>"
            f"<h1 style='color: red; font-size: 24px;'>💀 GAME OVER 💀</h1>"
            f"<h2 style='color: darkred;'>🏴 BANKRUCTWO! 🏴</h2>"
            f"</div>"
        )
        
        # Set detailed message
        msg_box.setInformativeText(
            f"<div style='font-size: 14px;'>"
            f"<b>Twoje miasto zbankrutowało!</b><br><br>"
            f"💰 <b>Obecny dług:</b> <span style='color: red; font-weight: bold;'>${abs(current_debt):,.0f}</span><br>"
            f"📉 <b>Limit długu:</b> $4,000<br><br>"
            f"<i>💔 Nie udało się utrzymać równowagi finansowej miasta.<br>"
            f"👥 Mieszkańcy stracili zaufanie do władz lokalnych.<br>"
            f"🏛️ Miasto popadło w ruinę...</i><br><br>"
            f"<b>Co chcesz zrobić?</b>"
            f"</div>"
        )
        
        # Add custom buttons
        new_game_button = msg_box.addButton("🎯 Nowa Gra", QMessageBox.ButtonRole.AcceptRole)
        exit_button = msg_box.addButton("🚪 Wyjdź", QMessageBox.ButtonRole.RejectRole)
        
        # Set button styles
        new_game_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: 2px solid #145a32;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #145a32;
            }
        """)
        
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # Set default button
        msg_box.setDefaultButton(new_game_button)
        
        # Show dialog and handle response
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == new_game_button:
            # Start new game
            self.new_game()
            # Restart timer
            self.game_timer.start(15000)
        elif clicked_button == exit_button:
            # Close the application
            self.close()

    def show_alerts(self):
        """Show alerts panel"""
        if not hasattr(self, 'alerts_panel'):
            from gui.alerts_panel import AlertsPanel
            self.alerts_panel = AlertsPanel(self.game_engine)
        
        self.alerts_panel.refresh_alerts()
        self.alerts_panel.show()
    
    def show_diplomacy(self):
        """Show diplomacy panel"""
        if not hasattr(self, 'diplomacy_panel'):
            from gui.diplomacy_panel import DiplomacyPanel
            self.diplomacy_panel = DiplomacyPanel(self.game_engine)
        
        self.diplomacy_panel.refresh_data()
        self.diplomacy_panel.show()
    
    def show_finance(self):
        """Show finance panel"""
        self.finance_panel.update_display(self.game_engine.economy, self.game_engine.population)
        self.finance_panel.show()
    
    def show_scenarios(self):
        """Show scenarios panel"""
        self.scenarios_panel.update_display()
        self.scenarios_panel.show()
    
    def on_loan_requested(self, loan_type: str, amount: float):
        """Handle loan request from finance panel"""
        success, message = self.game_engine.apply_for_loan(loan_type, amount)
        
        from PyQt6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Pożyczka zatwierdzona", message)
            # Aktualizuj interfejs
            self.build_panel.update_resources(self.game_engine.economy)
            self.finance_panel.update_display(self.game_engine.economy, self.game_engine.population)
        else:
            QMessageBox.warning(self, "Pożyczka odrzucona", message)
    
    def on_scenario_started(self, scenario_id: str):
        """Handle scenario start"""
        success, message = self.game_engine.start_scenario(scenario_id)
        
        from PyQt6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Scenariusz rozpoczęty", message)
            
            # PEŁNE ODŚWIEŻENIE INTERFEJSU po resetacji gry
            self.build_panel.update_resources(self.game_engine.economy)
            self.map_canvas.resources = self.game_engine.economy.get_resource_amount('money')
            self.map_canvas.city_map = self.game_engine.city_map  # Odśwież mapę
            self.map_canvas.draw_map()  # Przerysuj mapę
            
            # Aktualizuj poziom miasta
            current_pop = self.game_engine.population.get_total_population()
            next_level_pop = self.game_engine.get_next_level_requirement()
            self.build_panel.update_city_level_info(
                self.game_engine.city_level,
                current_pop,
                next_level_pop
            )
            
            # Aktualizuj dostępność budynków
            self.build_panel.refresh_building_availability()
            
            # Aktualizuj status bar
            self.update_status_bar()
            
            # Zamknij panel scenariuszy
            self.scenarios_panel.hide()
            
        else:
            QMessageBox.warning(self, "Błąd scenariusza", message)

def main():
    """
    main() - Funkcja główna aplikacji z obsługą argumentów wiersza poleceń
    
    Obsługuje podstawowe argumenty:
    --width, --height - rozmiar okna
    --map-size - rozmiar mapy
    --debug - tryb debugowania
    --scenario - scenariusz startowy
    --version - wersja aplikacji
    """
    import argparse
    
    # Parsowanie argumentów wiersza poleceń
    parser = argparse.ArgumentParser(
        description='City Builder - Advanced City Simulator',
        prog='City Builder',
        epilog='Przykłady użycia:\n'
               '  python Main.py --width 1920 --height 1080\n'
               '  python Main.py --debug --scenario sandbox\n'
               '  python Main.py --map-size 80',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Dodaj podstawowe argumenty
    parser.add_argument(
        '--width', 
        type=int, 
        default=1600, 
        help='Szerokość okna (domyślnie: 1600)'
    )
    
    parser.add_argument(
        '--height', 
        type=int, 
        default=1000, 
        help='Wysokość okna (domyślnie: 1000)'
    )
    
    parser.add_argument(
        '--map-size', 
        type=int, 
        default=60, 
        help='Rozmiar mapy (szerokość i wysokość, domyślnie: 60)'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Włącz tryb debugowania z szczegółowym logowaniem'
    )
    
    parser.add_argument(
        '--scenario', 
        type=str, 
        choices=['sandbox', 'campaign', 'challenge', 'tutorial'],
        help='Rozpocznij z wybranym scenariuszem'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='City Builder 1.0 - Advanced City Simulator'
    )
    
    # Parsuj argumenty
    args = parser.parse_args()
    
    # Zastosuj argumenty do konfiguracji
    if args.debug:
        print("🐛 Tryb debugowania włączony")
        # Zmień poziom logowania na DEBUG
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Utwórz instancję aplikacji PyQt6
        app = QApplication(sys.argv)
        
        # Utwórz główne okno aplikacji
        window = MainWindow()
        
        # Zastosuj argumenty rozmiaru okna
        if args.width != 1600 or args.height != 1000:
            window.setGeometry(100, 100, args.width, args.height)
            print(f"📏 Rozmiar okna ustawiony na: {args.width}x{args.height}")
        
        # Zastosuj rozmiar mapy (wymaga restartu gry)
        if args.map_size != 60:
            print(f"🗺️ Rozmiar mapy będzie ustawiony na: {args.map_size}x{args.map_size}")
            # Można dodać logikę zmiany rozmiaru mapy
        
        # Jeśli podano scenariusz, uruchom go po pokazaniu okna
        if args.scenario:
            print(f"🎮 Rozpoczynanie scenariusza: {args.scenario}")
        
        window.show()
        
        # Uruchom scenariusz po pokazaniu okna (jeśli podano)
        if args.scenario:
            from PyQt6.QtCore import QTimer
            def start_scenario():
                success, message = window.game_engine.start_scenario(args.scenario)
                if success:
                    print(f"✅ Scenariusz '{args.scenario}' uruchomiony pomyślnie")
                else:
                    print(f"❌ Błąd uruchamiania scenariusza: {message}")
            
            # Uruchom scenariusz z opóźnieniem (po pełnej inicjalizacji)
            QTimer.singleShot(1000, start_scenario)
        
        # Uruchom główną pętlę aplikacji
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Błąd krytyczny: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
