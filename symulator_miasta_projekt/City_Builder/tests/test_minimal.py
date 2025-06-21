"""
Minimalny test dla podstawowej funkcjonalności
"""
import pytest
import sys
import os

# Dodaj ścieżkę do modułów projektu - MUSI być przed importami z core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication
from core.game_engine import GameEngine
from core.population import PopulationManager
from core.events import EventManager
from core.objectives import ObjectiveManager
from core.tile import Building, BuildingType, TerrainType
from tests.test_helpers import find_buildable_location

def test_imports():
    """Test podstawowych importów"""
    assert GameEngine is not None
    assert PopulationManager is not None
    assert EventManager is not None
    assert ObjectiveManager is not None

def test_basic_creation():
    """Test podstawowego tworzenia obiektów"""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    engine = GameEngine(map_width=3, map_height=3)
    assert engine is not None
    
    population = PopulationManager()
    assert population is not None
    
    events = EventManager()
    assert events is not None
    
    objectives = ObjectiveManager()
    assert objectives is not None

def test_simple_building():
    """Test prostego budowania"""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    # Użyj większej mapy aby zwiększyć szanse na odpowiedni teren
    engine = GameEngine(map_width=10, map_height=10)
    house = Building("House", BuildingType.HOUSE, 500, {"population": 35})

    # Sprawdź pieniądze
    money = engine.economy.get_resource_amount('money')
    assert money >= 500

    # Debug: sprawdź typy terenu na mapie
    terrain_types = {}
    for x in range(10):
        for y in range(10):
            tile = engine.city_map.get_tile(x, y)
            terrain_type = tile.terrain_type.value if tile else "None"
            terrain_types[terrain_type] = terrain_types.get(terrain_type, 0) + 1
    
    print(f"Terrain types on 10x10 map: {terrain_types}")

    # Znajdź odpowiedni teren do budowania (trawa lub piasek)
    build_x, build_y = None, None
    for x in range(10):
        for y in range(10):
            tile = engine.city_map.get_tile(x, y)
            if tile and not tile.is_occupied:
                # Sprawdź czy można budować na tym terenie
                if tile.terrain_type in [TerrainType.GRASS, TerrainType.SAND]:
                    can_build, reason = engine.can_build(x, y, house)
                    if can_build:
                        build_x, build_y = x, y
                        break
        if build_x is not None:
            break
    
    # Jeśli nadal nie ma odpowiedniego terenu, spróbuj na dowolnym dostępnym
    if build_x is None:
        for x in range(10):
            for y in range(10):
                tile = engine.city_map.get_tile(x, y)
                if tile and not tile.is_occupied:
                    # Spróbuj zbudować nawet na wodzie/górach dla testu
                    can_build, reason = engine.can_build(x, y, house)
                    if can_build:
                        build_x, build_y = x, y
                        break
            if build_x is not None:
                break
    
    # Jeśli nadal nie ma miejsca, wymuszaj budowę na pierwszym dostępnym miejscu
    if build_x is None:
        for x in range(10):
            for y in range(10):
                tile = engine.city_map.get_tile(x, y)
                if tile and not tile.is_occupied:
                    # Tymczasowo zmień teren na trawę dla testu
                    tile.terrain_type = TerrainType.GRASS
                    can_build, reason = engine.can_build(x, y, house)
                    if can_build:
                        build_x, build_y = x, y
                        break
            if build_x is not None:
                break
    
    assert build_x is not None, f"No suitable terrain found for building. Terrain types: {terrain_types}"
    assert build_y is not None, "No suitable terrain found for building"

    # Sprawdź czy można budować
    can_build, reason = engine.can_build(build_x, build_y, house)
    assert can_build, f"Cannot build: {reason}"

    # Postaw budynek
    success = engine.place_building(build_x, build_y, house)
    assert success

    # Sprawdź czy budynek został postawiony
    tile = engine.city_map.get_tile(build_x, build_y)
    assert tile.building is not None
    assert tile.building.name == "House"

if __name__ == "__main__":
    pytest.main([__file__]) 