"""
Moduł podstawowych walidatorów dla systemu rekomendacji tras turystycznych.
Centralizuje podstawowe funkcje walidacyjne używane w całym projekcie.
"""

from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Wyjątek dla błędów walidacji."""
    pass

class BasicValidators:
    """Klasa zawierająca podstawowe walidatory."""
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str = "pole") -> Any:
        """
        Waliduje czy wartość nie jest pusta.
        
        Args:
            value: Wartość do sprawdzenia
            field_name: Nazwa pola (dla komunikatu błędu)
            
        Returns:
            Wartość jeśli jest poprawna
            
        Raises:
            ValidationError: Jeśli wartość jest pusta
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} nie może być pusty")
        return value
    
    @staticmethod
    def validate_string(value: Any, field_name: str = "pole", min_length: int = 1, max_length: int = 1000) -> str:
        """
        Waliduje string.
        
        Args:
            value: Wartość do sprawdzenia
            field_name: Nazwa pola
            min_length: Minimalna długość
            max_length: Maksymalna długość
            
        Returns:
            String jeśli jest poprawny
            
        Raises:
            ValidationError: Jeśli wartość nie jest prawidłowym stringiem
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} musi być tekstem")
        
        if len(value.strip()) < min_length:
            raise ValidationError(f"{field_name} musi mieć co najmniej {min_length} znaków")
        
        if len(value) > max_length:
            raise ValidationError(f"{field_name} może mieć maksymalnie {max_length} znaków")
        
        return value.strip()
    
    @staticmethod
    def validate_number(value: Any, field_name: str = "pole", min_val: float = None, max_val: float = None) -> float:
        """
        Waliduje liczbę.
        
        Args:
            value: Wartość do sprawdzenia
            field_name: Nazwa pola
            min_val: Minimalna wartość
            max_val: Maksymalna wartość
            
        Returns:
            Float jeśli jest poprawny
            
        Raises:
            ValidationError: Jeśli wartość nie jest liczbą lub jest poza zakresem
        """
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} musi być liczbą")
        
        if min_val is not None and num_value < min_val:
            raise ValidationError(f"{field_name} musi być co najmniej {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValidationError(f"{field_name} może być maksymalnie {max_val}")
        
        return num_value
    
    @staticmethod
    def validate_integer(value: Any, field_name: str = "pole", min_val: int = None, max_val: int = None) -> int:
        """
        Waliduje liczbę całkowitą.
        
        Args:
            value: Wartość do sprawdzenia
            field_name: Nazwa pola
            min_val: Minimalna wartość
            max_val: Maksymalna wartość
            
        Returns:
            Int jeśli jest poprawny
            
        Raises:
            ValidationError: Jeśli wartość nie jest liczbą całkowitą lub jest poza zakresem
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} musi być liczbą całkowitą")
        
        if min_val is not None and int_value < min_val:
            raise ValidationError(f"{field_name} musi być co najmniej {min_val}")
        
        if max_val is not None and int_value > max_val:
            raise ValidationError(f"{field_name} może być maksymalnie {max_val}")
        
        return int_value
    
    @staticmethod
    def validate_coordinates(lat: Any, lon: Any) -> tuple[float, float]:
        """
        Waliduje współrzędne geograficzne.
        
        Args:
            lat: Szerokość geograficzna
            lon: Długość geograficzna
            
        Returns:
            Tuple z walidowanymi współrzędnymi
            
        Raises:
            ValidationError: Jeśli współrzędne są nieprawidłowe
        """
        try:
            lat_float = float(lat)
            lon_float = float(lon)
        except (ValueError, TypeError):
            raise ValidationError("Współrzędne muszą być liczbami")
        
        if not (-90 <= lat_float <= 90):
            raise ValidationError("Szerokość geograficzna musi być między -90 a 90")
        
        if not (-180 <= lon_float <= 180):
            raise ValidationError("Długość geograficzna musi być między -180 a 180")
        
        return lat_float, lon_float
    
    @staticmethod
    def validate_date(date_str: str, field_name: str = "data") -> datetime:
        """
        Waliduje format daty.
        
        Args:
            date_str: String z datą w formacie YYYY-MM-DD
            field_name: Nazwa pola
            
        Returns:
            Obiekt datetime
            
        Raises:
            ValidationError: Jeśli data ma nieprawidłowy format
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(f"{field_name} musi być w formacie YYYY-MM-DD")
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], field_name: str = "pole") -> Any:
        """
        Waliduje czy wartość jest jedną z dozwolonych opcji.
        
        Args:
            value: Wartość do sprawdzenia
            choices: Lista dozwolonych wartości
            field_name: Nazwa pola
            
        Returns:
            Wartość jeśli jest w dozwolonych opcjach
            
        Raises:
            ValidationError: Jeśli wartość nie jest dozwolona
        """
        if value not in choices:
            raise ValidationError(f"{field_name} musi być jedną z opcji: {', '.join(map(str, choices))}")
        return value

class TrailValidators:
    """Walidatory specyficzne dla tras turystycznych."""
    
    @staticmethod
    def validate_trail_data(trail_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Waliduje kompletne dane trasy.
        
        Args:
            trail_data: Słownik z danymi trasy
            
        Returns:
            Zwalidowane dane trasy
            
        Raises:
            ValidationError: Jeśli dane są nieprawidłowe
        """
        if not isinstance(trail_data, dict):
            raise ValidationError("Dane trasy muszą być słownikiem")
        
        validated = {}
        
        # Wymagane pola tekstowe
        validated['name'] = BasicValidators.validate_string(
            trail_data.get('name'), 'nazwa trasy', min_length=2, max_length=200
        )
        
        # Współrzędne (wymagane)
        if 'start_lat' not in trail_data or 'start_lon' not in trail_data:
            raise ValidationError("Współrzędne startu są wymagane")
        
        validated['start_lat'], validated['start_lon'] = BasicValidators.validate_coordinates(
            trail_data['start_lat'], trail_data['start_lon']
        )
        
        # Długość trasy
        if 'length_km' in trail_data:
            validated['length_km'] = BasicValidators.validate_number(
                trail_data['length_km'], 'długość trasy', min_val=0, max_val=1000
            )
        
        # Trudność
        if 'difficulty' in trail_data:
            validated['difficulty'] = BasicValidators.validate_integer(
                trail_data['difficulty'], 'trudność', min_val=1, max_val=5
            )
        
        # Typ terenu
        if 'terrain_type' in trail_data:
            terrain_choices = ['górski', 'leśny', 'nizinny', 'miejski', 'mieszany']
            validated['terrain_type'] = BasicValidators.validate_choice(
                trail_data['terrain_type'].lower(), terrain_choices, 'typ terenu'
            )
        
        # Kategoria
        if 'category' in trail_data:
            category_choices = ['rodzinna', 'widokowa', 'sportowa', 'ekstremalna']
            validated['category'] = BasicValidators.validate_choice(
                trail_data['category'].lower(), category_choices, 'kategoria'
            )
        
        # Ocena użytkowników
        if 'user_rating' in trail_data:
            validated['user_rating'] = BasicValidators.validate_number(
                trail_data['user_rating'], 'ocena', min_val=1.0, max_val=5.0
            )
        
        return validated

