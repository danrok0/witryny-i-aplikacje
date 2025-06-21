"""
Moduł walidacji danych z wykorzystaniem wyrażeń regularnych
Implementuje zaawansowane walidacje dla wszystkich typów danych w grze
"""

import re
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import logging
from datetime import datetime

class DataValidator:
    """Klasa do walidacji danych z wykorzystaniem wyrażeń regularnych"""
    
    def __init__(self):
        """Inicjalizuje walidator z predefiniowanymi wzorcami regex"""
        
        # Wzorce dla podstawowych typów danych
        self.patterns = {
            # Identyfikatory i nazwy
            'city_name': re.compile(r'^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-]{2,50}$'),
            'building_id': re.compile(r'^[a-z_][a-z0-9_]{2,30}$'),
            'player_name': re.compile(r'^[A-Za-z0-9ĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-\.]{2,30}$'),
            'save_filename': re.compile(r'^[A-Za-z0-9_\-]{1,50}\.json$'),
            
            # Współrzędne i pozycje
            'coordinates': re.compile(r'^(\d{1,3}),(\d{1,3})$'),
            'map_size': re.compile(r'^(\d{2,3})x(\d{2,3})$'),
            'position_range': re.compile(r'^(\d+)-(\d+)$'),
            
            # Wartości numeryczne
            'money_amount': re.compile(r'^-?\d{1,12}(\.\d{2})?$'),
            'percentage': re.compile(r'^(100|[0-9]{1,2})(\.\d{1,2})?%?$'),
            'population_count': re.compile(r'^[0-9]{1,8}$'),
            'resource_amount': re.compile(r'^[0-9]{1,10}(\.\d{1,3})?$'),
            
            # Daty i czas
            'date_iso': re.compile(r'^\d{4}-\d{2}-\d{2}$'),
            'datetime_iso': re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'),
            'game_time': re.compile(r'^(\d{1,4}):(\d{1,2}):(\d{1,2})$'),
            
            # Konfiguracja i ustawienia
            'difficulty_level': re.compile(r'^(Easy|Normal|Hard|Extreme)$'),
            'language_code': re.compile(r'^(pl|en|de|fr|es)$'),
            'color_hex': re.compile(r'^#[0-9A-Fa-f]{6}$'),
            'version_number': re.compile(r'^\d+\.\d+\.\d+$'),
            
            # Ścieżki plików
            'file_path': re.compile(r'^[A-Za-z]:[\\\/](?:[^<>:"|?*\r\n]+[\\\/])*[^<>:"|?*\r\n]*$'),
            'relative_path': re.compile(r'^(?:\.\.?[\\\/])*[^<>:"|?*\r\n\\\/]+(?:[\\\/][^<>:"|?*\r\n\\\/]+)*$'),
            
            # Email i URL (dla przyszłych funkcji multiplayer)
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'),
            
            # Specjalne wzorce dla gry
            'building_type': re.compile(r'^(residential|commercial|industrial|public|infrastructure)$'),
            'resource_type': re.compile(r'^(money|energy|water|materials|food|luxury_goods)$'),
            'event_type': re.compile(r'^(disaster|economic|social|political|technological)$'),
            
            # Wzorce dla importu/eksportu danych
            'csv_line': re.compile(r'^(?:"[^"]*"|[^,]*)(?:,(?:"[^"]*"|[^,]*))*$'),
            'json_key': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$'),
            'xml_tag': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-]*$'),
        }
        
        # Wzorce złożone dla walidacji struktur danych
        self.complex_patterns = {
            'building_config': re.compile(
                r'^{.*"id":\s*"[a-z_][a-z0-9_]*".*"cost":\s*\d+.*"type":\s*"(residential|commercial|industrial|public|infrastructure)".*}$',
                re.DOTALL
            ),
            'save_game_header': re.compile(
                r'^{.*"version":\s*"\d+\.\d+\.\d+".*"timestamp":\s*"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}".*"city_name":\s*"[^"]{2,50}".*}$',
                re.DOTALL
            ),
        }
        
        self.logger = logging.getLogger(__name__)
    
    def validate_field(self, field_name: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Waliduje pojedyncze pole używając odpowiedniego wzorca regex
        
        Args:
            field_name: Nazwa pola do walidacji
            value: Wartość do sprawdzenia
            
        Returns:
            Tuple[bool, Optional[str]]: (czy_poprawne, komunikat_błędu)
        """
        if field_name not in self.patterns:
            return False, f"Nieznany typ pola: {field_name}"
        
        pattern = self.patterns[field_name]
        
        if not isinstance(value, str):
            value = str(value)
        
        if pattern.match(value):
            return True, None
        else:
            return False, f"Niepoprawny format dla {field_name}: {value}"
    
    def validate_coordinates(self, coord_string: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Waliduje i parsuje współrzędne"""
        match = self.patterns['coordinates'].match(coord_string)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            if 0 <= x <= 999 and 0 <= y <= 999:
                return True, (x, y)
        return False, None
    
    def validate_map_size(self, size_string: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Waliduje i parsuje rozmiar mapy"""
        match = self.patterns['map_size'].match(size_string)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            if 20 <= width <= 200 and 20 <= height <= 200:
                return True, (width, height)
        return False, None
    
    def validate_money_amount(self, amount_string: str) -> Tuple[bool, Optional[float]]:
        """Waliduje i parsuje kwotę pieniędzy"""
        match = self.patterns['money_amount'].match(amount_string)
        if match:
            try:
                amount = float(amount_string)
                if -999999999999 <= amount <= 999999999999:
                    return True, amount
            except ValueError:
                pass
        return False, None
    
    def validate_percentage(self, percent_string: str) -> Tuple[bool, Optional[float]]:
        """Waliduje i parsuje procenty"""
        # Usuń znak % jeśli istnieje
        clean_string = percent_string.rstrip('%')
        match = self.patterns['percentage'].match(percent_string)
        if match:
            try:
                percent = float(clean_string)
                if 0 <= percent <= 100:
                    return True, percent
            except ValueError:
                pass
        return False, None
    
    def validate_game_data_structure(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Waliduje całą strukturę danych gry
        
        Args:
            data: Słownik z danymi gry
            
        Returns:
            Tuple[bool, List[str]]: (czy_poprawne, lista_błędów)
        """
        errors = []
        
        # Sprawdź wymagane pola
        required_fields = {
            'city_name': 'city_name',
            'version': 'version_number',
            'timestamp': 'datetime_iso',
            'difficulty': 'difficulty_level'
        }
        
        for field, pattern_name in required_fields.items():
            if field not in data:
                errors.append(f"Brakuje wymaganego pola: {field}")
            else:
                is_valid, error = self.validate_field(pattern_name, str(data[field]))
                if not is_valid:
                    errors.append(f"Błąd w polu {field}: {error}")
        
        # Sprawdź struktury zagnieżdżone
        if 'buildings' in data and isinstance(data['buildings'], list):
            for i, building in enumerate(data['buildings']):
                building_errors = self._validate_building_data(building)
                for error in building_errors:
                    errors.append(f"Budynek {i}: {error}")
        
        if 'resources' in data and isinstance(data['resources'], dict):
            resource_errors = self._validate_resources_data(data['resources'])
            errors.extend(resource_errors)
        
        return len(errors) == 0, errors
    
    def _validate_building_data(self, building: Dict) -> List[str]:
        """Waliduje dane pojedynczego budynku"""
        errors = []
        
        required_fields = {
            'id': 'building_id',
            'type': 'building_type',
            'x': 'population_count',  # Używamy tego wzorca dla liczb całkowitych
            'y': 'population_count'
        }
        
        for field, pattern_name in required_fields.items():
            if field not in building:
                errors.append(f"Brakuje pola: {field}")
            else:
                is_valid, error = self.validate_field(pattern_name, str(building[field]))
                if not is_valid:
                    errors.append(f"Błąd w polu {field}: {error}")
        
        return errors
    
    def _validate_resources_data(self, resources: Dict) -> List[str]:
        """Waliduje dane zasobów"""
        errors = []
        
        valid_resources = ['money', 'energy', 'water', 'materials', 'food', 'luxury_goods']
        
        for resource_name, amount in resources.items():
            # Sprawdź czy nazwa zasobu jest poprawna
            is_valid, error = self.validate_field('resource_type', resource_name)
            if not is_valid:
                errors.append(f"Niepoprawna nazwa zasobu: {resource_name}")
            
            # Sprawdź czy ilość jest poprawna
            is_valid, parsed_amount = self.validate_money_amount(str(amount))
            if not is_valid:
                errors.append(f"Niepoprawna ilość zasobu {resource_name}: {amount}")
        
        return errors
    
    def validate_csv_data(self, csv_content: str) -> Tuple[bool, List[str]]:
        """Waliduje dane CSV"""
        errors = []
        lines = csv_content.strip().split('\n')
        
        for i, line in enumerate(lines):
            if not self.patterns['csv_line'].match(line):
                errors.append(f"Niepoprawny format CSV w linii {i+1}: {line[:50]}...")
        
        return len(errors) == 0, errors
    
    def validate_xml_structure(self, xml_content: str) -> Tuple[bool, List[str]]:
        """Waliduje strukturę XML"""
        errors = []
        
        try:
            root = ET.fromstring(xml_content)
            self._validate_xml_element(root, errors)
        except ET.ParseError as e:
            errors.append(f"Błąd parsowania XML: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_xml_element(self, element: ET.Element, errors: List[str]):
        """Rekurencyjnie waliduje elementy XML"""
        # Sprawdź nazwę tagu
        if not self.patterns['xml_tag'].match(element.tag):
            errors.append(f"Niepoprawna nazwa tagu XML: {element.tag}")
        
        # Sprawdź atrybuty
        for attr_name, attr_value in element.attrib.items():
            if not self.patterns['xml_tag'].match(attr_name):
                errors.append(f"Niepoprawna nazwa atrybutu XML: {attr_name}")
        
        # Rekurencyjnie sprawdź dzieci
        for child in element:
            self._validate_xml_element(child, errors)
    
    def extract_data_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Ekstraktuje różne typy danych z tekstu używając regex
        
        Args:
            text: Tekst do analizy
            
        Returns:
            Dict zawierający znalezione dane pogrupowane według typu
        """
        extracted = {
            'emails': [],
            'urls': [],
            'dates': [],
            'coordinates': [],
            'money_amounts': [],
            'percentages': [],
            'file_paths': []
        }
        
        # Znajdź wszystkie emaile
        email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
        extracted['emails'] = email_pattern.findall(text)
        
        # Znajdź wszystkie URL-e
        url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
        extracted['urls'] = url_pattern.findall(text)
        
        # Znajdź daty
        date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
        extracted['dates'] = date_pattern.findall(text)
        
        # Znajdź współrzędne
        coord_pattern = re.compile(r'\b\d{1,3},\d{1,3}\b')
        extracted['coordinates'] = coord_pattern.findall(text)
        
        # Znajdź kwoty pieniędzy
        money_pattern = re.compile(r'\b\d{1,12}(?:\.\d{2})?\s*(?:zł|PLN|$|€|USD|EUR)\b')
        extracted['money_amounts'] = money_pattern.findall(text)
        
        # Znajdź procenty
        percent_pattern = re.compile(r'\b\d{1,3}(?:\.\d{1,2})?%\b')
        extracted['percentages'] = percent_pattern.findall(text)
        
        # Znajdź ścieżki plików
        path_pattern = re.compile(r'\b[A-Za-z]:[\\\/](?:[^<>:"|?*\r\n\s]+[\\\/])*[^<>:"|?*\r\n\s]+\b')
        extracted['file_paths'] = path_pattern.findall(text)
        
        return extracted
    
    def sanitize_input(self, input_string: str, field_type: str) -> str:
        """
        Oczyszcza dane wejściowe usuwając niebezpieczne znaki
        
        Args:
            input_string: Tekst do oczyszczenia
            field_type: Typ pola (określa jakie znaki są dozwolone)
            
        Returns:
            Oczyszczony tekst
        """
        if field_type == 'city_name':
            # Usuń wszystko oprócz liter, cyfr, spacji i myślników
            return re.sub(r'[^A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\s\-]', '', input_string)
        
        elif field_type == 'building_id':
            # Usuń wszystko oprócz małych liter, cyfr i podkreśleń
            return re.sub(r'[^a-z0-9_]', '', input_string.lower())
        
        elif field_type == 'numeric':
            # Usuń wszystko oprócz cyfr, kropki i minusa
            return re.sub(r'[^0-9.\-]', '', input_string)
        
        elif field_type == 'filename':
            # Usuń niebezpieczne znaki z nazw plików
            return re.sub(r'[<>:"|?*\\\/]', '_', input_string)
        
        else:
            # Domyślnie usuń tylko najbardziej niebezpieczne znaki
            return re.sub(r'[<>"|]', '', input_string)
    
    def validate_and_parse_config_file(self, file_path: str) -> Tuple[bool, Dict, List[str]]:
        """
        Waliduje i parsuje plik konfiguracyjny
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            Tuple[bool, Dict, List[str]]: (czy_poprawny, dane, błędy)
        """
        errors = []
        data = {}
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                errors.append(f"Plik nie istnieje: {file_path}")
                return False, {}, errors
            
            content = path.read_text(encoding='utf-8')
            
            if path.suffix.lower() == '.json':
                data = json.loads(content)
                is_valid, validation_errors = self.validate_game_data_structure(data)
                errors.extend(validation_errors)
            
            elif path.suffix.lower() == '.xml':
                is_valid, validation_errors = self.validate_xml_structure(content)
                errors.extend(validation_errors)
                if is_valid:
                    # Konwertuj XML do dict (uproszczona implementacja)
                    root = ET.fromstring(content)
                    data = self._xml_to_dict(root)
            
            else:
                errors.append(f"Nieobsługiwany format pliku: {path.suffix}")
                return False, {}, errors
        
        except json.JSONDecodeError as e:
            errors.append(f"Błąd parsowania JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Błąd odczytu pliku: {str(e)}")
        
        return len(errors) == 0, data, errors
    
    def _xml_to_dict(self, element: ET.Element) -> Dict:
        """Konwertuje element XML do słownika"""
        result = {}
        
        # Dodaj atrybuty
        if element.attrib:
            result.update(element.attrib)
        
        # Dodaj tekst jeśli istnieje
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Dodaj dzieci
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def generate_validation_report(self, data: Dict) -> str:
        """
        Generuje szczegółowy raport walidacji
        
        Args:
            data: Dane do walidacji
            
        Returns:
            Sformatowany raport tekstowy
        """
        is_valid, errors = self.validate_game_data_structure(data)
        
        report = []
        report.append("=== RAPORT WALIDACJI DANYCH ===")
        report.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Status: {'POPRAWNE' if is_valid else 'BŁĘDY ZNALEZIONE'}")
        report.append("")
        
        if errors:
            report.append("ZNALEZIONE BŁĘDY:")
            for i, error in enumerate(errors, 1):
                report.append(f"{i:2d}. {error}")
        else:
            report.append("✓ Wszystkie dane są poprawne")
        
        report.append("")
        report.append("STATYSTYKI:")
        report.append(f"- Sprawdzonych pól: {len(data)}")
        report.append(f"- Znalezionych błędów: {len(errors)}")
        
        return "\n".join(report)


# Globalna instancja walidatora
_validator_instance = None

def get_data_validator() -> DataValidator:
    """Zwraca globalną instancję walidatora (singleton)"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DataValidator()
    return _validator_instance 