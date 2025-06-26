"""
Testy jednostkowe dla GameEngine - głównego silnika gry
"""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import os

# Dodaj ścieżkę do modułów projektu - MUSI być przed importami z core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game_engine import GameEngine
from core.tile import Building, BuildingType, TerrainType
from tests.test_helpers import find_buildable_location, place_building_safely


class TestGameEngine:
    """Test głównego silnika gry"""
    
    def setup_method(self):
        """Setup przed każdym testem"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        
        self.engine = GameEngine(map_width=10, map_height=10)
    
    def test_initialization(self):
        """Test inicjalizacji silnika gry"""
        assert self.engine.city_map is not None
        assert self.engine.economy is not None
        assert self.engine.population is not None
        assert self.engine.turn == 0
        assert self.engine.city_level == 1
        assert not self.engine.paused
        
        # Sprawdź początkowe zasoby
        money = self.engine.economy.get_resource_amount('money')
        assert money > 0
    
    def test_level_requirements(self):
        """Test wymagań poziomów miasta"""
        assert self.engine.level_requirements[1] == 0
        assert self.engine.level_requirements[2] == 600
        assert self.engine.level_requirements[3] == 1400
        assert self.engine.level_requirements[10] == 30000
    
    def test_get_next_level_requirement(self):
        """Test pobierania wymagań następnego poziomu"""
        # Poziom 1 -> następny poziom 2 (600 mieszkańców)
        assert self.engine.get_next_level_requirement() == 600
        
        # Symulacja awansu na poziom 2
        self.engine.city_level = 2
        assert self.engine.get_next_level_requirement() == 1400
        
        # Maksymalny poziom
        self.engine.city_level = 10
        assert self.engine.get_next_level_requirement() == 0
    
    def test_building_placement(self):
        """Test stawiania budynków"""
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        # Znajdź odpowiednie miejsce
        x, y = find_buildable_location(self.engine)
        assert x is not None and y is not None
        
        # Sprawdź czy można postawić
        can_build, reason = self.engine.can_build(x, y, house)
        assert can_build, f"Cannot build: {reason}"
        
        # Postaw budynek
        success = self.engine.place_building(x, y, house)
        assert success
        
        # Sprawdź czy budynek został postawiony
        tile = self.engine.city_map.get_tile(x, y)
        assert tile.building is not None
        assert tile.building.name == "Test House"
        assert tile.is_occupied
    
    def test_building_removal(self):
        """Test usuwania budynków"""
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        # Postaw budynek
        x, y = find_buildable_location(self.engine)
        success = self.engine.place_building(x, y, house)
        assert success
        
        # Sprawdź początkowy stan
        tile = self.engine.city_map.get_tile(x, y)
        assert tile.building is not None
        
        # Usuń budynek
        success = self.engine.remove_building(x, y)
        assert success
        
        # Sprawdź czy budynek został usunięty
        tile = self.engine.city_map.get_tile(x, y)
        assert tile.building is None
        assert not tile.is_occupied
    
    def test_can_build_validation(self):
        """Test walidacji możliwości budowania"""
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        # Test na nieprawidłowych współrzędnych
        can_build, reason = self.engine.can_build(-1, -1, house)
        assert not can_build
        assert ("Invalid location" in reason or "Cannot build outside map boundaries" in reason or "Building extends beyond map boundaries" in reason)
        
        can_build, reason = self.engine.can_build(100, 100, house)
        assert not can_build
        assert ("Invalid location" in reason or "Cannot build outside map boundaries" in reason or "Building extends beyond map boundaries" in reason)
        
        # Test na zajętym miejscu
        x, y = find_buildable_location(self.engine)
        self.engine.place_building(x, y, house)
        
        house2 = Building("Test House 2", BuildingType.HOUSE, 500, {"population": 35})
        can_build, reason = self.engine.can_build(x, y, house2)
        assert not can_build
        assert "already occupied" in reason
        
        # Test na wodzie/górach
        for x in range(self.engine.city_map.width):
            for y in range(self.engine.city_map.height):
                tile = self.engine.city_map.get_tile(x, y)
                if tile.terrain_type == TerrainType.WATER:
                    can_build, reason = self.engine.can_build(x, y, house2)
                    assert not can_build
                    assert "water" in reason.lower()
                    break
                elif tile.terrain_type == TerrainType.MOUNTAIN:
                    can_build, reason = self.engine.can_build(x, y, house2)
                    assert not can_build
                    assert "mountain" in reason.lower()
                    break
    
    def test_insufficient_funds(self):
        """Test budowania przy niewystarczających środkach"""
        # Wydaj wszystkie pieniądze
        current_money = self.engine.economy.get_resource_amount('money')
        self.engine.economy.spend_money(current_money - 100)
        
        # Spróbuj postawić drogi budynek
        expensive_building = Building("Expensive", BuildingType.HOSPITAL, 50000, {"health": 100})
        
        x, y = find_buildable_location(self.engine)
        can_build, reason = self.engine.can_build(x, y, expensive_building)
        assert not can_build
        assert "Insufficient funds" in reason
    
    def test_update_turn(self):
        """Test aktualizacji tury"""
        initial_turn = self.engine.turn
        
        # Dodaj budynek żeby mieć jakąś aktywność
        house = Building("House", BuildingType.HOUSE, 500, {"population": 35})
        place_building_safely(self.engine, house)
        
        # Aktualizuj turę
        self.engine.update_turn()
        
        assert self.engine.turn == initial_turn + 1
        
        # Sprawdź czy systemy zostały zaktualizowane
        # (trudno to przetestować bezpośrednio, ale nie powinno być błędów)
    
    def test_update_city_level(self):
        """Test aktualizacji poziomu miasta"""
        initial_level = self.engine.city_level
        
        # Dodaj dużo domów aby zwiększyć populację
        houses_needed = 20  # Powinno wystarczyć na poziom 2 (600 mieszkańców)
        placed_houses = 0
        
        for i in range(houses_needed):
            house = Building(f"House {i}", BuildingType.HOUSE, 500, {"population": 35})
            if place_building_safely(self.engine, house):
                placed_houses += 1
                if placed_houses >= 15:  # 15 * 35 = 525, blisko 600
                    break
        
        # Sprawdź czy udało się postawić wystarczająco domów
        population = self.engine.population.get_total_population()
        print(f"Population after placing {placed_houses} houses: {population}")
        
        # Aktualizuj poziom miasta
        self.engine.update_city_level()
        
        # Jeśli populacja przekroczyła próg, poziom powinien wzrosnąć
        if population >= 600:
            assert self.engine.city_level > initial_level
        else:
            # Jeśli nie udało się osiągnąć progu, poziom pozostaje ten sam
            assert self.engine.city_level == initial_level
    
    def test_get_all_buildings(self):
        """Test pobierania wszystkich budynków"""
        # Na początku brak budynków
        buildings = self.engine.get_all_buildings()
        initial_count = len(buildings)
        
        # Dodaj kilka budynków
        house1 = Building("House 1", BuildingType.HOUSE, 500, {"population": 35})
        house2 = Building("House 2", BuildingType.HOUSE, 500, {"population": 35})
        shop = Building("Shop", BuildingType.SHOP, 800, {"commerce": 20})
        
        placed_count = 0
        if place_building_safely(self.engine, house1):
            placed_count += 1
        if place_building_safely(self.engine, house2):
            placed_count += 1
        if place_building_safely(self.engine, shop):
            placed_count += 1
        
        buildings = self.engine.get_all_buildings()
        assert len(buildings) == initial_count + placed_count
        
        # Sprawdź czy budynki są w liście
        building_names = [b.name for b in buildings if b is not None]
        if placed_count >= 1:
            assert "House 1" in building_names or "House 2" in building_names or "Shop" in building_names
    
    def test_pause_resume(self):
        """Test pauzowania i wznawiania gry"""
        assert not self.engine.paused
        
        self.engine.pause_game()
        assert self.engine.paused
        
        self.engine.resume_game()
        assert not self.engine.paused
    
    def test_game_speed(self):
        """Test zmiany prędkości gry"""
        assert self.engine.game_speed == 1.0
        
        self.engine.set_game_speed(2.0)
        assert self.engine.game_speed == 2.0
        
        self.engine.set_game_speed(0.5)
        assert self.engine.game_speed == 0.5
    
    def test_difficulty_settings(self):
        """Test ustawień trudności"""
        assert self.engine.difficulty == "Normal"
        
        self.engine.set_difficulty("Hard")
        assert self.engine.difficulty == "Hard"
        
        # Test modyfikatorów trudności
        modifier = self.engine.difficulty_modifiers["Hard"]["cost_multiplier"]
        assert modifier > 1.0  # Hard powinien być droższy
        
        # Test dostosowanego kosztu
        base_cost = 1000
        adjusted_cost = self.engine.get_adjusted_cost(base_cost)
        assert adjusted_cost == base_cost * modifier
    
    def test_alerts_system(self):
        """Test systemu alertów"""
        initial_alerts = len(self.engine.get_recent_alerts())
        
        self.engine.add_alert("Test alert")
        
        alerts = self.engine.get_recent_alerts()
        assert len(alerts) == initial_alerts + 1
        
        # Sprawdź czy alert zawiera odpowiednie informacje
        latest_alert = alerts[-1]
        assert "Test alert" in latest_alert['message']
        assert 'timestamp' in latest_alert
        assert 'priority' in latest_alert
    
    def test_city_summary(self):
        """Test podsumowania miasta"""
        # Dodaj kilka budynków
        house = Building("House", BuildingType.HOUSE, 500, {"population": 35})
        shop = Building("Shop", BuildingType.SHOP, 800, {"jobs": 15})
        
        place_building_safely(self.engine, house)
        place_building_safely(self.engine, shop)
        
        summary = self.engine.get_city_summary()
        
        # Sprawdź podstawowe informacje
        assert 'population' in summary
        assert 'money' in summary
        assert 'turn' in summary
        assert 'total_buildings' in summary
        assert 'building_types' in summary
        
        # Sprawdź czy wartości są sensowne
        assert summary['population'] >= 0
        assert summary['money'] >= 0
        assert summary['turn'] >= 0
        assert summary['total_buildings'] >= 0
    
    def test_statistics_tracking(self):
        """Test śledzenia statystyk"""
        initial_stats = self.engine.statistics.copy()
        
        # Postaw budynek
        house = Building("House", BuildingType.HOUSE, 500, {"population": 35})
        place_building_safely(self.engine, house)
        
        # Sprawdź czy statystyki się zmieniły
        assert self.engine.statistics['buildings_built'] == initial_stats['buildings_built'] + 1
        assert self.engine.statistics['total_money_spent'] > initial_stats['total_money_spent']
        
        # Aktualizuj turę
        self.engine.update_turn()
        
        assert self.engine.statistics['turns_played'] > initial_stats['turns_played']


if __name__ == "__main__":
    pytest.main([__file__]) 