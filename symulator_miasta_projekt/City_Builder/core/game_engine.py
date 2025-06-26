from typing import List, Dict, Optional
from .city_map import CityMap
from .resources import Economy
from .population import PopulationManager
from .tile import Building, BuildingType, TerrainType
from .technology import TechnologyManager
from .trade import TradeManager
from .achievements import AchievementManager
from .finance import FinanceManager
from .scenarios import ScenarioManager
import time
from copy import deepcopy

class GameEngine:
    """
    Główny silnik gry koordinujący wszystkie systemy miasta.
    
    Jest to centralny system zarządzający logiką gry City Builder.
    Odpowiada za:
    - Koordynację wszystkich podsystemów (ekonomia, populacja, technologie)
    - Aktualizację stanu gry co turę
    - Zarządzanie budynkami i mapą miasta
    - Obsługę poziomów trudności
    - Zbieranie statystyk i osiągnięć
    """
    
    def __init__(self, map_width: int = 60, map_height: int = 60):
        """
        Konstruktor silnika gry.
        
        Args:
            map_width (int): szerokość mapy w kafelkach (domyślnie 60)
            map_height (int): wysokość mapy w kafelkach (domyślnie 60)
        """
        # Podstawowe systemy gry
        self.city_map = CityMap(map_width, map_height)    # mapa miasta z kafelkami
        self.economy = Economy()                          # system ekonomiczny (pieniądze, zasoby)
        self.population = PopulationManager()             # zarządzanie ludnością
        
        # Zaawansowane systemy dodane w późniejszych fazach
        self.technology_manager = TechnologyManager()     # drzewo technologii
        self.trade_manager = TradeManager()               # handel z innymi miastami
        self.achievement_manager = AchievementManager()   # system osiągnięć
        self.finance_manager = FinanceManager()           # system finansowy i pożyczek
        self.scenario_manager = ScenarioManager()         # scenariusze i tryby gry
        
        # Stan gry
        self.turn = 0                                     # numer aktualnej tury
        self.game_speed = 1.0                            # mnożnik prędkości gry
        self.paused = False                              # czy gra jest wstrzymana
        self.last_update = time.time()                   # czas ostatniej aktualizacji
        
        # System poziomów miasta
        self.city_level = 1                               # aktualny poziom miasta
        self.level_requirements = {                       # wymagania populacji dla każdego poziomu
            1: 0,      # poziom 1: start gry (0 mieszkańców)
            2: 600,    # poziom 2: 600 mieszkańców
            3: 1400,   # poziom 3: 1400 mieszkańców
            4: 2800,   # poziom 4: 2800 mieszkańców
            5: 5000,   # poziom 5: 5000 mieszkańców
            6: 8000,   # poziom 6: 8000 mieszkańców
            7: 12000,  # poziom 7: 12000 mieszkańców
            8: 17000,  # poziom 8: 17000 mieszkańców
            9: 23000,  # poziom 9: 23000 mieszkańców
            10: 30000  # poziom 10: 30000 mieszkańców (maksymalny)
        }
        
        # Ustawienia poziomów trudności
        self.difficulty = "Normal"                        # aktualny poziom trudności
        self.difficulty_modifiers = {                     # modyfikatory dla różnych poziomów trudności
            "Easy": {                                     # łatwy poziom
                "cost_multiplier": 0.8,                   # budynki kosztują 20% mniej
                "income_multiplier": 1.2,                 # dochody o 20% wyższe
                "event_frequency": 0.5                    # wydarzenia 2x rzadsze
            },
            "Normal": {                                   # normalny poziom (bazowy)
                "cost_multiplier": 1.0,                   # standardowe koszty
                "income_multiplier": 1.0,                 # standardowe dochody
                "event_frequency": 1.0                    # standardowa częstotliwość wydarzeń
            },
            "Hard": {                                     # trudny poziom
                "cost_multiplier": 1.3,                   # budynki kosztują 30% więcej
                "income_multiplier": 0.8,                 # dochody o 20% niższe
                "event_frequency": 1.5                    # wydarzenia 50% częstsze
            }
        }
        
        # Zaawansowane śledzenie statystyk gry
        self.statistics = {
            'buildings_built': 0,                    # całkowita liczba zbudowanych budynków
            'total_money_spent': 0,                  # całkowita suma wydanych pieniędzy
            'max_population': 0,                     # maksymalna populacja osiągnięta w grze
            'turns_played': 0,                       # liczba rozegranych tur
            'technologies_researched': 0,            # liczba zbadanych technologii
            'trades_completed': 0,                   # liczba ukończonych transakcji handlowych
            'total_tax_collected': 0,               # całkowita suma zebranych podatków
            'unemployment_streak': 0,               # najdłuższa pasa bezrobocia
            'building_types_built': set(),          # set() - unikalny zbiór typów zbudowanych budynków
            'parks_built': 0,                       # liczba zbudowanych parków
            'pollution_level': 0,                   # aktualny poziom zanieczyszczenia
            'renewable_energy_percent': 0,         # procent energii odnawialnej
            'disasters_survived': 0,               # liczba przetrwanych katastrof
            'crisis_events_resolved': 0,          # liczba rozwiązanych kryzysów
            'perfect_happiness_streak': 0,        # najdłuższa pasa 100% zadowolenia
            'allied_cities': 0                    # liczba sprzymierzonych miast
        }
        
        # System alertów i powiadomień
        self.alerts = []                              # lista aktualnych alertów dla gracza
        
        # Aktualny scenariusz
        self.current_scenario = None                  # obecnie uruchomiony scenariusz
        
        # Specjalne tryby gry
        self.special_sandbox_mode = False             # Tryb nieograniczonych środków
        self.bankruptcy_disabled = False              # Wyłączenie bankructwa
        
    def get_all_buildings(self) -> List[Building]:
        """
        Pobiera wszystkie budynki z mapy miasta.
        
        Returns:
            List[Building]: lista wszystkich budynków znajdujących się na mapie
            
        Ta metoda przechodzi przez każdy kafelek na mapie i zbiera wszystkie budynki.
        Jest używana do aktualizacji ekonomii, populacji i innych systemów.
        """
        buildings = []  # pusta lista na budynki
        
        # Przejdź przez wszystkie kafelki na mapie (podwójna pętla)
        for x in range(self.city_map.width):          # dla każdej kolumny
            for y in range(self.city_map.height):     # dla każdego rzędu
                tile = self.city_map.get_tile(x, y)   # pobierz kafelek na pozycji (x, y)
                # Sprawdź czy kafelek istnieje i czy ma budynek
                if tile and tile.building:
                    buildings.append(tile.building)   # dodaj budynek do listy
        
        return buildings  # zwróć listę wszystkich budynków
    
    def can_build(self, x: int, y: int, building: Building) -> tuple[bool, str]:
        """
        Sprawdza czy można zbudować budynek na danej pozycji.
        
        Ta metoda wykonuje kompletną walidację przed budową, sprawdzając:
        - Czy budynek jest odblokowany (poziom miasta, technologie)
        - Czy miasto ma wystarczające środki finansowe
        - Czy budynek mieści się w granicach mapy
        - Czy wszystkie potrzebne kafelki są wolne
        - Czy teren pozwala na budowę (nie na wodzie/górach)
        
        Args:
            x, y: współrzędne lewego górnego rogu budynku (indeks kafelka)
            building: obiekt budynku do umieszczenia
            
        Returns:
            tuple[bool, str]: (czy_można_budować, powód_odmowy_lub_OK)
        """
        # KROK 1: Sprawdź czy budynek jest odblokowany (poziom, technologie)
        unlocked, reason = self.is_building_unlocked(building)
        if not unlocked:
            return False, reason  # zwróć powód blokady
        
        # KROK 2: Sprawdź dostępność środków finansowych (z modyfikatorem trudności)
        cost = self.get_adjusted_cost(building.cost)  # koszt z uwzględnieniem poziomu trudności
        if not self.economy.can_afford(cost):
            money = self.economy.get_resource_amount('money')
            return False, f"Insufficient funds. Need ${cost:,.0f}, have ${money:,.0f}"
        
        # KROK 3: Sprawdź czy budynek mieści się w granicach mapy
        building_width, building_height = building.get_building_size()  # rozmiar budynku w kafelkach
        
        # Sprawdź prawą i dolną granicę mapy
        if x + building_width > self.city_map.width or y + building_height > self.city_map.height:
            return False, f"Building extends beyond map boundaries (size: {building_width}x{building_height})"
        
        # Sprawdź lewą i górną granicę mapy
        if x < 0 or y < 0:
            return False, "Cannot build outside map boundaries"
        
        # KROK 4: Sprawdź dostępność wszystkich potrzebnych kafelków
        occupied_tiles = building.get_occupied_tiles(x, y)  # lista kafelków które budynek zajmie
        for tile_x, tile_y in occupied_tiles:
            tile = self.city_map.get_tile(tile_x, tile_y)  # pobierz kafelek
            if not tile:  # nieprawidłowe współrzędne
                return False, f"Invalid tile position ({tile_x}, {tile_y})"
            
            if tile.is_occupied:  # kafelek już zajęty przez inny budynek
                return False, f"Tile ({tile_x}, {tile_y}) is already occupied"
            
            # KROK 5: Sprawdź kompatybilność terenu
            # Nie można budować na wodzie i w górach (ograniczenia realistyczne)
            if tile.terrain_type in [TerrainType.WATER, TerrainType.MOUNTAIN]:
                terrain_name = "water" if tile.terrain_type == TerrainType.WATER else "mountains"
                return False, f"Cannot build on {terrain_name} at ({tile_x}, {tile_y})"
        
        return True, "OK"  # wszystkie sprawdzenia przeszły pomyślnie
    
    def place_building(self, x: int, y: int, building: Building) -> bool:
        """
        Umieszcza budynek na mapie po pomyślnej walidacji.
        
        Proces budowy składa się z następujących kroków:
        1. Walidacja możliwości budowy
        2. Zajęcie wszystkich kafelków przez budynek
        3. Natychmiastowe dodanie efektów budynku
        4. Pobranie kosztów z budżetu miasta
        5. Aktualizacja statystyk gry
        6. Powiadomienie gracza o budowie
        
        Args:
            x, y: współrzędne lewego górnego rogu budynku
            building: obiekt budynku do umieszczenia
            
        Returns:
            bool: True jeśli budowa się powiodła, False w przeciwnym razie
        """
        # KROK 1: Sprawdź czy można budować (używa can_build)
        can_build, reason = self.can_build(x, y, building)
        if not can_build:
            self.add_alert(f"Cannot build: {reason}")  # powiadom gracza o problemie
            return False
        
        # KROK 2: Zajmij wszystkie kafelki potrzebne dla budynku
        occupied_tiles = building.get_occupied_tiles(x, y)  # lista wszystkich kafelków budynku
        
        # Ustaw budynek na wszystkich kaflach (główny + pomocnicze)
        for i, (tile_x, tile_y) in enumerate(occupied_tiles):
            tile = self.city_map.get_tile(tile_x, tile_y)
            
            # Pierwszy kafel (indeks 0) to główny kafel budynku
            if i == 0:
                tile.building = building  # główny kafel ma pełny obiekt budynku
                tile.is_main_tile = True  # oznacz jako główny kafel
            else:
                tile.building = building  # pomocnicze kafle też mają referencję do budynku
                tile.is_main_tile = False  # oznacz jako pomocniczy kafel
            
            tile.is_occupied = True  # zaznacz kafel jako zajęty
        
        # KROK 3: Zastosuj natychmiastowe efekty budynku
        # Jeśli budynek mieszkalny - dodaj populację od razu
        if hasattr(building, 'effects') and 'population' in building.effects:
            self.population.add_instant_population(building.effects['population'])
        
        # KROK 4: Pobierz koszt budowy z budżetu miasta
        cost = self.get_adjusted_cost(building.cost)  # koszt z modyfikatorem trudności
        self.economy.spend_money(cost, self)  # wydaj pieniądze na budowę
        
        # KROK 5: Aktualizuj statystyki gry dla osiągnięć i raportów
        self.statistics['buildings_built'] += 1  # zwiększ licznik zbudowanych budynków
        self.statistics['total_money_spent'] += cost  # dodaj koszt do łącznych wydatków
        self.statistics['building_types_built'].add(building.building_type.value)  # dodaj typ do set'a
        
        # Śledź specjalne typy budynków (dla konkretnych osiągnięć)
        if building.building_type == BuildingType.PARK:
            self.statistics['parks_built'] += 1  # licznik parków
        
        # KROK 6: Powiadom gracza o pomyślnej budowie
        # Dodaj informację o rozmiarze dla budynków większych niż 1x1
        building_size_text = f" ({building.size[0]}x{building.size[1]})" if building.size != (1, 1) else ""
        self.add_alert(f"Built {building.name}{building_size_text} for ${cost:,.0f}")
        return True  # budowa zakończona sukcesem
    
    def remove_building(self, x: int, y: int) -> bool:
        """Remove a building from the map and refund half its cost. Also remove its effects from city systems and update all stats."""
        tile = self.city_map.get_tile(x, y)
        if not tile or not tile.building:
            return False
        
        building = tile.building
        building_name = building.name
        building_cost = building.cost
        
        # Znajdź wszystkie kafle zajęte przez budynek
        # Jeśli kliknięto pomocniczy kafel, znajdź główny kafel
        main_tile = tile
        main_x, main_y = x, y
        
        # Jeśli to nie główny kafel, znajdź główny kafel tego budynku
        if hasattr(tile, 'is_main_tile') and not tile.is_main_tile:
            # Przeszukaj pobliskie kafle aby znaleźć główny kafel tego samego budynku
            for search_x in range(max(0, x - 4), min(self.city_map.width, x + 5)):
                for search_y in range(max(0, y - 4), min(self.city_map.height, y + 5)):
                    search_tile = self.city_map.get_tile(search_x, search_y)
                    if (search_tile and search_tile.building == building and 
                        hasattr(search_tile, 'is_main_tile') and search_tile.is_main_tile):
                        main_tile = search_tile
                        main_x, main_y = search_x, search_y
                        break
                if main_tile != tile:
                    break
        
        # Pobierz wszystkie kafle zajęte przez budynek
        occupied_tiles = building.get_occupied_tiles(main_x, main_y)
        
        # Usuwanie efektów budynku
        if hasattr(building, 'effects'):
            effects = building.effects
            # Populacja
            if 'population' in effects:
                self.population.add_instant_population(-effects['population'])
            # Praca
            if 'jobs' in effects:
                pass
        
        # Usuń budynek ze wszystkich kafelków
        for tile_x, tile_y in occupied_tiles:
            tile_to_clear = self.city_map.get_tile(tile_x, tile_y)
            if tile_to_clear and tile_to_clear.building == building:
                tile_to_clear.building = None
                tile_to_clear.is_occupied = False
                tile_to_clear.is_main_tile = True  # Reset do domyślnej wartości
        
        # Refund half the cost
        refund = building_cost * 0.5
        self.economy.earn_money(refund)
        
        # Wymuś pełną aktualizację niektórych systemów/statystyk
        buildings = self.get_all_buildings()
        self.population.calculate_needs(buildings)
        self.population.update_population_dynamics()
        self.update_city_level()
        
        building_size_text = f" ({building.size[0]}x{building.size[1]})" if building.size != (1, 1) else ""
        self.add_alert(f"Sprzedano {building_name}{building_size_text} za ${refund:,.0f}")
        return True
    
    def get_adjusted_cost(self, base_cost: float) -> float:
        """Get cost adjusted for difficulty"""
        modifier = self.difficulty_modifiers[self.difficulty]["cost_multiplier"]
        return base_cost * modifier
    
    def update_turn(self):
        """
        Aktualizuje wszystkie systemy gry o jedną turę.
        
        To jest główna metoda zarządzająca logiką gry, wywoływana co turę.
        Koordynuje wszystkie podsystemy w określonej kolejności aby zapewnić
        spójność danych i właściwe przetwarzanie zależności między systemami.
        
        Kolejność aktualizacji jest ważna:
        1. Populacja (bazowe potrzeby mieszkańców)
        2. Ekonomia (podatki, wydatki na podstawie populacji)
        3. Systemy zaawansowane (technologie, handel, finanse)
        4. Scenariusze i osiągnięcia (ocena postępu)
        5. Sprawdzenie sytuacji krytycznych
        """
        if self.paused:  # jeśli gra wstrzymana, nie aktualizuj
            return
        
        # KROK 1: Pobierz wszystkie budynki z mapy (potrzebne dla wszystkich systemów)
        buildings = self.get_all_buildings()
        
        # KROK 2: Aktualizuj system populacji (pierwszy, bo inne systemy zależą od niego)
        self.population.calculate_needs(buildings)  # oblicz potrzeby mieszkańców na podstawie budynków
        self.population.update_population_dynamics()  # aktualizuj wzrost/spadek populacji
        self.update_city_level()  # sprawdź czy miasto awansowało na wyższy poziom
        
        # KROK 3: Aktualizuj ekonomię (podatki zależą od populacji)
        self.economy.update_turn(buildings, self.population)  # przelicz podatki, koszty utrzymania
        
        # KROK 4: Aktualizuj zaawansowane systemy
        self.technology_manager.update_research()  # postęp badań naukowych
        self.trade_manager.current_turn = self.turn  # zsynchronizuj numer tury
        self.trade_manager.update_turn()  # przetwórz kontrakty handlowe
        
        # KROK 5: Aktualizuj system finansowy (kredyty, rating)
        self.finance_manager.calculate_credit_score(self.economy, self.population)  # oblicz rating kredytowy
        loan_payments = self.finance_manager.process_loan_payments(self.economy, self.turn)  # spłaty pożyczek
        financial_report = self.finance_manager.generate_financial_report(
            self.turn, self.economy, self.population, buildings)  # wygeneruj raport finansowy
        
        # KROK 6: Aktualizuj postęp scenariusza (jeśli aktywny)
        if self.scenario_manager.current_scenario:
            game_state = self.get_city_summary()  # pobierz aktualny stan miasta
            scenario_update = self.scenario_manager.update_scenario(game_state)  # sprawdź postęp
            if scenario_update.get('completed'):  # scenariusz ukończony
                self.add_alert(f"🎯 Scenariusz ukończony: {self.scenario_manager.current_scenario.title}!", 
                             priority="achievement")
            elif scenario_update.get('failed'):  # scenariusz nieudany
                self.add_alert(f"💥 Scenariusz nieudany: {self.scenario_manager.current_scenario.title}", 
                             priority="critical")
        
        # KROK 7: Aktualizuj statystyki gry (dla osiągnięć i raportów)
        self._update_enhanced_statistics(buildings)
        
        # KROK 8: Sprawdź osiągnięcia (na podstawie aktualnych statystyk)
        newly_unlocked = self.achievement_manager.check_achievements(self.statistics)
        for achievement in newly_unlocked:  # powiadom o nowych osiągnięciach
            self.add_alert(f"🏆 Osiągnięcie odblokowane: {achievement.name}!", priority="achievement")
        
        # KROK 9: Sprawdź sytuacje krytyczne (długi, niezadowolenie, braki)
        self._check_critical_situations()
        
        # KROK 10: Zakończ turę (zwiększ licznik tur)
        self.turn += 1  # przejdź do następnej tury
        self.statistics['turns_played'] = self.turn  # aktualizuj statystyki
    
    def _update_enhanced_statistics(self, buildings: List[Building]):
        """Update enhanced statistics for achievements"""
        # Basic population stats
        current_pop = self.population.get_total_population()
        if current_pop > self.statistics['max_population']:
            self.statistics['max_population'] = current_pop
        
        # Current population for achievements
        self.statistics['population'] = current_pop
        self.statistics['money'] = self.economy.get_resource_amount('money')
        
        # Technology stats
        self.statistics['technologies_researched'] = len(self.technology_manager.get_researched_technologies())
        
        # Trade stats
        trade_stats = self.trade_manager.get_trade_statistics()
        self.statistics['trades_completed'] = trade_stats['total_trades']
        
        # Count allied cities
        allied_count = 0
        for city_name, city_data in trade_stats['relationships'].items():
            if city_data['status'] == 'allied':
                allied_count += 1
        self.statistics['allied_cities'] = allied_count
        
        # Unemployment tracking for achievements
        unemployment_rate = self.population.get_unemployment_rate()
        if unemployment_rate == 0:
            self.statistics['unemployment_streak'] += 1
        else:
            self.statistics['unemployment_streak'] = 0
        
        # Happiness tracking
        satisfaction = self.population.get_average_satisfaction()
        if satisfaction >= 100:
            self.statistics['perfect_happiness_streak'] += 1
        else:
            self.statistics['perfect_happiness_streak'] = 0
        
        # Tax collection tracking
        # This would need to be tracked in economy system
        
        # Environmental stats (placeholder - would need actual implementation)
        self.statistics['pollution_level'] = max(0, 50 - len([b for b in buildings if b.building_type == BuildingType.PARK]))
        
        # Count renewable energy buildings
        renewable_buildings = [b for b in buildings if 'renewable' in b.name.lower() or 'solar' in b.name.lower() or 'wind' in b.name.lower()]
        total_energy_buildings = [b for b in buildings if 'power' in b.name.lower() or 'energy' in b.name.lower()]
        if total_energy_buildings:
            self.statistics['renewable_energy_percent'] = (len(renewable_buildings) / len(total_energy_buildings)) * 100
        else:
            self.statistics['renewable_energy_percent'] = 0
    
    def _check_critical_situations(self):
        """Check for situations that require player attention"""
        # Money warnings - including debt warnings
        money = self.economy.get_resource_amount('money')
        if money <= -3500:  # Very close to bankruptcy
            self.add_alert("🚨 CRITICAL: Bankruptcy imminent! Debt approaching -$4,000 limit!", priority="critical")
        elif money <= -2000:  # Deep in debt
            self.add_alert("⚠️ WARNING: Heavy debt! Reduce expenses or increase income!", priority="warning")
        elif money < 0:  # In debt but not critical
            self.add_alert("💸 City is in debt - monitor expenses carefully", priority="info")
        elif money < 5000:  # Low money warning
            self.add_alert("⚠️ Treasury running low!", priority="warning")
        
        # Low satisfaction warning
        avg_satisfaction = self.population.get_average_satisfaction()
        if avg_satisfaction < 30:
            self.add_alert("😞 Population satisfaction is very low!", priority="warning")
        
        # High unemployment warning
        unemployment = self.population.get_unemployment_rate()
        if unemployment > 20:
            self.add_alert(f"📈 High unemployment: {unemployment:.1f}%", priority="warning")
        
        # Resource shortages
        for need_name, need_data in self.population.needs.items():
            if need_data['satisfaction'] < 25:
                self.add_alert(f"🏥 Shortage of {need_name}", priority="info")
    
    def add_alert(self, message: str, priority: str = "info"):
        """Add an alert message"""
        alert = {
            'message': message,
            'priority': priority,
            'turn': self.turn,
            'timestamp': time.time()
        }
        self.alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts.pop(0)
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-count:]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
    
    def set_difficulty(self, difficulty: str):
        """Set game difficulty"""
        if difficulty in self.difficulty_modifiers:
            self.difficulty = difficulty
            self.add_alert(f"Difficulty set to {difficulty}")
        
    def pause_game(self):
        """Pause the game"""
        self.paused = True
        
    def resume_game(self):
        """Resume the game"""
        self.paused = False
        
    def set_game_speed(self, speed: float):
        """Set game speed multiplier"""
        self.game_speed = max(0.1, min(5.0, speed))  # Clamp between 0.1x and 5x
    
    def get_city_summary(self) -> Dict:
        """Get a comprehensive summary of city status"""
        buildings = self.get_all_buildings()
        demographics = self.population.get_demographics()
        resources = self.economy.get_resource_summary()
        
        return {
            'turn': self.turn,
            'difficulty': self.difficulty,
            'paused': self.paused,
            'city_name': f"City Turn {self.turn}",  # Could be customizable
            
            # Economy
            'money': resources['money']['amount'],
            'money_change': resources['money']['production'] - resources['money']['consumption'],
            'resources': resources,
            
            # Population
            'population': demographics['total_population'],
            'unemployment_rate': demographics['unemployment_rate'],
            'satisfaction': demographics['average_satisfaction'],
            'demographics': demographics,
            
            # Infrastructure
            'total_buildings': len(buildings),
            'building_types': self._count_building_types(buildings),
            'needs': self.population.needs,
            
            # Statistics
            'statistics': self.statistics,
            'alerts': self.get_recent_alerts()
        }
    
    def _count_building_types(self, buildings: List[Building]) -> Dict[str, int]:
        """Count buildings by type"""
        counts = {}
        for building in buildings:
            building_type = building.building_type.value
            counts[building_type] = counts.get(building_type, 0) + 1
        return counts
    
    def save_game(self, filepath: str) -> bool:
        """Save game state to file with validation"""
        from .validation_system import get_validation_system
        
        try:
            import json
            import os
            
            validator = get_validation_system()
            
            # Walidacja ścieżki pliku
            if not isinstance(filepath, str) or not filepath:
                self.add_alert("Nieprawidłowa ścieżka pliku", priority="warning")
                return False
            
            # Prepare statistics for JSON serialization (convert set to list)
            statistics_for_save = self.statistics.copy()
            if 'building_types_built' in statistics_for_save and isinstance(statistics_for_save['building_types_built'], set):
                statistics_for_save['building_types_built'] = list(statistics_for_save['building_types_built'])
            
            save_data = {
                'version': '1.0',
                'turn': self.turn,
                'difficulty': self.difficulty,
                'statistics': statistics_for_save,
                'alerts': self.alerts,
                'city_level': self.city_level,
                
                # Map data
                'map': {
                    'width': self.city_map.width,
                    'height': self.city_map.height,
                    'tiles': []
                },
                
                # Economy data
                'economy': self.economy.save_to_dict(),
                
                # Population data
                'population': self.population.save_to_dict()
            }
            
            # Save tile data
            for x in range(self.city_map.width):
                for y in range(self.city_map.height):
                    tile = self.city_map.get_tile(x, y)
                    tile_data = {
                        'x': x,
                        'y': y,
                        'terrain_type': tile.terrain_type.value,
                        'is_occupied': tile.is_occupied,
                        'building': None
                    }
                    
                    if tile.building:
                        tile_data['building'] = {
                            'name': tile.building.name,
                            'building_type': tile.building.building_type.value,
                            'cost': tile.building.cost,
                            'effects': tile.building.effects,
                            'rotation': tile.building.rotation
                        }
                    
                    save_data['map']['tiles'].append(tile_data)
            
            # Walidacja danych przed zapisem
            save_validation = validator.validate_game_save_data(save_data)
            
            if not save_validation.is_valid:
                error_msg = "Błędy walidacji danych zapisu: " + "; ".join(save_validation.errors)
                self.add_alert(error_msg, priority="warning")
                # Możemy kontynuować mimo ostrzeżeń, ale logujemy błędy
                import logging
                logger = logging.getLogger('game_engine')
                logger.warning(f"Save validation errors: {save_validation.errors}")
            
            # Loguj ostrzeżenia
            if save_validation.warnings:
                import logging
                logger = logging.getLogger('game_engine')
                logger.info(f"Save validation warnings: {save_validation.warnings}")
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            filename = os.path.basename(filepath)
            self.add_alert(f"Gra zapisana jako {filename}")
            return True
            
        except Exception as e:
            self.add_alert(f"Błąd zapisu gry: {str(e)}", priority="warning")
            return False
    
    def load_game(self, filepath: str) -> bool:
        """Load game state from file"""
        try:
            import json
            import os
            from .city_map import CityMap, TerrainType
            from .tile import Building, BuildingType
            
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Load basic game state
            self.turn = save_data.get('turn', 0)
            self.difficulty = save_data.get('difficulty', 'Normal')
            self.statistics = save_data.get('statistics', {})
            
            # Convert building_types_built from list back to set if needed
            if 'building_types_built' in self.statistics and isinstance(self.statistics['building_types_built'], list):
                self.statistics['building_types_built'] = set(self.statistics['building_types_built'])
            
            self.alerts = save_data.get('alerts', [])
            self.city_level = save_data.get('city_level', 1)
            
            # Load map
            map_data = save_data.get('map', {})
            self.city_map = CityMap(map_data.get('width', 60), map_data.get('height', 60))
            
            # Load tiles
            for tile_data in map_data.get('tiles', []):
                x, y = tile_data['x'], tile_data['y']
                tile = self.city_map.get_tile(x, y)
                
                if tile:
                    tile.terrain_type = TerrainType(tile_data['terrain_type'])
                    tile.is_occupied = tile_data['is_occupied']
                    
                    if tile_data['building']:
                        building_data = tile_data['building']
                        building = Building(
                            building_data['name'],
                            BuildingType(building_data['building_type']),
                            building_data['cost'],
                            building_data['effects']
                        )
                        building.rotation = building_data.get('rotation', 0)
                        tile.building = building
            
            # Load economy
            if 'economy' in save_data:
                self.economy.load_from_dict(save_data['economy'])
            
            # Load population
            if 'population' in save_data:
                self.population.load_from_dict(save_data['population'])
            
            filename = os.path.basename(filepath)
            self.add_alert(f"Gra wczytana: {filename}")
            return True
            
        except Exception as e:
            self.add_alert(f"Błąd wczytywania gry: {str(e)}", priority="warning")
            return False
    
    def update_city_level(self):
        """Update city level based on population"""
        current_pop = self.population.get_total_population()
        next_level = self.city_level + 1
        
        if next_level in self.level_requirements:
            if current_pop >= self.level_requirements[next_level]:
                self.city_level = next_level
                self.add_alert(f"🎉 Miasto osiągnęło poziom {next_level}!")
                return True
        return False

    def get_next_level_requirement(self) -> int:
        """Get population requirement for next level"""
        next_level = self.city_level + 1
        return self.level_requirements.get(next_level, 0)

    def is_building_unlocked(self, building: Building) -> tuple[bool, str]:
        """Check if a building is unlocked based on game conditions"""
        # Basic buildings are always available
        basic_buildings = [
            BuildingType.ROAD,
            BuildingType.ROAD_CURVE,
            BuildingType.SIDEWALK,
            BuildingType.HOUSE,
            BuildingType.SHOP
        ]
        if building.building_type in basic_buildings:
            return True, "OK"
        if not hasattr(building, 'unlock_condition') or not building.unlock_condition:
            return True, "OK"
        conditions = building.unlock_condition
        # Check city level requirement
        if 'city_level' in conditions:
            if self.city_level < conditions['city_level']:
                return False, f"Od poziomu miasta: {conditions['city_level']}"
        # Check population requirement
        if 'population' in conditions:
            current_pop = self.population.get_total_population()
            if current_pop < conditions['population']:
                return False, f"Wymagana populacja: {conditions['population']}"
        
        # Check technology requirement
        if 'technology' in conditions:
            required_tech = conditions['technology']
            if required_tech not in [tech.id for tech in self.technology_manager.get_researched_technologies()]:
                tech = self.technology_manager.technologies.get(required_tech)
                tech_name = tech.name if tech else required_tech
                return False, f"Wymagana technologia: {tech_name}"
        
        return True, "OK"
    
    # Technology management methods
    def start_research(self, tech_id: str, investment: int = 0) -> tuple[bool, str]:
        """Start researching a technology"""
        can_research, reason = self.technology_manager.can_research(tech_id)
        if not can_research:
            return False, reason
        
        # Check if we can afford the investment
        if investment > 0 and not self.economy.can_afford(investment):
            return False, f"Cannot afford research investment of ${investment:,}"
        
        # Deduct investment cost
        if investment > 0:
            self.economy.spend_money(investment, self)
        
        success = self.technology_manager.start_research(tech_id, investment)
        if success:
            tech = self.technology_manager.technologies[tech_id]
            self.add_alert(f"🔬 Started researching: {tech.name}")
            if investment > 0:
                self.add_alert(f"💰 Research investment: ${investment:,}")
        
        return success, "Research started" if success else "Failed to start research"
    
    def get_available_technologies(self):
        """Get technologies available for research"""
        return self.technology_manager.get_available_technologies()
    
    def get_researched_technologies(self):
        """Get completed technologies"""
        return self.technology_manager.get_researched_technologies()
    
    def get_current_research(self):
        """Get currently researched technology"""
        if self.technology_manager.current_research:
            return self.technology_manager.technologies[self.technology_manager.current_research]
        return None
    
    def get_technology_effects(self):
        """Get cumulative effects of all researched technologies"""
        return self.technology_manager.get_technology_effects()
    
    # Trade management methods
    def get_trade_offers(self, good_type=None):
        """Get available trade offers"""
        return self.trade_manager.get_available_offers(good_type)
    
    def accept_trade_offer(self, offer_id: str) -> tuple[bool, str]:
        """Accept a trade offer"""
        success, message = self.trade_manager.accept_offer(offer_id)
        if success:
            self.statistics['trades_completed'] += 1
            self.add_alert(f"📦 {message}")
        return success, message
    
    def create_trade_contract(self, city_id: str, good_type, quantity_per_turn: int, 
                            price_per_unit: float, duration_turns: int, is_buying: bool) -> tuple[bool, str]:
        """Create a long-term trade contract"""
        return self.trade_manager.create_contract(city_id, good_type, quantity_per_turn, 
                                                price_per_unit, duration_turns, is_buying)
    
    def get_trade_statistics(self):
        """Get trade statistics"""
        return self.trade_manager.get_trade_statistics()
    
    def get_trading_cities(self):
        """Get all trading cities"""
        return self.trade_manager.trading_cities
    
    # Achievement management methods
    def get_achievements_by_category(self, category):
        """Get achievements by category"""
        return self.achievement_manager.get_achievements_by_category(category)
    
    def get_unlocked_achievements(self):
        """Get unlocked achievements"""
        return self.achievement_manager.get_unlocked_achievements()
    
    def get_locked_achievements(self, include_hidden=False):
        """Get locked achievements"""
        return self.achievement_manager.get_locked_achievements(include_hidden)
    
    def get_achievement_statistics(self):
        """Get achievement statistics"""
        return self.achievement_manager.get_achievement_statistics()
    
    def get_achievement_notifications(self):
        """Get and clear achievement notifications"""
        return self.achievement_manager.get_notifications()
    
    def get_all_achievements(self):
        """Get all achievements"""
        return list(self.achievement_manager.achievements.values())
    
    # ===== SYSTEM FINANSOWY =====
    
    def get_loan_offer(self, loan_type: str, amount: float):
        """Pobiera ofertę pożyczki"""
        from .finance import LoanType
        loan_type_enum = LoanType(loan_type)
        return self.finance_manager.get_loan_offer(loan_type_enum, amount, self.economy, self.population)
    
    def apply_for_loan(self, loan_type: str, amount: float) -> tuple[bool, str]:
        """Składa wniosek o pożyczkę"""
        from .finance import LoanType
        loan_type_enum = LoanType(loan_type)
        offer = self.finance_manager.get_loan_offer(loan_type_enum, amount, self.economy, self.population)
        
        if not offer:
            return False, "Nie można uzyskać tej pożyczki"
        
        success, message = self.finance_manager.take_loan(offer, self.turn)
        if success:
            # Dodaj pieniądze do budżetu
            self.economy.earn_money(amount)
            self.add_alert(f"💳 Zaciągnięto pożyczkę ${amount:,.0f}", priority="info")
        
        return success, message
    
    def get_financial_summary(self):
        """Pobiera podsumowanie finansowe"""
        return {
            'credit_score': self.finance_manager.credit_score,
            'credit_rating': self.finance_manager.credit_rating.value,
            'bankruptcy_risk': self.finance_manager.bankruptcy_risk,
            'active_loans': len(self.finance_manager.active_loans),
            'total_debt': sum(loan.remaining_amount for loan in self.finance_manager.active_loans),
            'monthly_payments': sum(loan.monthly_payment for loan in self.finance_manager.active_loans)
        }
    
    def get_financial_advice(self):
        """Pobiera porady finansowe"""
        return self.finance_manager.get_financial_advice(self.economy, self.population)
    
    # ===== SYSTEM SCENARIUSZY =====
    
    def start_scenario(self, scenario_id: str) -> tuple[bool, str]:
        """Uruchamia scenariusz"""
        success, message = self.scenario_manager.start_scenario(scenario_id)
        if success:
            scenario = self.scenario_manager.scenarios[scenario_id]
            
            # RESETUJ GRĘ - ważne dla zmiany scenariuszy
            self.reset_game_state()
            
            # Zastosuj warunki początkowe scenariusza
            self.economy.modify_resource('money', scenario.starting_money - self.economy.get_resource_amount('money'))
            
            # Zastosuj specjalne warunki scenariuszy
            if "unlimited_money" in scenario.special_conditions:
                self.special_sandbox_mode = True
                self.add_alert("💰 Tryb nieograniczonych środków aktywny!", priority="info")
            else:
                self.special_sandbox_mode = False
            
            if "no_bankruptcy" in scenario.special_conditions:
                self.bankruptcy_disabled = True
            else:
                self.bankruptcy_disabled = False
            
            self.current_scenario = scenario
            self.add_alert(f"🎮 Rozpoczęto scenariusz: {scenario.title}", priority="info")
            
        return success, message
    
    def reset_game_state(self):
        """Resetuje stan gry do początkowego"""
        # Reset podstawowych zasobów
        self.turn = 0
        
        # Reset ekonomii
        self.economy.resources['money'].amount = 10000.0  # Domyślna ilość
        
        # Reset populacji
        self.population.reset_to_initial_state()
        
        # Reset miasta - wyczyść mapę
        for x in range(self.city_map.width):
            for y in range(self.city_map.height):
                if self.city_map.get_tile(x, y).building:
                    self.city_map.get_tile(x, y).building = None
        
        # Reset poziomu miasta
        self.city_level = 1
        
        # Reset alertów
        self.alerts.clear()
        
        # Reset statystyk - zachowaj wszystkie klucze z konstruktora
        self.statistics = {
            'buildings_built': 0,                    # całkowita liczba zbudowanych budynków
            'total_money_spent': 0,                  # całkowita suma wydanych pieniędzy
            'max_population': 0,                     # maksymalna populacja osiągnięta w grze
            'turns_played': 0,                       # liczba rozegranych tur
            'technologies_researched': 0,            # liczba zbadanych technologii
            'trades_completed': 0,                   # liczba ukończonych transakcji handlowych
            'total_tax_collected': 0,               # całkowita suma zebranych podatków
            'unemployment_streak': 0,               # najdłuższa pasa bezrobocia
            'building_types_built': set(),          # set() - unikalny zbiór typów zbudowanych budynków
            'parks_built': 0,                       # liczba zbudowanych parków
            'pollution_level': 0,                   # aktualny poziom zanieczyszczenia
            'renewable_energy_percent': 0,         # procent energii odnawialnej
            'disasters_survived': 0,               # liczba przetrwanych katastrof
            'crisis_events_resolved': 0,          # liczba rozwiązanych kryzysów
            'perfect_happiness_streak': 0,        # najdłuższa pasa 100% zadowolenia
            'allied_cities': 0                    # liczba sprzymierzonych miast
        }
        
        # Reset systemów
        if hasattr(self, 'finance_manager'):
            self.finance_manager.active_loans.clear()
            self.finance_manager.credit_score = 650  # Reset score
        
        # Reset technologii
        if hasattr(self, 'technology_manager'):
            for tech in self.technology_manager.technologies.values():
                tech.is_researched = False
                tech.research_progress = 0
            self.technology_manager.current_research = None
    
    def get_available_scenarios(self):
        """Pobiera dostępne scenariusze"""
        return self.scenario_manager.get_available_scenarios()
    
    def get_scenario_progress(self):
        """Pobiera postęp aktualnego scenariusza"""
        if self.scenario_manager.current_scenario:
            return self.scenario_manager.current_scenario.get_progress()
        return None
