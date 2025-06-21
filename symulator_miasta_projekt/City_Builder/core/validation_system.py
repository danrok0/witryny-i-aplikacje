"""
Kompleksowy system walidacji i zabezpieczeń dla City Builder
Zapewnia bezpieczeństwo danych, walidację wejść użytkownika i ochronę przed błędami
"""

import re
import json
import math
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import logging
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """
    Wynik walidacji danych.
    
    Attributes:
        is_valid (bool): czy walidacja przeszła pomyślnie
        errors (List[str]): lista błędów krytycznych
        warnings (List[str]): lista ostrzeżeń (nie blokują operacji)
        cleaned_data (Any): oczyszczone i zwalidowane dane
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Any] = None

class ValidationSystem:
    """
    Centralny system walidacji dla całej aplikacji City Builder.
    
    Zapewnia:
    - Walidację danych wejściowych użytkownika
    - Sanityzację tekstu i nazw plików
    - Sprawdzanie limitów numerycznych
    - Walidację struktury JSON
    - Ochronę przed atakami injection
    """
    
    def __init__(self):
        """
        Inicjalizuje system walidacji z wzorcami regex i limitami.
        
        Tworzy:
        - Słownik wzorców regex dla różnych typów danych
        - Limity numeryczne dla wszystkich wartości w grze
        - Logger do rejestrowania błędów walidacji
        """
        self.logger = logging.getLogger('validation')
        
        # Wzorce walidacji - wyrażenia regularne (regex) do sprawdzania formatów
        # Regex to sposób opisywania wzorców tekstu, np. ^[A-Z]+$ oznacza "tylko wielkie litery"
        self.patterns = {
            # Podstawowe wzorce tekstowe
            'city_name': re.compile(r'^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-]{2,50}$'),  # nazwa miasta: litery, spacje, myślniki, 2-50 znaków
            'player_name': re.compile(r'^[A-Za-z0-9ĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-\.]{2,30}$'),  # nazwa gracza: + cyfry i kropki
            'save_filename': re.compile(r'^[A-Za-z0-9_\-\s]{1,50}$'),  # nazwa pliku zapisu: bezpieczne znaki
            'building_name': re.compile(r'^[A-Za-z0-9\s\-_]{2,30}$'),  # nazwa budynku
            
            # Wzorce numeryczne
            'coordinates': re.compile(r'^(\d{1,3}),(\d{1,3})$'),  # współrzędne "x,y" - max 3 cyfry każda
            'money_amount': re.compile(r'^-?\d{1,12}(\.\d{1,2})?$'),  # kwota pieniędzy: opcjonalny minus, max 12 cyfr, max 2 miejsca po przecinku
            'percentage': re.compile(r'^(100|[0-9]{1,2})(\.\d{1,2})?$'),  # procent 0-100 z miejscami dziesiętnymi
            'population': re.compile(r'^[0-9]{1,8}$'),  # populacja: tylko dodatnie liczby, max 8 cyfr
            'positive_int': re.compile(r'^[1-9]\d*$'),  # dodatnia liczba całkowita (nie zero)
            'non_negative_int': re.compile(r'^(0|[1-9]\d*)$'),  # nieujemna liczba całkowita (włącznie z zerem)
            'positive_float': re.compile(r'^[0-9]*\.?[0-9]+$'),  # dodatnia liczba zmiennoprzecinkowa
            
            # Wzorce dat i czasu (format ISO)
            'date_iso': re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # data YYYY-MM-DD
            'datetime_iso': re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'),  # data i czas ISO
            
            # Wzorce konfiguracyjne
            'difficulty': re.compile(r'^(Easy|Normal|Hard|Extreme)$'),  # poziomy trudności
            'log_level': re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$'),  # poziomy logowania
            'map_size': re.compile(r'^(\d{2,3})x(\d{2,3})$'),  # rozmiar mapy "50x50"
            
            # Wzorce bezpieczeństwa - zapobiegają atakom
            'safe_filename': re.compile(r'^[A-Za-z0-9_\-\s\.]{1,255}$'),  # bezpieczna nazwa pliku
            'safe_path': re.compile(r'^[A-Za-z0-9_\-\s\./\\]+$'),  # bezpieczna ścieżka
            'json_key': re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$'),  # klucz JSON (jak nazwa zmiennej)
        }
        
        # Limity walidacji - minimalne i maksymalne wartości dla różnych typów danych
        # Zapobiegają wprowadzaniu niemożliwych wartości (np. ujemna populacja)
        self.limits = {
            'money': {'min': -999999999, 'max': 999999999},  # pieniądze mogą być ujemne (długi)
            'population': {'min': 0, 'max': 99999999},  # populacja zawsze dodatnia
            'coordinates': {'min': 0, 'max': 999},  # współrzędne mapy
            'percentage': {'min': 0, 'max': 100},  # procenty 0-100%
            'map_size': {'min': 10, 'max': 500},  # rozmiar mapy w kafelkach
            'city_level': {'min': 1, 'max': 50},  # poziom miasta
            'turn': {'min': 0, 'max': 999999},  # numer tury
            'building_cost': {'min': 0, 'max': 999999},  # koszt budynku
            'satisfaction': {'min': 0, 'max': 100},  # zadowolenie mieszkańców
            'unemployment': {'min': 0, 'max': 100},  # bezrobocie w procentach
            'tax_rate': {'min': 0, 'max': 1},  # stawka podatkowa 0-1 (0-100%)
            'resource_amount': {'min': 0, 'max': 999999},  # ilość zasobów
            'string_length': {'min': 1, 'max': 255},  # długość tekstu
            'filename_length': {'min': 1, 'max': 50},  # długość nazwy pliku
            'city_name_length': {'min': 2, 'max': 50},  # długość nazwy miasta
        }
    
    def validate_input_data(self, data: Dict[str, Any], schema: Dict[str, str]) -> ValidationResult:
        """
        Waliduje dane wejściowe według podanego schematu.
        
        Args:
            data: słownik danych do walidacji {nazwa_pola: wartość}
            schema: schemat walidacji {nazwa_pola: typ_walidacji}
                   typy mogą kończyć się na "_required" dla pól obowiązkowych
            
        Returns:
            ValidationResult: wynik walidacji z błędami, ostrzeżeniami i oczyszczonymi danymi
            
        Example:
            data = {"city_name": "Warszawa", "population": "1000000"}
            schema = {"city_name": "city_name_required", "population": "population"}
            result = validator.validate_input_data(data, schema)
        """
        errors = []  # lista błędów krytycznych
        warnings = []  # lista ostrzeżeń
        cleaned_data = {}  # oczyszczone dane
        
        # Przejdź przez każde pole w schemacie
        for field_name, validation_type in schema.items():
            # Sprawdź czy pole istnieje w danych
            if field_name not in data:
                if validation_type.endswith('_required'):
                    errors.append(f"Wymagane pole {field_name} jest puste")
                    continue
                else:
                    warnings.append(f"Opcjonalne pole {field_name} nie zostało podane")
                    continue
            
            # Waliduj pojedyncze pole
            value = data[field_name]
            result = self._validate_single_field(field_name, value, validation_type)
            
            if not result.is_valid:
                errors.extend(result.errors)  # extend dodaje wszystkie elementy z listy
            else:
                cleaned_data[field_name] = result.cleaned_data
                
            warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,  # walidacja OK gdy brak błędów
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data
        )
    
    def _validate_single_field(self, field_name: str, value: Any, validation_type: str) -> ValidationResult:
        """
        Waliduje pojedyncze pole danych.
        
        Args:
            field_name: nazwa pola (do komunikatów błędów)
            value: wartość do walidacji
            validation_type: typ walidacji (może kończyć się na "_required")
            
        Returns:
            ValidationResult: wynik walidacji pojedynczego pola
            
        Metoda prywatna (prefix _) - używana tylko wewnątrz klasy
        """
        errors = []
        warnings = []
        cleaned_value = value
        
        # Usuń suffix _required z typu walidacji
        clean_type = validation_type.replace('_required', '')
        
        try:
            # Wybierz odpowiednią metodę walidacji na podstawie typu
            # To jest przykład wzorca "strategy pattern" - różne strategie dla różnych typów
            if clean_type == 'city_name':
                cleaned_value, field_errors = self._validate_city_name(value)
            elif clean_type == 'player_name':
                cleaned_value, field_errors = self._validate_player_name(value)
            elif clean_type == 'save_filename':
                cleaned_value, field_errors = self._validate_save_filename(value)
            elif clean_type == 'money_amount':
                cleaned_value, field_errors = self._validate_money_amount(value)
            elif clean_type == 'coordinates':
                # Ta walidacja wymaga dodatkowych parametrów map_width i map_height
                # Używamy podstawowej walidacji współrzędnych
                try:
                    if isinstance(value, str):  # isinstance sprawdza typ obiektu
                        match = self.patterns['coordinates'].match(value)
                        if match:
                            # match.group(1) i match.group(2) to przechwycone grupy z regex
                            x, y = int(match.group(1)), int(match.group(2))
                            cleaned_value = (x, y)  # tuple (krotka) współrzędnych
                            field_errors = []
                        else:
                            field_errors = ["Nieprawidłowy format współrzędnych"]
                            cleaned_value = (0, 0)
                    else:
                        field_errors = ["Współrzędne muszą być w formacie 'x,y'"]
                        cleaned_value = (0, 0)
                except Exception:
                    field_errors = ["Błąd parsowania współrzędnych"]
                    cleaned_value = (0, 0)
            elif clean_type == 'percentage':
                cleaned_value, field_errors = self._validate_percentage(value)
            elif clean_type == 'population':
                cleaned_value, field_errors = self._validate_population(value)
            elif clean_type == 'positive_int':
                cleaned_value, field_errors = self._validate_positive_int(value)
            elif clean_type == 'non_negative_int':
                cleaned_value, field_errors = self._validate_non_negative_int(value)
            elif clean_type == 'positive_float':
                cleaned_value, field_errors = self._validate_positive_float(value)
            elif clean_type == 'difficulty':
                cleaned_value, field_errors = self._validate_difficulty(value)
            elif clean_type == 'map_size':
                cleaned_value, field_errors = self._validate_map_size(value)
            elif clean_type == 'safe_filename':
                cleaned_value, field_errors = self._validate_safe_filename(value)
            elif clean_type == 'json_structure':
                cleaned_value, field_errors = self._validate_json_structure(value)
            else:
                field_errors = [f"Nieznany typ walidacji: {clean_type}"]
            
            errors.extend(field_errors)
            
        except Exception as e:
            # Obsługa nieoczekiwanych błędów - zawsze lepiej złapać wyjątek niż crashować program
            errors.append(f"Błąd walidacji pola {field_name}: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_value
        )
    
    def _validate_city_name(self, value: Any) -> Tuple[str, List[str]]:
        """
        Waliduje nazwę miasta.
        
        Args:
            value: wartość do walidacji (powinna być string)
            
        Returns:
            Tuple[str, List[str]]: (oczyszczona_nazwa, lista_błędów)
            
        Sprawdza:
        - Czy to string
        - Czy ma odpowiednią długość
        - Czy zawiera tylko dozwolone znaki (litery, spacje, myślniki)
        - Sanityzuje tekst (usuwa niebezpieczne znaki)
        """
        errors = []
        
        if not isinstance(value, str):
            errors.append("Nazwa miasta musi być tekstem")
            return str(value), errors
        
        # Sanityzacja - oczyszczenie tekstu z potencjalnie niebezpiecznych znaków
        cleaned = self._sanitize_text(value)
        
        # Sprawdzenie długości
        if len(cleaned) < self.limits['city_name_length']['min']:
            errors.append(f"Nazwa miasta musi mieć co najmniej {self.limits['city_name_length']['min']} znaki")
        elif len(cleaned) > self.limits['city_name_length']['max']:
            errors.append(f"Nazwa miasta może mieć maksymalnie {self.limits['city_name_length']['max']} znaków")
        
        # Sprawdzenie wzorca
        if not self.patterns['city_name'].match(cleaned):
            errors.append("Nazwa miasta zawiera niedozwolone znaki")
        
        return cleaned, errors
    
    def _validate_player_name(self, value: Any) -> Tuple[str, List[str]]:
        """Waliduje nazwę gracza"""
        errors = []
        
        if not isinstance(value, str):
            errors.append("Nazwa gracza musi być tekstem")
            return str(value), errors
        
        cleaned = self._sanitize_text(value)
        
        if len(cleaned) < 2:
            errors.append("Nazwa gracza musi mieć co najmniej 2 znaki")
        elif len(cleaned) > 30:
            errors.append("Nazwa gracza może mieć maksymalnie 30 znaków")
        
        if not self.patterns['player_name'].match(cleaned):
            errors.append("Nazwa gracza zawiera niedozwolone znaki")
        
        return cleaned, errors
    
    def _validate_save_filename(self, value: Any) -> Tuple[str, List[str]]:
        """Waliduje nazwę pliku zapisu"""
        errors = []
        
        if not isinstance(value, str):
            errors.append("Nazwa pliku musi być tekstem")
            return str(value), errors
        
        # Sanityzacja
        cleaned = self._sanitize_filename(value)
        
        if len(cleaned) < 1:
            errors.append("Nazwa pliku nie może być pusta")
        elif len(cleaned) > self.limits['filename_length']['max']:
            errors.append(f"Nazwa pliku może mieć maksymalnie {self.limits['filename_length']['max']} znaków")
        
        # Sprawdzenie niebezpiecznych znaków
        if not self.patterns['safe_filename'].match(cleaned):
            errors.append("Nazwa pliku zawiera niedozwolone znaki")
        
        # Sprawdzenie zarezerwowanych nazw (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        if cleaned.upper() in reserved_names:
            errors.append(f"Nazwa pliku '{cleaned}' jest zarezerwowana w systemie Windows")
        
        return cleaned, errors
    
    def _validate_money_amount(self, value: Any) -> Tuple[float, List[str]]:
        """Waliduje kwotę pieniędzy"""
        errors = []
        
        try:
            # Konwersja na float
            if isinstance(value, str):
                # Usuń znaki walut i spacje
                cleaned_str = re.sub(r'[\$\€\£\¥\s,]', '', value)
                amount = float(cleaned_str)
            else:
                amount = float(value)
            
            # Sprawdzenie NaN i Infinity
            if math.isnan(amount) or math.isinf(amount):
                errors.append("Kwota pieniędzy nie może być NaN lub nieskończona")
                return 0.0, errors
            
            # Sprawdzenie limitów
            if amount < self.limits['money']['min']:
                errors.append(f"Kwota nie może być mniejsza niż {self.limits['money']['min']}")
            elif amount > self.limits['money']['max']:
                errors.append(f"Kwota nie może być większa niż {self.limits['money']['max']}")
            
            # Zaokrąglenie do 2 miejsc po przecinku
            amount = round(amount, 2)
            
        except (ValueError, TypeError):
            errors.append("Nieprawidłowa kwota pieniędzy")
            return 0.0, errors
        
        return amount, errors
    
    def validate_coordinates(self, x: Any, y: Any, map_width: int, map_height: int) -> ValidationResult:
        """Waliduje współrzędne na mapie"""
        errors = []
        warnings = []
        
        try:
            x_int = int(x)
            y_int = int(y)
        except (ValueError, TypeError):
            errors.append("Współrzędne muszą być liczbami całkowitymi")
            return ValidationResult(False, errors, warnings, (0, 0))
        
        # Sprawdzenie granic mapy
        if x_int < 0 or x_int >= map_width:
            errors.append(f"Współrzędna X ({x_int}) jest poza mapą (0-{map_width-1})")
        
        if y_int < 0 or y_int >= map_height:
            errors.append(f"Współrzędna Y ({y_int}) jest poza mapą (0-{map_height-1})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=(x_int, y_int)
        )
    
    def validate_building_data(self, building_data: Dict) -> ValidationResult:
        """Waliduje dane budynku"""
        errors = []
        warnings = []
        cleaned_data = {}
        
        # Sprawdzenie wymaganych pól
        required_fields = ['name', 'building_type', 'cost']
        for field in required_fields:
            if field not in building_data:
                errors.append(f"Brak wymaganego pola budynku: {field}")
        
        # Walidacja nazwy
        if 'name' in building_data:
            name = building_data['name']
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append("Nazwa budynku nie może być pusta")
            elif len(name) > 50:
                errors.append("Nazwa budynku może mieć maksymalnie 50 znaków")
            else:
                cleaned_data['name'] = self._sanitize_text(name)
        
        # Walidacja kosztu
        if 'cost' in building_data:
            cost_result = self.validate_money_amount(building_data['cost'])
            if cost_result.is_valid:
                if cost_result.cleaned_data < 0:
                    errors.append("Koszt budynku nie może być ujemny")
                else:
                    cleaned_data['cost'] = cost_result.cleaned_data
            else:
                errors.extend([f"Koszt budynku: {err}" for err in cost_result.errors])
        
        # Walidacja efektów (jeśli istnieją)
        if 'effects' in building_data:
            effects = building_data['effects']
            if not isinstance(effects, dict):
                errors.append("Efekty budynku muszą być słownikiem")
            else:
                cleaned_effects = {}
                for effect_name, effect_value in effects.items():
                    try:
                        cleaned_effects[effect_name] = float(effect_value)
                    except (ValueError, TypeError):
                        warnings.append(f"Efekt {effect_name} ma nieprawidłową wartość")
                cleaned_data['effects'] = cleaned_effects
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data
        )
    
    def _validate_percentage(self, value: Any) -> Tuple[float, List[str]]:
        """Waliduje procenty"""
        errors = []
        
        try:
            if isinstance(value, str):
                # Usuń znak %
                cleaned_str = value.rstrip('%')
                percent = float(cleaned_str)
            else:
                percent = float(value)
            
            if math.isnan(percent) or math.isinf(percent):
                errors.append("Procent nie może być NaN lub nieskończony")
                return 0.0, errors
            
            if percent < self.limits['percentage']['min']:
                errors.append(f"Procent nie może być mniejszy niż {self.limits['percentage']['min']}")
            elif percent > self.limits['percentage']['max']:
                errors.append(f"Procent nie może być większy niż {self.limits['percentage']['max']}")
            
            percent = round(percent, 2)
            
        except (ValueError, TypeError):
            errors.append("Nieprawidłowa wartość procentowa")
            return 0.0, errors
        
        return percent, errors
    
    def _validate_population(self, value: Any) -> Tuple[int, List[str]]:
        """Waliduje liczebność population"""
        errors = []
        
        try:
            population = int(value)
            
            if population < self.limits['population']['min']:
                errors.append(f"Populacja nie może być mniejsza niż {self.limits['population']['min']}")
            elif population > self.limits['population']['max']:
                errors.append(f"Populacja nie może być większa niż {self.limits['population']['max']}")
            
        except (ValueError, TypeError):
            errors.append("Populacja musi być liczbą całkowitą")
            return 0, errors
        
        return population, errors
    
    def _validate_positive_int(self, value: Any) -> Tuple[int, List[str]]:
        """Waliduje dodatnią liczbę całkowitą"""
        errors = []
        
        try:
            number = int(value)
            if number <= 0:
                errors.append("Wartość musi być dodatnią liczbą całkowitą")
                return 1, errors
        except (ValueError, TypeError):
            errors.append("Wartość musi być liczbą całkowitą")
            return 1, errors
        
        return number, errors
    
    def _validate_non_negative_int(self, value: Any) -> Tuple[int, List[str]]:
        """Waliduje nieujemną liczbę całkowitą"""
        errors = []
        
        try:
            number = int(value)
            if number < 0:
                errors.append("Wartość nie może być ujemna")
                return 0, errors
        except (ValueError, TypeError):
            errors.append("Wartość musi być liczbą całkowitą")
            return 0, errors
        
        return number, errors
    
    def _validate_positive_float(self, value: Any) -> Tuple[float, List[str]]:
        """Waliduje dodatnią liczbę zmiennoprzecinkową"""
        errors = []
        
        try:
            number = float(value)
            if math.isnan(number) or math.isinf(number):
                errors.append("Wartość nie może być NaN lub nieskończona")
                return 1.0, errors
            if number <= 0:
                errors.append("Wartość musi być dodatnią liczbą")
                return 1.0, errors
        except (ValueError, TypeError):
            errors.append("Wartość musi być liczbą")
            return 1.0, errors
        
        return number, errors
    
    def _validate_difficulty(self, value: Any) -> Tuple[str, List[str]]:
        """Waliduje poziom trudności"""
        errors = []
        
        if not isinstance(value, str):
            errors.append("Poziom trudności musi być tekstem")
            return "Normal", errors
        
        if not self.patterns['difficulty'].match(value):
            errors.append("Nieprawidłowy poziom trudności (dozwolone: Easy, Normal, Hard, Extreme)")
            return "Normal", errors
        
        return value, errors
    
    def _validate_map_size(self, value: Any) -> Tuple[Tuple[int, int], List[str]]:
        """Waliduje rozmiar mapy"""
        errors = []
        
        if isinstance(value, str):
            match = self.patterns['map_size'].match(value)
            if not match:
                errors.append("Nieprawidłowy format rozmiaru mapy (oczekiwano WxH)")
                return (60, 60), errors
            
            try:
                width, height = int(match.group(1)), int(match.group(2))
            except ValueError:
                errors.append("Rozmiar mapy musi składać się z liczb całkowitych")
                return (60, 60), errors
        
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            try:
                width, height = int(value[0]), int(value[1])
            except (ValueError, TypeError):
                errors.append("Rozmiar mapy musi składać się z liczb całkowitych")
                return (60, 60), errors
        else:
            errors.append("Rozmiar mapy musi być w formacie 'WxH' lub (W, H)")
            return (60, 60), errors
        
        # Sprawdzenie limitów
        size_limit = self.limits['map_size']
        if width < size_limit['min'] or width > size_limit['max']:
            errors.append(f"Szerokość mapy musi być między {size_limit['min']} a {size_limit['max']}")
        if height < size_limit['min'] or height > size_limit['max']:
            errors.append(f"Wysokość mapy musi być między {size_limit['min']} a {size_limit['max']}")
        
        return (width, height), errors
    
    def _validate_safe_filename(self, value: Any) -> Tuple[str, List[str]]:
        """Waliduje bezpieczną nazwę pliku"""
        errors = []
        
        if not isinstance(value, str):
            errors.append("Nazwa pliku musi być tekstem")
            return "safe_file", errors
        
        # Sanityzacja
        cleaned = self._sanitize_filename(value)
        
        if not self.patterns['safe_filename'].match(cleaned):
            errors.append("Nazwa pliku zawiera niedozwolone znaki")
        
        return cleaned, errors
    
    def _validate_json_structure(self, value: Any) -> Tuple[Dict, List[str]]:
        """Waliduje strukturę JSON"""
        errors = []
        
        if isinstance(value, str):
            try:
                json_data = json.loads(value)
            except json.JSONDecodeError as e:
                errors.append(f"Nieprawidłowa struktura JSON: {str(e)}")
                return {}, errors
        elif isinstance(value, dict):
            json_data = value
        else:
            errors.append("Dane JSON muszą być słownikiem lub tekstem JSON")
            return {}, errors
        
        # Sprawdzenie głębokości struktury (zabezpieczenie przed deep nesting)
        if self._get_dict_depth(json_data) > 10:
            errors.append("Struktura JSON jest zbyt głęboka (maksymalnie 10 poziomów)")
        
        return json_data, errors
    
    def _sanitize_text(self, text: str) -> str:
        """Oczyszcza tekst z niebezpiecznych znaków"""
        # Usuń znaki kontrolne
        cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # Usuń potencjalnie niebezpieczne znaki
        cleaned = re.sub(r'[<>"\']', '', cleaned)
        
        # Normalizuj białe znaki
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Oczyszcza nazwę pliku"""
        # Usuń niebezpieczne znaki
        cleaned = re.sub(r'[<>:"|?*\\\/]', '_', filename)
        
        # Usuń znaki kontrolne
        cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', cleaned)
        
        # Usuń wielokrotne spacje i podkreślenia
        cleaned = re.sub(r'[_\s]+', '_', cleaned)
        
        return cleaned.strip('_. ')
    
    def _get_dict_depth(self, d: Dict, depth: int = 0) -> int:
        """Oblicza głębokość zagnieżdżenia słownika"""
        if not isinstance(d, dict):
            return depth
        
        max_depth = depth
        for value in d.values():
            if isinstance(value, dict):
                max_depth = max(max_depth, self._get_dict_depth(value, depth + 1))
        
        return max_depth
    
    def validate_save_filename(self, filename: str) -> ValidationResult:
        """Waliduje nazwę pliku zapisu"""
        errors = []
        warnings = []
        
        if not filename:
            errors.append("Nazwa pliku nie może być pusta")
            return ValidationResult(False, errors, warnings, "")
        
        # Sanityzacja
        cleaned = self._sanitize_filename(filename)
        
        # Sprawdzenie długości
        if len(cleaned) > self.limits['filename_length']['max']:
            errors.append(f"Nazwa pliku może mieć maksymalnie {self.limits['filename_length']['max']} znaków")
        
        # Sprawdzenie bezpiecznych znaków
        if not self.patterns['safe_filename'].match(cleaned):
            warnings.append("Niektóre znaki zostały usunięte dla bezpieczeństwa")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned
        )
    
    def validate_json_file(self, file_path: str) -> ValidationResult:
        """Waliduje plik JSON"""
        errors = []
        warnings = []
        data = {}
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                errors.append(f"Plik nie istnieje: {file_path}")
                return ValidationResult(False, errors, warnings, {})
            
            # Sprawdzenie rozszerzenia
            if path.suffix.lower() != '.json':
                warnings.append("Plik nie ma rozszerzenia .json")
            
            # Sprawdzenie rozmiaru pliku
            file_size = path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB
                errors.append("Plik jest za duży (maksymalnie 50MB)")
                return ValidationResult(False, errors, warnings, {})
            
            # Odczyt i parsowanie
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Sprawdzenie czy plik nie jest pusty
            if not content.strip():
                errors.append("Plik jest pusty")
                return ValidationResult(False, errors, warnings, {})
            
            # Parsowanie JSON
            data = json.loads(content)
            
            # Sprawdzenie głębokości struktury
            if self._get_dict_depth(data) > 10:
                warnings.append("Bardzo głęboka struktura danych może wpływać na wydajność")
            
        except json.JSONDecodeError as e:
            errors.append(f"Błąd parsowania JSON: {str(e)}")
        except UnicodeDecodeError:
            errors.append("Błąd kodowania pliku - użyj UTF-8")
        except Exception as e:
            errors.append(f"Błąd odczytu pliku: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=data
        )
    
    def validate_money_amount(self, amount: Any) -> ValidationResult:
        """Waliduje kwotę pieniędzy"""
        errors = []
        warnings = []
        
        try:
            if isinstance(amount, str):
                # Usuń znaki walut i spacje
                cleaned_str = re.sub(r'[\$\€\£\¥\s,]', '', amount)
                amount_float = float(cleaned_str)
            else:
                amount_float = float(amount)
            
            # Sprawdzenie NaN i Infinity
            if math.isnan(amount_float) or math.isinf(amount_float):
                errors.append("Kwota nie może być NaN lub nieskończona")
                return ValidationResult(False, errors, warnings, 0.0)
            
            # Sprawdzenie limitów
            if amount_float < self.limits['money']['min']:
                errors.append(f"Kwota nie może być mniejsza niż {self.limits['money']['min']:,}")
            elif amount_float > self.limits['money']['max']:
                errors.append(f"Kwota nie może być większa niż {self.limits['money']['max']:,}")
            
            # Zaokrąglenie do 2 miejsc po przecinku
            amount_float = round(amount_float, 2)
            
        except (ValueError, TypeError):
            errors.append("Nieprawidłowa kwota pieniędzy")
            return ValidationResult(False, errors, warnings, 0.0)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=amount_float
        )
    
    def validate_population(self, population: Any) -> ValidationResult:
        """Waliduje liczebność populacji"""
        errors = []
        warnings = []
        
        try:
            pop_int = int(population)
            
            if pop_int < self.limits['population']['min']:
                errors.append(f"Populacja nie może być mniejsza niż {self.limits['population']['min']}")
            elif pop_int > self.limits['population']['max']:
                errors.append(f"Populacja nie może być większa niż {self.limits['population']['max']:,}")
            
        except (ValueError, TypeError):
            errors.append("Populacja musi być liczbą całkowitą")
            return ValidationResult(False, errors, warnings, 0)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=pop_int
        )
    
    def validate_tax_rate(self, rate: Any) -> ValidationResult:
        """Waliduje stawkę podatkową"""
        errors = []
        
        try:
            rate_float = float(rate)
            
            if math.isnan(rate_float) or math.isinf(rate_float):
                errors.append("Stawka podatkowa nie może być NaN lub nieskończona")
                return ValidationResult(False, errors, [], 0.0)
            
            if rate_float < self.limits['tax_rate']['min']:
                errors.append(f"Stawka podatkowa nie może być mniejsza niż {self.limits['tax_rate']['min']}")
            elif rate_float > self.limits['tax_rate']['max']:
                errors.append(f"Stawka podatkowa nie może być większa niż {self.limits['tax_rate']['max']}")
            
            rate_float = round(rate_float, 4)  # Precyzja do 4 miejsc po przecinku
            
        except (ValueError, TypeError):
            errors.append("Stawka podatkowa musi być liczbą")
            return ValidationResult(False, errors, [], 0.0)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            cleaned_data=rate_float
        )
    
    def validate_game_save_data(self, save_data: Dict) -> ValidationResult:
        """Waliduje dane zapisu gry"""
        schema = {
            'version': 'safe_filename',
            'turn': 'non_negative_int_required',
            'difficulty': 'difficulty_required',
            'city_level': 'positive_int',
            'map': 'json_structure_required',
            'economy': 'json_structure_required',
            'population': 'json_structure_required'
        }
        
        return self.validate_input_data(save_data, schema)
    
    def validate_building_placement(self, x: int, y: int, building_data: Dict, 
                                  map_width: int, map_height: int) -> ValidationResult:
        """Waliduje umieszczenie budynku"""
        errors = []
        warnings = []
        
        # Sprawdzenie współrzędnych
        if x < 0 or x >= map_width:
            errors.append(f"Współrzędna X ({x}) jest poza mapą (0-{map_width-1})")
        if y < 0 or y >= map_height:
            errors.append(f"Współrzędna Y ({y}) jest poza mapą (0-{map_height-1})")
        
        # Sprawdzenie danych budynku
        if not isinstance(building_data, dict):
            errors.append("Dane budynku muszą być słownikiem")
        else:
            required_fields = ['name', 'building_type', 'cost']
            for field in required_fields:
                if field not in building_data:
                    errors.append(f"Brak wymaganego pola budynku: {field}")
            
            # Walidacja kosztu
            if 'cost' in building_data:
                cost_result = self._validate_money_amount(building_data['cost'])
                if not cost_result[1]:  # Brak błędów
                    if cost_result[0] < 0:
                        errors.append("Koszt budynku nie może być ujemny")
                else:
                    errors.extend(cost_result[1])
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_economic_data(self, economy_data: Dict) -> ValidationResult:
        """Waliduje dane ekonomiczne"""
        errors = []
        warnings = []
        
        # Sprawdzenie struktury
        required_fields = ['resources', 'tax_rates']
        for field in required_fields:
            if field not in economy_data:
                errors.append(f"Brak wymaganego pola ekonomii: {field}")
        
        # Walidacja zasobów
        if 'resources' in economy_data:
            resources = economy_data['resources']
            if not isinstance(resources, dict):
                errors.append("Zasoby muszą być słownikiem")
            else:
                for resource_name, resource_data in resources.items():
                    if not isinstance(resource_data, dict):
                        errors.append(f"Dane zasobu {resource_name} muszą być słownikiem")
                        continue
                    
                    # Sprawdzenie kwoty
                    if 'amount' in resource_data:
                        amount_result = self._validate_money_amount(resource_data['amount'])
                        if amount_result[1]:  # Są błędy
                            errors.extend([f"Zasób {resource_name}: {err}" for err in amount_result[1]])
        
        # Walidacja stawek podatkowych
        if 'tax_rates' in economy_data:
            tax_rates = economy_data['tax_rates']
            if not isinstance(tax_rates, dict):
                errors.append("Stawki podatkowe muszą być słownikiem")
            else:
                for tax_type, rate in tax_rates.items():
                    try:
                        rate_float = float(rate)
                        if rate_float < 0 or rate_float > 1:
                            errors.append(f"Stawka podatkowa {tax_type} musi być między 0 a 1")
                    except (ValueError, TypeError):
                        errors.append(f"Stawka podatkowa {tax_type} musi być liczbą")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# Singleton instance
_validation_system = None

def get_validation_system() -> ValidationSystem:
    """Pobiera singleton systemu walidacji"""
    global _validation_system
    if _validation_system is None:
        _validation_system = ValidationSystem()
    return _validation_system 