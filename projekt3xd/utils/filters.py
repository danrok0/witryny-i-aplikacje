from typing import List, Dict, Any, Callable, Optional
from functools import reduce

class BaseFilter:
    """Bazowa klasa dla filtrów."""
    
    @staticmethod
    def apply_filters(items: List[Dict[str, Any]], 
                     filters: List[Callable]) -> List[Dict[str, Any]]:
        """Aplikuje listę filtrów do listy elementów."""
        return reduce(
            lambda items, filter_func: list(filter(filter_func, items)),
            filters,
            items
        )

class TrailsFilter(BaseFilter):
    """Klasa do filtrowania szlaków turystycznych."""

    @classmethod
    def filter_by_criteria(cls,
                         trails: List[Dict[str, Any]],
                         region: Optional[str] = None,
                         min_length: Optional[float] = None,
                         max_length: Optional[float] = None,
                         difficulty: Optional[int] = None,
                         terrain_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filtruje szlaki na podstawie wielu kryteriów używając programowania funkcyjnego."""
        filter_functions = []
        
        if region:
            filter_functions.append(
                lambda trail: trail['region'].lower() == region.lower()
            )
            
        if min_length is not None:
            filter_functions.append(
                lambda trail: trail['length_km'] >= min_length
            )
            
        if max_length is not None:
            filter_functions.append(
                lambda trail: trail['length_km'] <= max_length
            )
            
        if difficulty is not None:
            filter_functions.append(
                lambda trail: trail['difficulty'] == difficulty
            )
            
        if terrain_type is not None:
            filter_functions.append(
                lambda trail: trail.get('terrain_type', '').lower() == terrain_type.lower()
            )
            
        return cls.apply_filters(trails, filter_functions)
    
    @classmethod
    def filter_by_weather(cls,
                         trails: List[Dict[str, Any]],
                         weather: Dict[str, Any],
                         max_precipitation: Optional[float] = None,
                         min_temperature: Optional[float] = None,
                         max_temperature: Optional[float] = None,
                         min_sunshine: Optional[float] = None) -> List[Dict[str, Any]]:
        """Filtruje szlaki na podstawie warunków pogodowych."""
        filter_functions = []
        
        if max_precipitation is not None:
            filter_functions.append(
                lambda _: weather.get('precipitation', 0) <= max_precipitation
            )
            
        if min_temperature is not None:
            filter_functions.append(
                lambda _: weather.get('temperature_min', 0) >= min_temperature
            )
            
        if max_temperature is not None:
            filter_functions.append(
                lambda _: weather.get('temperature_max', 0) <= max_temperature
            )
            
        if min_sunshine is not None:
            filter_functions.append(
                lambda _: weather.get('sunshine_hours', 0) >= min_sunshine
            )
            
        return cls.apply_filters(trails, filter_functions)