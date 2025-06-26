"""
Zaawansowane przetwarzanie plików i katalogów
Obsługuje różne formaty danych: CSV, JSON, XML
Implementuje system logowania zdarzeń
"""

import os  # Moduł do operacji na systemie plików
import csv  # Moduł do obsługi plików CSV
import json  # Moduł do obsługi plików JSON
import xml.etree.ElementTree as ET  # Moduł do parsowania XML (drzewo elementów)
import xml.dom.minidom as minidom  # Moduł do ładnego formatowania XML
from pathlib import Path  # Klasa do obsługi ścieżek plików
from typing import Dict, List, Optional, Any, Union, Iterator, Tuple  # Typowanie
import logging  # Moduł do logowania
from datetime import datetime  # Klasa do obsługi daty i czasu
import shutil  # Moduł do operacji kopiowania plików
import zipfile  # Moduł do obsługi archiwów ZIP
import tempfile  # Moduł do obsługi plików tymczasowych
from dataclasses import dataclass, asdict  # Dekorator do prostych klas danych
import pandas as pd  # Biblioteka do zaawansowanej analizy danych (CSV)

from .data_validator import get_data_validator  # Import walidatora danych
from .logger import get_game_logger  # Import loggera gry

@dataclass
class FileMetadata:
    """
    Metadane pliku (ścieżka, rozmiar, daty, format, kodowanie, suma kontrolna).
    """
    path: str  # Pełna ścieżka do pliku
    size: int  # Rozmiar pliku w bajtach
    created: datetime  # Data utworzenia pliku
    modified: datetime  # Data ostatniej modyfikacji
    format: str  # Rozszerzenie pliku (np. .json)
    encoding: str = 'utf-8'  # Kodowanie pliku (domyślnie UTF-8)
    checksum: Optional[str] = None  # Suma kontrolna pliku (opcjonalnie)

