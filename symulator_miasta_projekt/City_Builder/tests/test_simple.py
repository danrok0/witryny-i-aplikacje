"""
Uproszczone testy jednostkowe dla City Builder
"""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import os

# Dodaj ścieżkę do modułów projektu - MUSI być przed importami z core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game_engine import GameEngine
from core.population import PopulationManager
from core.events import EventManager
from core.objectives import ObjectiveManager
from core.tile import Building, BuildingType
from tests.test_helpers import find_buildable_location, place_building_safely


class TestBasicFunctionality:
    """Podstawowe testy funkcjonalności"""
    
    def test_game_engine_initialization(self):
        """Test inicjalizacji silnika gry"""
        engine = GameEngine(map_width=10, map_height=10)
        
        assert engine.turn == 0
        assert engine.city_level == 1
        assert engine.city_map.width == 10
        assert engine.city_map.height == 10
        assert hasattr(engine, 'population')
        assert hasattr(engine, 'economy')
    
    def test_population_manager_initialization(self):
        """Test inicjalizacji managera populacji"""
        population = PopulationManager()
        
        assert population.get_total_population() > 0
        assert population.get_unemployment_rate() >= 0
        assert population.get_average_satisfaction() > 0
        assert len(population.groups) == 5
    
    def test_event_manager_initialization(self):
        """Test inicjalizacji managera wydarzeń"""
        event_manager = EventManager()
        
        assert len(event_manager.events) > 0
        assert hasattr(event_manager, 'event_history')
        assert len(event_manager.event_history) == 0
    
    def test_objective_manager_initialization(self):
        """Test inicjalizacji managera celów"""
        objective_manager = ObjectiveManager()
        
        assert len(objective_manager.objectives) > 0
        assert len(objective_manager.completed_objectives) == 0
        assert len(objective_manager.failed_objectives) == 0
    
    def test_building_creation(self):
        """Test tworzenia budynków"""
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        assert house.name == "Test House"
        assert house.building_type == BuildingType.HOUSE
        assert house.cost == 500
        assert house.effects["population"] == 35
    
    def test_building_placement(self):
        """Test stawiania budynków"""
        engine = GameEngine(map_width=10, map_height=10)
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        # Znajdź odpowiednie miejsce do budowania
        x, y = find_buildable_location(engine)
        assert x is not None, "No buildable location found"
        
        # Test poprawnego stawiania
        success = engine.place_building(x, y, house)
        assert success
        
        # Test stawiania na zajętym miejscu
        house2 = Building("Test House 2", BuildingType.HOUSE, 500, {"population": 35})
        success = engine.place_building(x, y, house2)
        assert not success
    
    def test_population_calculation(self):
        """Test obliczania populacji"""
        population = PopulationManager()
        
        # Test podstawowych obliczeń
        total = population.get_total_population()
        unemployment = population.get_unemployment_rate()
        satisfaction = population.get_average_satisfaction()
        
        assert total >= 0
        assert 0 <= unemployment <= 100
        assert 0 <= satisfaction <= 100
    
    def test_event_triggering(self):
        """Test wyzwalania wydarzeń"""
        event_manager = EventManager()
        
        # Test losowego wydarzenia
        event = event_manager.trigger_random_event()
        
        assert event is not None
        assert hasattr(event, 'title')
        assert hasattr(event, 'description')
        assert hasattr(event, 'effects')
        assert len(event_manager.event_history) == 1
    
    def test_objective_management(self):
        """Test zarządzania celami"""
        objective_manager = ObjectiveManager()
        
        # Test pobierania aktywnych celów
        active_objectives = objective_manager.get_active_objectives()
        assert len(active_objectives) > 0
        
        # Test pobierania ukończonych celów
        completed_objectives = objective_manager.get_completed_objectives()
        assert len(completed_objectives) == 0
    
    def test_game_turn_update(self):
        """Test aktualizacji tury"""
        engine = GameEngine(map_width=10, map_height=10)
        initial_turn = engine.turn
        
        engine.update_turn()
        
        assert engine.turn == initial_turn + 1
    
    def test_resource_management(self):
        """Test zarządzania zasobami"""
        engine = GameEngine(map_width=10, map_height=10)
        
        initial_money = engine.economy.get_resource_amount('money')
        
        # Test wydawania pieniędzy
        engine.economy.spend_money(1000)
        assert engine.economy.get_resource_amount('money') == initial_money - 1000
        
        # Test dodawania pieniędzy
        engine.economy.earn_money(500)
        assert engine.economy.get_resource_amount('money') == initial_money - 500


class TestIntegration:
    """Testy integracyjne"""
    
    def test_building_affects_population(self):
        """Test czy budynki wpływają na populację"""
        engine = GameEngine(map_width=10, map_height=10)
        
        initial_population = engine.population.get_total_population()
        
        # Dodaj dom
        house = Building("House", BuildingType.HOUSE, 500, {"population": 35})
        success = place_building_safely(engine, house)
        assert success, "Failed to place house"
        
        # Sprawdź czy populacja wzrosła
        new_population = engine.population.get_total_population()
        assert new_population > initial_population
    
    def test_multiple_buildings(self):
        """Test stawiania wielu budynków"""
        engine = GameEngine(map_width=10, map_height=10)
        
        buildings = [
            Building("House 1", BuildingType.HOUSE, 500, {"population": 35}),
            Building("House 2", BuildingType.HOUSE, 500, {"population": 35}),
            Building("Shop", BuildingType.SHOP, 800, {"jobs": 15})
        ]
        
        placed_count = 0
        for building in buildings:
            success = place_building_safely(engine, building)
            if success:
                placed_count += 1
        
        assert placed_count >= 2, f"Only placed {placed_count} out of {len(buildings)} buildings"
        
        # Sprawdź czy budynki są na mapie
        all_buildings = engine.get_all_buildings()
        assert len(all_buildings) >= placed_count
    
    def test_city_level_progression(self):
        """Test progresji poziomu miasta"""
        engine = GameEngine(map_width=10, map_height=10)
        
        initial_level = engine.city_level
        
        # Dodaj dużo domów
        houses_placed = 0
        for i in range(20):
            house = Building(f"House {i}", BuildingType.HOUSE, 500, {"population": 35})
            success = place_building_safely(engine, house)
            if success:
                houses_placed += 1
                if houses_placed >= 15:  # Wystarczy na test
                    break
        
        # Aktualizuj poziom miasta
        engine.update_city_level()
        
        # Sprawdź czy poziom wzrósł (jeśli populacja przekroczyła próg)
        population = engine.population.get_total_population()
        if population >= 600:
            assert engine.city_level > initial_level
        else:
            # Jeśli nie osiągnięto progu, poziom pozostaje ten sam
            assert engine.city_level == initial_level


if __name__ == "__main__":
    pytest.main([__file__]) 