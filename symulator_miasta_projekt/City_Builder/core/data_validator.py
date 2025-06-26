"""
Moduł walidacji danych z wykorzystaniem wyrażeń regularnych.
Implementuje zaawansowane walidacje dla wszystkich typów danych w grze.

Ten moduł zawiera kompleksowy system walidacji danych używający wyrażeń regularnych (regex).
Sprawdza poprawność wszystkich typów danych w grze: nazwy miast, współrzędne, kwoty, daty, etc.
"""

# === IMPORTY POTRZEBNE DLA WALIDACJI DANYCH ===
import re                                                  # Do wyrażeń regularnych (regex)
import json                                                # Do parsowania i walidacji JSON
import xml.etree.ElementTree as ET                        # Do parsowania i walidacji XML
from typing import Dict, List, Optional, Tuple, Any, Union  # Dla typowania - poprawia czytelność kodu
from pathlib import Path                                   # Do obsługi ścieżek plików
import logging                                             # Do logowania operacji walidacji
from datetime import datetime                              # Do walidacji dat i czasu

class DataValidator:
    """
    Klasa do walidacji danych z wykorzystaniem wyrażeń regularnych.
    
    Zawiera predefiniowane wzorce regex dla wszystkich typów danych w grze.
    Oferuje metody do walidacji pojedynczych pól oraz całych struktur danych.
    Obsługuje różne formaty: JSON, XML, CSV.
    """
    
    def __init__(self):
        """
        Inicjalizuje walidator z predefiniowanymi wzorcami regex.
        
        Tworzy kompletną bibliotekę wyrażeń regularnych dla wszystkich typów danych
        używanych w grze. Każdy wzorzec ma swoją nazwę i opis.
        """
        
        # === WZORCE DLA PODSTAWOWYCH TYPÓW DANYCH ===
        # Słownik zawierający wszystkie wzorce regex z opisami
        self.patterns = {
            # === IDENTYFIKATORY I NAZWY ===
            'city_name': re.compile(r'^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-]{2,50}$'),  # Nazwa miasta: 2-50 znaków, litery + polskie znaki
            'building_id': re.compile(r'^[a-z_][a-z0-9_]{2,30}$'),              # ID budynku: małe litery, cyfry, podkreślenia
            'player_name': re.compile(r'^[A-Za-z0-9ĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-\.]{2,30}$'),  # Nazwa gracza: litery, cyfry, polskie znaki
            'save_filename': re.compile(r'^[A-Za-z0-9_\-]{1,50}\.json$'),       # Nazwa pliku zapisu: litery, cyfry, rozszerzenie .json
            
            # === WSPÓŁRZĘDNE I POZYCJE ===
            'coordinates': re.compile(r'^(\d{1,3}),(\d{1,3})$'),                # Współrzędne: x,y (1-3 cyfry każda)
            'map_size': re.compile(r'^(\d{2,3})x(\d{2,3})$'),                   # Rozmiar mapy: szerokość x wysokość (2-3 cyfry)
            'position_range': re.compile(r'^(\d+)-(\d+)$'),                      # Zakres pozycji: liczba-liczba
            
            # === WARTOŚCI NUMERYCZNE ===
            'money_amount': re.compile(r'^-?\d{1,12}(\.\d{2})?$'),              # Kwota pieniędzy: opcjonalny minus, do 12 cyfr, 2 miejsca po przecinku
            'percentage': re.compile(r'^(100|[0-9]{1,2})(\.\d{1,2})?%?$'),      # Procent: 0-100, opcjonalne miejsca po przecinku
            'population_count': re.compile(r'^[0-9]{1,8}$'),                    # Liczba mieszkańców: 1-8 cyfr
            'resource_amount': re.compile(r'^[0-9]{1,10}(\.\d{1,3})?$'),        # Ilość zasobu: do 10 cyfr, 3 miejsca po przecinku
            
            # === DATY I CZAS ===
            'date_iso': re.compile(r'^\d{4}-\d{2}-\d{2}$'),                     # Data ISO: YYYY-MM-DD
            'datetime_iso': re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'),  # Data i czas ISO: YYYY-MM-DDTHH:MM:SS
            'game_time': re.compile(r'^(\d{1,4}):(\d{1,2}):(\d{1,2})$'),        # Czas gry: godziny:minuty:sekundy
            
            # === KONFIGURACJA I USTAWIENIA ===
            'difficulty_level': re.compile(r'^(Easy|Normal|Hard|Extreme)$'),     # Poziom trudności: tylko te 4 opcje
            'language_code': re.compile(r'^(pl|en|de|fr|es)$'),                  # Kod języka: tylko obsługiwane języki
            'color_hex': re.compile(r'^#[0-9A-Fa-f]{6}$'),                      # Kolor hex: #RRGGBB
            'version_number': re.compile(r'^\d+\.\d+\.\d+$'),                    # Numer wersji: major.minor.patch
            
            # === ŚCIEŻKI PLIKÓW ===
            'file_path': re.compile(r'^[A-Za-z]:[\\\/](?:[^<>:"|?*\r\n]+[\\\/])*[^<>:"|?*\r\n]*$'),  # Ścieżka absolutna Windows
            'relative_path': re.compile(r'^(?:\.\.?[\\\/])*[^<>:"|?*\r\n\\\/]+(?:[\\\/][^<>:"|?*\r\n\\\/]+)*$'),  # Ścieżka względna
            
            # === EMAIL I URL (DLA PRZYSZŁYCH FUNKCJI MULTIPLAYER) ===
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),  # Adres email: user@domain.tld
            'url': re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'),  # URL HTTP/HTTPS
            
            # === SPECJALNE WZORCE DLA GRY ===
            'building_type': re.compile(r'^(residential|commercial|industrial|public|infrastructure)$'),  # Typ budynku
            'resource_type': re.compile(r'^(money|energy|water|materials|food|luxury_goods)$'),          # Typ zasobu
            'event_type': re.compile(r'^(disaster|economic|social|political|technological)$'),          # Typ wydarzenia
            
            # === WZORCE DLA IMPORTU/EKSPORTU DANYCH ===
            'csv_line': re.compile(r'^(?:"[^"]*"|[^,]*)(?:,(?:"[^"]*"|[^,]*))*$'),  # Linia CSV z obsługą cudzysłowów
            'json_key': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$'),                   # Klucz JSON: litera/podkreślenie + litery/cyfry
            'xml_tag': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-]*$'),                  # Tag XML: litera/podkreślenie + litery/cyfry/myślniki
        }
        
        # === WZORCE ZŁOŻONE DLA WALIDACJI STRUKTUR DANYCH ===
        # Bardziej skomplikowane wzorce dla całych struktur JSON
        self.complex_patterns = {
            'building_config': re.compile(
                r'^{.*"id":\s*"[a-z_][a-z0-9_]*".*"cost":\s*\d+.*"type":\s*"(residential|commercial|industrial|public|infrastructure)".*}$',
                re.DOTALL  # Kropka pasuje do nowej linii
            ),
            'save_game_header': re.compile(
                r'^{.*"version":\s*"\d+\.\d+\.\d+".*"timestamp":\s*"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}".*"city_name":\s*"[^"]{2,50}".*}$',
                re.DOTALL  # Kropka pasuje do nowej linii
            ),
        }
        
        # Logger do rejestrowania operacji walidacji
        self.logger = logging.getLogger(__name__)
    
    def validate_field(self, field_name: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Waliduje pojedyncze pole używając odpowiedniego wzorca regex.
        
        Args:
            field_name: Nazwa pola do walidacji (klucz w słowniku patterns)
            value: Wartość do sprawdzenia (string)
            
        Returns:
            Tuple[bool, Optional[str]]: (czy_poprawne, komunikat_błędu)
        """
        # Sprawdź czy istnieje wzorzec dla tego pola
        if field_name not in self.patterns:
            return False, f"Nieznany typ pola: {field_name}"
        
        # Pobierz odpowiedni wzorzec regex
        pattern = self.patterns[field_name]
        
        # Upewnij się, że wartość jest stringiem
        if not isinstance(value, str):
            value = str(value)
        
        # Sprawdź czy wartość pasuje do wzorca
        if pattern.match(value):
            return True, None  # Wartość poprawna
        else:
            return False, f"Niepoprawny format dla {field_name}: {value}"  # Wartość niepoprawna
    
    def validate_coordinates(self, coord_string: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Waliduje i parsuje współrzędne.
        
        Args:
            coord_string: String z współrzędnymi (np. "123,456")
            
        Returns:
            Tuple[bool, Optional[Tuple[int, int]]]: (czy_poprawne, (x, y) lub None)
        """
        # Sprawdź czy string pasuje do wzorca współrzędnych
        match = self.patterns['coordinates'].match(coord_string)
        if match:
            # Wyciągnij liczby z grup regex
            x, y = int(match.group(1)), int(match.group(2))
            # Sprawdź zakres (0-999)
            if 0 <= x <= 999 and 0 <= y <= 999:
                return True, (x, y)  # Współrzędne poprawne
        return False, None  # Współrzędne niepoprawne
    
    def validate_map_size(self, size_string: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Waliduje i parsuje rozmiar mapy.
        
        Args:
            size_string: String z rozmiarem mapy (np. "60x60")
            
        Returns:
            Tuple[bool, Optional[Tuple[int, int]]]: (czy_poprawne, (szerokość, wysokość) lub None)
        """
        # Sprawdź czy string pasuje do wzorca rozmiaru mapy
        match = self.patterns['map_size'].match(size_string)
        if match:
            # Wyciągnij liczby z grup regex
            width, height = int(match.group(1)), int(match.group(2))
            # Sprawdź zakres (20-200)
            if 20 <= width <= 200 and 20 <= height <= 200:
                return True, (width, height)  # Rozmiar poprawny
        return False, None  # Rozmiar niepoprawny
    
    def validate_money_amount(self, amount_string: str) -> Tuple[bool, Optional[float]]:
        """
        Waliduje i parsuje kwotę pieniędzy.
        
        Args:
            amount_string: String z kwotą (np. "1234.56" lub "-1000")
            
        Returns:
            Tuple[bool, Optional[float]]: (czy_poprawne, kwota lub None)
        """
        # Sprawdź czy string pasuje do wzorca kwoty
        match = self.patterns['money_amount'].match(amount_string)
        if match:
            try:
                # Konwertuj na float
                amount = float(amount_string)
                # Sprawdź zakres (-999999999999 do +999999999999)
                if -999999999999 <= amount <= 999999999999:
                    return True, amount  # Kwota poprawna
            except ValueError:
                pass  # Konwersja się nie udała
        return False, None  # Kwota niepoprawna
    
    def validate_percentage(self, percent_string: str) -> Tuple[bool, Optional[float]]:
        """
        Waliduje i parsuje procenty.
        
        Args:
            percent_string: String z procentem (np. "50%" lub "75.5")
            
        Returns:
            Tuple[bool, Optional[float]]: (czy_poprawne, procent lub None)
        """
        # Usuń znak % jeśli istnieje
        clean_string = percent_string.rstrip('%')
        # Sprawdź czy string pasuje do wzorca procentu
        match = self.patterns['percentage'].match(percent_string)
        if match:
            try:
                # Konwertuj na float
                percent = float(clean_string)
                # Sprawdź zakres (0-100)
                if 0 <= percent <= 100:
                    return True, percent  # Procent poprawny
            except ValueError:
                pass  # Konwersja się nie udała
        return False, None  # Procent niepoprawny
    
    def validate_game_data_structure(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Waliduje całą strukturę danych gry.
        
        Args:
            data: Słownik z danymi gry do walidacji
            
        Returns:
            Tuple[bool, List[str]]: (czy_poprawne, lista_błędów)
        """
        errors = []  # Lista błędów znalezionych podczas walidacji
        
        # === SPRAWDŹ WYMAGANE POLA ===
        # Mapowanie nazw pól na wzorce walidacji
        required_fields = {
            'city_name': 'city_name',      # Nazwa miasta
            'version': 'version_number',   # Numer wersji
            'timestamp': 'datetime_iso',   # Data i czas
            'difficulty': 'difficulty_level'  # Poziom trudności
        }
        
        # Sprawdź każde wymagane pole
        for field, pattern_name in required_fields.items():
            if field not in data:
                errors.append(f"Brakuje wymaganego pola: {field}")
            else:
                # Waliduj wartość pola
                is_valid, error = self.validate_field(pattern_name, str(data[field]))
                if not is_valid:
                    errors.append(f"Błąd w polu {field}: {error}")
        
        # === SPRAWDŹ STRUKTURY ZAGNIEŻDŻONE ===
        # Waliduj listę budynków
        if 'buildings' in data and isinstance(data['buildings'], list):
            for i, building in enumerate(data['buildings']):
                building_errors = self._validate_building_data(building)
                for error in building_errors:
                    errors.append(f"Budynek {i}: {error}")
        
        # Waliduj słownik zasobów
        if 'resources' in data and isinstance(data['resources'], dict):
            resource_errors = self._validate_resources_data(data['resources'])
            errors.extend(resource_errors)
        
        # Zwróć wynik walidacji (True jeśli brak błędów)
        return len(errors) == 0, errors
    
    def _validate_building_data(self, building: Dict) -> List[str]:
        """
        Waliduje dane pojedynczego budynku.
        
        Args:
            building: Słownik z danymi budynku
            
        Returns:
            List[str]: Lista błędów znalezionych w danych budynku
        """
        errors = []  # Lista błędów dla tego budynku
        
        # Wymagane pola dla budynku
        required_fields = {
            'id': 'building_id',           # ID budynku
            'type': 'building_type',       # Typ budynku
            'x': 'population_count',       # Współrzędna X (używamy wzorca dla liczb całkowitych)
            'y': 'population_count'        # Współrzędna Y (używamy wzorca dla liczb całkowitych)
        }
        
        # Sprawdź każde wymagane pole
        for field, pattern_name in required_fields.items():
            if field not in building:
                errors.append(f"Brakuje pola: {field}")
            else:
                # Waliduj wartość pola
                is_valid, error = self.validate_field(pattern_name, str(building[field]))
                if not is_valid:
                    errors.append(f"Błąd w polu {field}: {error}")
        
        return errors
    
    def _validate_resources_data(self, resources: Dict) -> List[str]:
        """
        Waliduje dane zasobów.
        
        Args:
            resources: Słownik z danymi zasobów
            
        Returns:
            List[str]: Lista błędów znalezionych w danych zasobów
        """
        errors = []  # Lista błędów dla zasobów
        
        # Lista poprawnych nazw zasobów
        valid_resources = ['money', 'energy', 'water', 'materials', 'food', 'luxury_goods']
        
        # Sprawdź każdy zasób
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
        """
        Waliduje dane CSV.
        
        Args:
            csv_content: Zawartość pliku CSV jako string
            
        Returns:
            Tuple[bool, List[str]]: (czy_poprawne, lista_błędów)
        """
        errors = []  # Lista błędów w danych CSV
        lines = csv_content.strip().split('\n')  # Podziel na linie
        
        # Sprawdź każdą linię
        for i, line in enumerate(lines):
            if not self.patterns['csv_line'].match(line):
                errors.append(f"Niepoprawny format CSV w linii {i+1}: {line[:50]}...")
        
        return len(errors) == 0, errors
    
    def validate_xml_structure(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Waliduje strukturę XML.
        
        Args:
            xml_content: Zawartość pliku XML jako string
            
        Returns:
            Tuple[bool, List[str]]: (czy_poprawne, lista_błędów)
        """
        errors = []  # Lista błędów w strukturze XML
        
        try:
            # Parsuj XML do drzewa elementów
            root = ET.fromstring(xml_content)
            # Rekurencyjnie waliduj wszystkie elementy
            self._validate_xml_element(root, errors)
        except ET.ParseError as e:
            # Błąd parsowania XML (niepoprawna składnia)
            errors.append(f"Błąd parsowania XML: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_xml_element(self, element: ET.Element, errors: List[str]):
        """
        Rekurencyjnie waliduje elementy XML.
        
        Args:
            element: Element XML do walidacji
            errors: Lista błędów (modyfikowana w miejscu)
        """
        # Sprawdź nazwę tagu
        if not self.patterns['xml_tag'].match(element.tag):
            errors.append(f"Niepoprawna nazwa tagu XML: {element.tag}")
        
        # Sprawdź atrybuty elementu
        for attr_name, attr_value in element.attrib.items():
            if not self.patterns['xml_tag'].match(attr_name):
                errors.append(f"Niepoprawna nazwa atrybutu XML: {attr_name}")
        
        # Rekurencyjnie sprawdź elementy potomne
        for child in element:
            self._validate_xml_element(child, errors)
    
    def extract_data_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Ekstraktuje różne typy danych z tekstu używając regex.
        
        Args:
            text: Tekst do analizy
            
        Returns:
            Dict zawierający znalezione dane pogrupowane według typu
        """
        # Inicjalizuj słownik wyników
        extracted = {
            'emails': [],           # Znalezione adresy email
            'urls': [],             # Znalezione URL-e
            'dates': [],            # Znalezione daty
            'coordinates': [],      # Znalezione współrzędne
            'money_amounts': [],    # Znalezione kwoty pieniędzy
            'percentages': [],      # Znalezione procenty
            'file_paths': []        # Znalezione ścieżki plików
        }
        
        # === ZNAJDŹ WSZYSTKIE EMAILE ===
        # Wzorzec dla adresów email
        email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
        extracted['emails'] = email_pattern.findall(text)
        
        # === ZNAJDŹ WSZYSTKIE URL-E ===
        # Wzorzec dla URL-i HTTP/HTTPS
        url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
        extracted['urls'] = url_pattern.findall(text)
        
        # === ZNAJDŹ DATY ===
        # Wzorzec dla dat w formacie YYYY-MM-DD
        date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
        extracted['dates'] = date_pattern.findall(text)
        
        # === ZNAJDŹ WSPÓŁRZĘDNE ===
        # Wzorzec dla współrzędnych x,y
        coord_pattern = re.compile(r'\b\d{1,3},\d{1,3}\b')
        extracted['coordinates'] = coord_pattern.findall(text)
        
        # === ZNAJDŹ KWOTY PIENIĘDZY ===
        # Wzorzec dla kwot z walutami
        money_pattern = re.compile(r'\b\d{1,12}(?:\.\d{2})?\s*(?:zł|PLN|$|€|USD|EUR)\b')
        extracted['money_amounts'] = money_pattern.findall(text)
        
        # === ZNAJDŹ PROCENTY ===
        # Wzorzec dla procentów
        percent_pattern = re.compile(r'\b\d{1,3}(?:\.\d{1,2})?%\b')
        extracted['percentages'] = percent_pattern.findall(text)
        
        # === ZNAJDŹ ŚCIEŻKI PLIKÓW ===
        # Wzorzec dla ścieżek Windows
        path_pattern = re.compile(r'\b[A-Za-z]:[\\\/](?:[^<>:"|?*\r\n\s]+[\\\/])*[^<>:"|?*\r\n\s]+\b')
        extracted['file_paths'] = path_pattern.findall(text)
        
        return extracted
    
    def sanitize_input(self, input_string: str, field_type: str) -> str:
        """
        Oczyszcza dane wejściowe usuwając niebezpieczne znaki.
        
        Args:
            input_string: Tekst do oczyszczenia
            field_type: Typ pola (określa jakie znaki są dozwolone)
            
        Returns:
            Oczyszczony tekst
        """
        if field_type == 'city_name':
            # Usuń wszystko oprócz liter, cyfr, spacji i myślników (dla nazw miast)
            return re.sub(r'[^A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\s\-]', '', input_string)
        
        elif field_type == 'building_id':
            # Usuń wszystko oprócz małych liter, cyfr i podkreśleń (dla ID budynków)
            return re.sub(r'[^a-z0-9_]', '', input_string.lower())
        
        elif field_type == 'numeric':
            # Usuń wszystko oprócz cyfr, kropki i minusa (dla liczb)
            return re.sub(r'[^0-9.\-]', '', input_string)
        
        elif field_type == 'filename':
            # Usuń niebezpieczne znaki z nazw plików
            return re.sub(r'[<>:"|?*\\\/]', '_', input_string)
        
        else:
            # Domyślnie usuń tylko najbardziej niebezpieczne znaki
            return re.sub(r'[<>"|]', '', input_string)
    
    def validate_and_parse_config_file(self, file_path: str) -> Tuple[bool, Dict, List[str]]:
        """
        Waliduje i parsuje plik konfiguracyjny.
        
        Args:
            file_path: Ścieżka do pliku konfiguracyjnego
            
        Returns:
            Tuple[bool, Dict, List[str]]: (czy_poprawny, dane, błędy)
        """
        errors = []  # Lista błędów
        data = {}    # Parsowane dane
        
        try:
            # Konwertuj ścieżkę na obiekt Path
            path = Path(file_path)
            
            # Sprawdź czy plik istnieje
            if not path.exists():
                errors.append(f"Plik nie istnieje: {file_path}")
                return False, {}, errors
            
            # Wczytaj zawartość pliku
            content = path.read_text(encoding='utf-8')
            
            # === WALIDUJ I PARSÓJ WG FORMATU ===
            if path.suffix.lower() == '.json':
                # Parsuj JSON
                data = json.loads(content)
                # Waliduj strukturę danych
                is_valid, validation_errors = self.validate_game_data_structure(data)
                errors.extend(validation_errors)
            
            elif path.suffix.lower() == '.xml':
                # Waliduj strukturę XML
                is_valid, validation_errors = self.validate_xml_structure(content)
                errors.extend(validation_errors)
                if is_valid:
                    # Konwertuj XML do dict (uproszczona implementacja)
                    root = ET.fromstring(content)
                    data = self._xml_to_dict(root)
            
            else:
                # Nieobsługiwany format
                errors.append(f"Nieobsługiwany format pliku: {path.suffix}")
                return False, {}, errors
        
        except json.JSONDecodeError as e:
            # Błąd parsowania JSON
            errors.append(f"Błąd parsowania JSON: {str(e)}")
        except Exception as e:
            # Inne błędy odczytu pliku
            errors.append(f"Błąd odczytu pliku: {str(e)}")
        
        return len(errors) == 0, data, errors
    
    def _xml_to_dict(self, element: ET.Element) -> Dict:
        """
        Konwertuje element XML do słownika.
        
        Args:
            element: Element XML do konwersji
            
        Returns:
            Dict: Słownik reprezentujący element XML
        """
        result = {}  # Wynikowy słownik
        
        # Dodaj atrybuty elementu
        if element.attrib:
            result.update(element.attrib)
        
        # Dodaj tekst elementu jeśli istnieje
        if element.text and element.text.strip():
            if len(element) == 0:
                # Element bez dzieci - zwróć tylko tekst
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Dodaj elementy potomne
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                # Jeśli tag już istnieje, utwórz listę
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                # Nowy tag
                result[child.tag] = child_data
        
        return result
    
    def generate_validation_report(self, data: Dict) -> str:
        """
        Generuje szczegółowy raport walidacji.
        
        Args:
            data: Dane do walidacji
            
        Returns:
            Sformatowany raport tekstowy
        """
        # Waliduj dane
        is_valid, errors = self.validate_game_data_structure(data)
        
        # Buduj raport
        report = []
        report.append("=== RAPORT WALIDACJI DANYCH ===")
        report.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Status: {'POPRAWNE' if is_valid else 'BŁĘDY ZNALEZIONE'}")
        report.append("")
        
        if errors:
            # Lista błędów
            report.append("ZNALEZIONE BŁĘDY:")
            for i, error in enumerate(errors, 1):
                report.append(f"{i:2d}. {error}")
        else:
            # Brak błędów
            report.append("✓ Wszystkie dane są poprawne")
        
        report.append("")
        report.append("STATYSTYKI:")
        report.append(f"- Sprawdzonych pól: {len(data)}")
        report.append(f"- Znalezionych błędów: {len(errors)}")
        
        return "\n".join(report)


# === GLOBALNA INSTANCJA WALIDATORA ===
# Zmienna globalna przechowująca jedyną instancję DataValidator
_validator_instance = None

def get_data_validator() -> DataValidator:
    """
    Zwraca globalną instancję walidatora (singleton).
    
    Singleton zapewnia, że w całej aplikacji istnieje tylko jedna instancja
    walidatora danych, co pozwala na spójną walidację i oszczędność pamięci.
    
    Returns:
        DataValidator: Jedyna instancja walidatora danych
    """
    global _validator_instance
    # Jeśli instancja nie istnieje, utwórz ją
    if _validator_instance is None:
        _validator_instance = DataValidator()
    # Zwróć istniejącą instancję
    return _validator_instance 