class FileProcessor:
    """
    Klasa do zaawansowanego przetwarzania plików.
    Obsługuje odczyt, zapis, walidację, backup, kompresję i czyszczenie plików.
    """
    def __init__(self):
        """
        Inicjalizuje procesor plików, logger i walidator.
        """
        self.validator = get_data_validator()  # Instancja walidatora danych
        self.logger = get_game_logger().get_logger('file_processor')  # Logger dla operacji plikowych
        self.supported_formats = {'.json', '.csv', '.xml', '.txt', '.log'}  # Obsługiwane formaty plików
    
    def read_json_file(self, file_path: str) -> Tuple[bool, Dict, List[str]]:
        """
        Czyta i waliduje plik JSON.
        Zwraca: (czy_sukces, dane, lista_błędów)
        """
        errors = []  # Lista błędów
        data = {}  # Słownik na dane
        try:
            path = Path(file_path)  # Utwórz obiekt ścieżki
            if not path.exists():  # Sprawdź czy plik istnieje
                errors.append(f"Plik nie istnieje: {file_path}")
                return False, {}, errors
            self.logger.info(f"Czytanie pliku JSON: {file_path}")
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)  # Wczytaj dane JSON
            # Walidacja struktury danych
            is_valid, validation_errors = self.validator.validate_game_data_structure(data)
            if not is_valid:
                errors.extend(validation_errors)
            self.logger.info(f"Pomyślnie wczytano plik JSON: {len(data)} elementów")
        except json.JSONDecodeError as e:
            error_msg = f"Błąd parsowania JSON: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"Błąd odczytu pliku: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        return len(errors) == 0, data, errors
    
    def write_json_file(self, file_path: str, data: Dict, pretty: bool = True) -> Tuple[bool, List[str]]:
        """
        Zapisuje dane do pliku JSON (opcjonalnie sformatowane).
        Zwraca: (czy_sukces, lista_błędów)
        """
        errors = []
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)  # Utwórz katalog jeśli nie istnieje
            self.logger.info(f"Zapisywanie pliku JSON: {file_path}")
            # Walidacja przed zapisem
            is_valid, validation_errors = self.validator.validate_game_data_structure(data)
            if not is_valid:
                self.logger.warning(f"Dane zawierają błędy walidacji: {len(validation_errors)}")
            with open(path, 'w', encoding='utf-8') as file:
                if pretty:
                    json.dump(data, file, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, file, ensure_ascii=False)
            self.logger.info(f"Pomyślnie zapisano plik JSON: {path.stat().st_size} bajtów")
        except Exception as e:
            error_msg = f"Błąd zapisu pliku JSON: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        return len(errors) == 0, errors
    
    def read_csv_file(self, file_path: str, delimiter: str = ',') -> Tuple[bool, List[Dict], List[str]]:
        """
        Czyta plik CSV i zwraca listę słowników (jeden słownik na wiersz).
        Zwraca: (czy_sukces, lista_słowników, lista_błędów)
        """
        errors = []
        data = []
        try:
            path = Path(file_path)
            if not path.exists():
                errors.append(f"Plik nie istnieje: {file_path}")
                return False, [], errors
            self.logger.info(f"Czytanie pliku CSV: {file_path}")
            with open(path, 'r', encoding='utf-8', newline='') as file:
                sample = file.read(1024)  # Próbka do wykrycia dialektu
                file.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                    reader = csv.DictReader(file, dialect=dialect)
                except csv.Error:
                    reader = csv.DictReader(file, delimiter=delimiter)
                for row_num, row in enumerate(reader, 1):
                    cleaned_row = {}
                    for key, value in row.items():
                        if key:  # Pomijaj puste klucze
                            cleaned_key = self.validator.sanitize_input(key, 'json_key')
                            cleaned_value = self.validator.sanitize_input(str(value), 'general')
                            cleaned_row[cleaned_key] = cleaned_value
                    if cleaned_row:
                        data.append(cleaned_row)
            self.logger.info(f"Pomyślnie wczytano plik CSV: {len(data)} wierszy")
        except Exception as e:
            error_msg = f"Błąd odczytu pliku CSV: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        return len(errors) == 0, data, errors
    
    def write_csv_file(self, file_path: str, data: List[Dict], fieldnames: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """
        Zapisuje dane do pliku CSV (lista słowników jako wiersze).
        Zwraca: (czy_sukces, lista_błędów)
        """
        errors = []
        try:
            if not data:
                errors.append("Brak danych do zapisania")
                return False, errors
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)  # Utwórz katalog jeśli nie istnieje
            self.logger.info(f"Zapisywanie pliku CSV: {file_path}")
            if fieldnames is None:
                fieldnames = list(data[0].keys())  # Automatyczne wykrywanie nazw kolumn
            with open(path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            self.logger.info(f"Pomyślnie zapisano plik CSV: {len(data)} wierszy")
        except Exception as e:
            error_msg = f"Błąd zapisu pliku CSV: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        return len(errors) == 0, errors
    
    def read_xml_file(self, file_path: str) -> Tuple[bool, Dict, List[str]]:
        """
        Czyta i parsuje plik XML
        
        Args:
            file_path: Ścieżka do pliku XML
            
        Returns:
            Tuple[bool, Dict, List[str]]: (sukces, dane, błędy)
        """
        errors = []
        data = {}
        
        try:
            path = Path(file_path)
            if not path.exists():
                errors.append(f"Plik nie istnieje: {file_path}")
                return False, {}, errors
            
            self.logger.info(f"Czytanie pliku XML: {file_path}")
            
            # Walidacja struktury XML
            with open(path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            is_valid, validation_errors = self.validator.validate_xml_structure(xml_content)
            if not is_valid:
                errors.extend(validation_errors)
                return False, {}, errors
            
            # Parsowanie XML
            tree = ET.parse(path)
            root = tree.getroot()
            
            data = self._xml_element_to_dict(root)
            
            self.logger.info(f"Pomyślnie wczytano plik XML: {len(data)} elementów")
            
        except ET.ParseError as e:
            error_msg = f"Błąd parsowania XML: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"Błąd odczytu pliku XML: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, data, errors
    
    def write_xml_file(self, file_path: str, data: Dict, root_name: str = 'root') -> Tuple[bool, List[str]]:
        """
        Zapisuje dane do pliku XML
        
        Args:
            file_path: Ścieżka do pliku
            data: Dane do zapisania
            root_name: Nazwa elementu głównego
            
        Returns:
            Tuple[bool, List[str]]: (sukces, błędy)
        """
        errors = []
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Zapisywanie pliku XML: {file_path}")
            
            # Tworzenie struktury XML
            root = ET.Element(root_name)
            self._dict_to_xml_element(data, root)
            
            # Formatowanie XML
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='  ')
            
            # Usunięcie pustych linii
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            formatted_xml = '\n'.join(lines)
            
            with open(path, 'w', encoding='utf-8') as file:
                file.write(formatted_xml)
            
            self.logger.info(f"Pomyślnie zapisano plik XML: {path.stat().st_size} bajtów")
            
        except Exception as e:
            error_msg = f"Błąd zapisu pliku XML: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, errors
    
    def _xml_element_to_dict(self, element: ET.Element) -> Dict:
        """
        Konwertuje element XML do słownika (rekurencyjnie).
        
        Metoda prywatna używana wewnętrznie przez read_xml_file().
        Przekształca hierarchiczną strukturę XML w zagnieżdżone słowniki.
        
        Args:
            element: element XML do przekonwertowania
            
        Returns:
            Dict: słownik reprezentujący element XML
            
        Obsługuje:
        - Atrybuty XML (jako '@attributes')
        - Tekst elementu (jako 'text' lub bezpośrednia wartość)
        - Elementy potomne (rekurencyjnie)
        - Elementy o tej samej nazwie (jako lista)
        """
        result = {}  # słownik wynikowy
        
        # Dodaj atrybuty elementu (np. <element attr1="value1">)
        if element.attrib:
            result['@attributes'] = element.attrib  # atrybuty pod specjalnym kluczem
        
        # Dodaj tekst wewnątrz elementu
        if element.text and element.text.strip():  # jeśli element ma tekst (nie tylko whitespace)
            if len(element) == 0:  # element bez dzieci - zwróć tylko tekst
                return element.text.strip()
            result['text'] = element.text.strip()  # element z dziećmi - tekst jako klucz 'text'
        
        # Dodaj elementy potomne (rekurencyjnie)
        for child in element:
            child_data = self._xml_element_to_dict(child)  # rekurencyjne wywołanie dla dziecka
            
            # Obsługa elementów o tej samej nazwie (tworzenie listy)
            if child.tag in result:  # jeśli klucz już istnieje
                if not isinstance(result[child.tag], list):  # jeśli nie jest jeszcze listą
                    result[child.tag] = [result[child.tag]]  # zamień na listę
                result[child.tag].append(child_data)  # dodaj nowy element do listy
            else:
                result[child.tag] = child_data  # pierwszy element o tej nazwie
        
        return result
    
    def _dict_to_xml_element(self, data: Any, parent: ET.Element):
        """
        Konwertuje słownik do elementów XML (rekurencyjnie).
        
        Metoda prywatna używana wewnętrznie przez write_xml_file().
        Odwrotność _xml_element_to_dict() - tworzy strukturę XML ze słownika.
        
        Args:
            data: dane do przekonwertowania (słownik, lista lub wartość prosta)
            parent: element XML-owy rodzic, do którego dodawane są nowe elementy
            
        Obsługuje:
        - Słowniki: klucze stają się nazwami elementów XML
        - Listy: każdy element staje się osobnym elementem <item>
        - Wartości proste: stają się tekstem elementu
        - Specjalne klucze: '@attributes' i 'text'
        """
        if isinstance(data, dict):  # jeśli dane to słownik
            for key, value in data.items():  # przejdź przez wszystkie pary klucz-wartość
                if key == '@attributes':  # specjalny klucz dla atrybutów
                    parent.attrib.update(value)  # dodaj atrybuty do elementu rodzica
                elif key == 'text':  # specjalny klucz dla tekstu elementu
                    parent.text = str(value)  # ustaw tekst elementu rodzica
                else:  # zwykły klucz staje się nowym elementem XML
                    child = ET.SubElement(parent, str(key))  # utwórz dziecko o nazwie klucza
                    self._dict_to_xml_element(value, child)  # rekurencyjnie przetwórz wartość
        elif isinstance(data, list):  # jeśli dane to lista
            for item in data:  # dla każdego elementu listy
                child = ET.SubElement(parent, 'item')  # utwórz element <item>
                self._dict_to_xml_element(item, child)  # rekurencyjnie przetwórz element
        else:  # wartość prosta (string, liczba, bool)
            parent.text = str(data)  # ustaw jako tekst elementu
    
    def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """
        Pobiera szczegółowe metadane pliku (rozmiar, daty, format).
        
        Args:
            file_path: ścieżka do pliku (względna lub bezwzględna)
            
        Returns:
            FileMetadata: obiekt z metadanymi lub None jeśli plik nie istnieje
            
        Metadane zawierają:
        - Pełną ścieżkę do pliku
        - Rozmiar w bajtach
        - Daty utworzenia i modyfikacji
        - Format pliku (rozszerzenie)
        - Kodowanie (domyślnie UTF-8)
        """
        try:
            path = Path(file_path)  # utwórz obiekt Path dla lepszej obsługi ścieżek
            if not path.exists():  # sprawdź czy plik istnieje
                return None  # zwróć None jeśli plik nie istnieje
            
            stat = path.stat()  # pobierz informacje systemowe o pliku
            
            # Utwórz obiekt FileMetadata z zebranymi informacjami
            return FileMetadata(
                path=str(path.absolute()),  # pełna, bezwzględna ścieżka
                size=stat.st_size,  # rozmiar w bajtach
                created=datetime.fromtimestamp(stat.st_ctime),  # data utworzenia (z timestamp)
                modified=datetime.fromtimestamp(stat.st_mtime),  # data ostatniej modyfikacji
                format=path.suffix.lower(),  # rozszerzenie pliku (.json, .csv, etc.)
                encoding='utf-8'  # domyślne kodowanie (może być rozszerzone w przyszłości)
            )
            
        except Exception as e:
            # Zaloguj błąd i zwróć None w przypadku problemów
            self.logger.error(f"Błąd pobierania metadanych pliku {file_path}: {str(e)}")
            return None
    
    def create_backup(self, file_path: str, backup_dir: str = 'backups') -> Tuple[bool, str]:
        """
        Tworzy kopię zapasową pliku z automatycznym nazewnictwem.
        
        Args:
            file_path: ścieżka do pliku źródłowego do skopiowania
            backup_dir: katalog docelowy dla kopii zapasowej (domyślnie 'backups')
            
        Returns:
            Tuple[bool, str]: (czy_sukces, ścieżka_kopii_lub_komunikat_błędu)
            
        Funkcja:
        - Sprawdza czy plik źródłowy istnieje
        - Tworzy katalog backupów jeśli nie istnieje
        - Generuje unikalną nazwę z timestamp'em
        - Kopiuje plik zachowując metadane (copy2)
        
        Przykład nazwy backupu: "config_20231215_143022.json"
        """
        try:
            source_path = Path(file_path)  # ścieżka do pliku źródłowego
            if not source_path.exists():  # sprawdź czy plik istnieje
                return False, f"Plik nie istnieje: {file_path}"
            
            # Tworzenie katalogu kopii zapasowych (z parents=True dla zagnieżdżonych folderów)
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)  # exist_ok=True - nie błąd jeśli istnieje
            
            # Nazwa kopii zapasowej z timestamp'em (YYYYMMDD_HHMMSS)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # format: 20231215_143022
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"  # nazwa_timestamp.rozszerzenie
            backup_file_path = backup_path / backup_filename  # pełna ścieżka do kopii
            
            # Kopiowanie pliku z zachowaniem metadanych (daty, uprawnienia)
            shutil.copy2(source_path, backup_file_path)  # copy2 zachowuje więcej metadanych niż copy
            
            self.logger.info(f"Utworzono kopię zapasową: {backup_file_path}")
            return True, str(backup_file_path)  # zwróć ścieżkę do utworzonej kopii
            
        except Exception as e:
            error_msg = f"Błąd tworzenia kopii zapasowej: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def compress_files(self, file_paths: List[str], archive_path: str) -> Tuple[bool, List[str]]:
        """
        Kompresuje listę plików do archiwum ZIP z kompresją DEFLATE.
        
        Args:
            file_paths: lista ścieżek do plików do skompresowania
            archive_path: ścieżka docelowa dla archiwum ZIP
            
        Returns:
            Tuple[bool, List[str]]: (czy_sukces, lista_błędów)
            
        Funkcjonalność:
        - Tworzy katalog docelowy jeśli nie istnieje
        - Używa kompresji ZIP_DEFLATED (standardowa kompresja ZIP)
        - Dodaje pliki do archiwum zachowując tylko nazwy (bez pełnych ścieżek)
        - Kontynuuje pracę nawet jeśli niektóre pliki nie istnieją
        - Loguje szczegóły procesu
        """
        errors = []  # lista błędów napotkanych podczas procesu
        
        try:
            archive_path_obj = Path(archive_path)  # obiekt Path dla archiwum
            archive_path_obj.parent.mkdir(parents=True, exist_ok=True)  # utwórz katalog docelowy
            
            self.logger.info(f"Tworzenie archiwum: {archive_path}")
            
            # Otwórz archiwum ZIP w trybie zapisu z kompresją DEFLATE
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:  # przejdź przez wszystkie pliki
                    path = Path(file_path)
                    if path.exists():  # jeśli plik istnieje
                        # Dodaj plik do archiwum używając tylko nazwy pliku (bez ścieżki)
                        zipf.write(path, path.name)  # path.name = nazwa pliku bez ścieżki
                        self.logger.debug(f"Dodano do archiwum: {path.name}")
                    else:
                        # Zanotuj błąd ale kontynuuj z pozostałymi plikami
                        errors.append(f"Plik nie istnieje: {file_path}")
            
            # Jeśli nie ma błędów, zaloguj sukces z rozmiarem archiwum
            if len(errors) == 0:
                archive_size = archive_path_obj.stat().st_size  # rozmiar utworzonego archiwum
                self.logger.info(f"Pomyślnie utworzono archiwum: {archive_size} bajtów")
            
        except Exception as e:
            # Krytyczny błąd podczas tworzenia archiwum
            error_msg = f"Błąd tworzenia archiwum: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, errors  # sukces jeśli brak błędów
    
    def extract_archive(self, archive_path: str, extract_dir: str) -> Tuple[bool, List[str]]:
        """
        Wypakowuje zawartość archiwum ZIP do wskazanego katalogu.
        
        Args:
            archive_path: ścieżka do archiwum ZIP do wypakowania
            extract_dir: katalog docelowy gdzie wypakować pliki
            
        Returns:
            Tuple[bool, List[str]]: (czy_sukces, lista_błędów)
            
        Funkcjonalność:
        - Sprawdza czy archiwum istnieje
        - Tworzy katalog docelowy jeśli nie istnieje
        - Wypakowuje wszystkie pliki z archiwum
        - Zachowuje strukturę katalogów z archiwum
        - Loguje proces wypakowywania
        
        Uwaga: Używa extractall() co jest bezpieczne dla zaufanych archiwów.
        """
        errors = []  # lista błędów podczas wypakowywania
        
        try:
            archive_path_obj = Path(archive_path)  # obiekt Path dla archiwum
            if not archive_path_obj.exists():  # sprawdź czy archiwum istnieje
                errors.append(f"Archiwum nie istnieje: {archive_path}")
                return False, errors
            
            extract_path = Path(extract_dir)  # obiekt Path dla katalogu docelowego
            extract_path.mkdir(parents=True, exist_ok=True)  # utwórz katalog docelowy
            
            self.logger.info(f"Wypakowywanie archiwum: {archive_path}")
            
            # Otwórz archiwum ZIP w trybie odczytu i wypakuj wszystko
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_path)  # wypakuj wszystkie pliki do katalogu docelowego
            
            self.logger.info(f"Pomyślnie wypakowano archiwum do: {extract_dir}")
            
        except zipfile.BadZipFile as e:
            # Błąd specyficzny dla uszkodzonych archiwów ZIP
            error_msg = f"Uszkodzone archiwum ZIP: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            # Ogólny błąd wypakowywania
            error_msg = f"Błąd wypakowywania archiwum: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, errors  # sukces jeśli brak błędów
    
    def cleanup_old_files(self, directory: str, days_old: int, pattern: str = '*') -> Tuple[int, List[str]]:
        """
        Usuwa stare pliki z katalogu na podstawie daty modyfikacji.
        
        Args:
            directory: katalog do wyczyszczenia
            days_old: maksymalny wiek plików w dniach (starsze będą usunięte)
            pattern: wzorzec nazw plików do sprawdzenia (domyślnie '*' = wszystkie)
            
        Returns:
            Tuple[int, List[str]]: (liczba_usuniętych_plików, lista_błędów)
            
        Funkcjonalność:
        - Sprawdza wszystkie pliki pasujące do wzorca
        - Usuwa pliki starsze niż określona liczba dni
        - Używa daty ostatniej modyfikacji pliku (st_mtime)
        - Loguje każde usunięcie dla audytu
        - Kontynuuje nawet jeśli niektóre pliki nie mogą być usunięte
        
        Przykłady wzorców:
        - '*' - wszystkie pliki
        - '*.log' - tylko pliki .log
        - 'backup_*' - pliki zaczynające się od 'backup_'
        """
        errors = []  # lista błędów podczas czyszczenia
        deleted_count = 0  # licznik usuniętych plików
        
        try:
            dir_path = Path(directory)  # obiekt Path dla katalogu
            if not dir_path.exists():  # sprawdź czy katalog istnieje
                errors.append(f"Katalog nie istnieje: {directory}")
                return 0, errors
            
            # Oblicz timestamp graniczny (pliki starsze od tego czasu będą usunięte)
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)  # days_old dni temu w sekundach
            
            # Przeszukaj wszystkie pliki pasujące do wzorca
            for file_path in dir_path.glob(pattern):  # glob() używa wzorców jak w shell'u
                if file_path.is_file():  # sprawdź czy to plik (nie katalog)
                    file_mtime = file_path.stat().st_mtime  # czas ostatniej modyfikacji
                    if file_mtime < cutoff_time:  # jeśli plik starszy niż granica
                        try:
                            file_path.unlink()  # usuń plik (unlink = usunięcie pliku)
                            deleted_count += 1  # zwiększ licznik
                            self.logger.debug(f"Usunięto stary plik: {file_path}")
                        except Exception as e:
                            # Nie udało się usunąć konkretnego pliku - zanotuj błąd
                            errors.append(f"Nie można usunąć {file_path}: {str(e)}")
            
            # Zaloguj podsumowanie operacji czyszczenia
            self.logger.info(f"Usunięto {deleted_count} starych plików z {directory}")
            
        except Exception as e:
            # Ogólny błąd czyszczenia katalogu
            error_msg = f"Błąd czyszczenia katalogu: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return deleted_count, errors  # zwróć liczbę usuniętych plików i błędy


# ============================================================================
# FUNKCJA SINGLETON - GLOBALNA INSTANCJA PROCESORA PLIKÓW
# ============================================================================

# Globalna instancja procesora plików (wzorzec Singleton)
_file_processor_instance = None

def get_file_processor() -> FileProcessor:
    """
    Zwraca globalną instancję procesora plików (wzorzec Singleton).
    
    Wzorzec Singleton zapewnia że w całej aplikacji istnieje tylko jedna
    instancja FileProcessor'a. Dzięki temu:
    - Oszczędzamy pamięć
    - Mamy spójne logowanie
    - Unikamy wielokrotnej inicjalizacji
    
    Returns:
        FileProcessor: globalna instancja procesora plików
        
    Użycie:
        processor = get_file_processor()
        processor.read_json_file("config.json")
    """
    global _file_processor_instance  # odwołanie do zmiennej globalnej
    if _file_processor_instance is None:  # jeśli instancja nie istnieje
        _file_processor_instance = FileProcessor()  # utwórz nową instancję
    return _file_processor_instance  # zwróć istniejącą instancję 