class WeatherValidators:
    """Walidatory dla danych pogodowych."""
    
    @staticmethod
    def validate_weather_data(weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Waliduje dane pogodowe.
        
        Args:
            weather_data: Słownik z danymi pogodowymi
            
        Returns:
            Zwalidowane dane pogodowe
            
        Raises:
            ValidationError: Jeśli dane są nieprawidłowe
        """
        if not isinstance(weather_data, dict):
            raise ValidationError("Dane pogodowe muszą być słownikiem")
        
        validated = {}
        
        # Temperatura
        if 'temperature' in weather_data:
            validated['temperature'] = BasicValidators.validate_number(
                weather_data['temperature'], 'temperatura', min_val=-50, max_val=50
            )
        
        # Opady
        if 'precipitation' in weather_data:
            validated['precipitation'] = BasicValidators.validate_number(
                weather_data['precipitation'], 'opady', min_val=0, max_val=500
            )
        
        # Prędkość wiatru
        if 'wind_speed' in weather_data:
            validated['wind_speed'] = BasicValidators.validate_number(
                weather_data['wind_speed'], 'prędkość wiatru', min_val=0, max_val=200
            )
        
        # Data
        if 'date' in weather_data:
            if isinstance(weather_data['date'], str):
                validated['date'] = BasicValidators.validate_date(weather_data['date'])
            else:
                validated['date'] = weather_data['date']
        
        return validated

# Funkcje pomocnicze do szybkiego użycia
def safe_validate(validator_func, *args, **kwargs):
    """
    Bezpieczna walidacja - zwraca None zamiast rzucać wyjątek.
    
    Args:
        validator_func: Funkcja walidacyjna
        *args: Argumenty funkcji
        **kwargs: Argumenty nazwane funkcji
        
    Returns:
        Wynik walidacji lub None w przypadku błędu
    """
    try:
        return validator_func(*args, **kwargs)
    except ValidationError as e:
        logger.warning(f"Błąd walidacji: {e}")
        return None
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd walidacji: {e}")
        return None

def validate_or_default(validator_func, default_value, *args, **kwargs):
    """
    Walidacja z wartością domyślną.
    
    Args:
        validator_func: Funkcja walidacyjna
        default_value: Wartość domyślna
        *args: Argumenty funkcji
        **kwargs: Argumenty nazwane funkcji
        
    Returns:
        Wynik walidacji lub wartość domyślna
    """
    result = safe_validate(validator_func, *args, **kwargs)
    return result if result is not None else default_value 