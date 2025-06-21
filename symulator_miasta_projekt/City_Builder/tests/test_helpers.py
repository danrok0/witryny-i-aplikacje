"""
Funkcje pomocnicze dla testów
"""
import sys
import os

# Dodaj ścieżkę do modułów projektu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.tile import TerrainType

def find_buildable_location(engine, start_x=0, start_y=0):
    """Znajdź odpowiednie miejsce do budowania (nie woda, nie góry)"""
    for x in range(start_x, engine.city_map.width):
        for y in range(start_y, engine.city_map.height):
            tile = engine.city_map.get_tile(x, y)
            if (tile and 
                tile.terrain_type not in [TerrainType.WATER, TerrainType.MOUNTAIN] and
                not tile.is_occupied):
                return x, y
    return None, None

def find_multiple_buildable_locations(engine, count):
    """Znajdź wiele miejsc do budowania"""
    locations = []
    x, y = 0, 0
    
    for _ in range(count):
        x, y = find_buildable_location(engine, x, y)
        if x is None:
            break
        locations.append((x, y))
        
        # Przejdź do następnej pozycji
        y += 1
        if y >= engine.city_map.height:
            y = 0
            x += 1
    
    return locations

def place_building_safely(engine, building, x=None, y=None):
    """Postaw budynek w bezpiecznym miejscu"""
    if x is None or y is None:
        x, y = find_buildable_location(engine)
        if x is None:
            return False
    
    success = engine.place_building(x, y, building)
    return success 