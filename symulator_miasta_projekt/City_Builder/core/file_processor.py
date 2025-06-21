"""
Zaawansowane przetwarzanie plików i katalogów
Obsługuje różne formaty danych: CSV, JSON, XML
Implementuje system logowania zdarzeń
"""

import os
import csv
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterator, Tuple
import logging
from datetime import datetime
import shutil
import zipfile
import tempfile
from dataclasses import dataclass, asdict
import pandas as pd

from .data_validator import get_data_validator
from .logger import get_game_logger

@dataclass
class FileMetadata:
    """Metadane pliku"""
    path: str
    size: int
    created: datetime
    modified: datetime
    format: str
    encoding: str = 'utf-8'
    checksum: Optional[str] = None

class FileProcessor:
    """Klasa do zaawansowanego przetwarzania plików"""
    
    def __init__(self):
        """Inicjalizuje procesor plików"""
        self.validator = get_data_validator()
        self.logger = get_game_logger().get_logger('file_processor')
        self.supported_formats = {'.json', '.csv', '.xml', '.txt', '.log'}
        
    def read_json_file(self, file_path: str) -> Tuple[bool, Dict, List[str]]:
        """
        Czyta i waliduje plik JSON
        
        Args:
            file_path: Ścieżka do pliku JSON
            
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
            
            self.logger.info(f"Czytanie pliku JSON: {file_path}")
            
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
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
        Zapisuje dane do pliku JSON
        
        Args:
            file_path: Ścieżka do pliku
            data: Dane do zapisania
            pretty: Czy formatować JSON czytelnie
            
        Returns:
            Tuple[bool, List[str]]: (sukces, błędy)
        """
        errors = []
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
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
        Czyta plik CSV i zwraca listę słowników
        
        Args:
            file_path: Ścieżka do pliku CSV
            delimiter: Separator kolumn
            
        Returns:
            Tuple[bool, List[Dict], List[str]]: (sukces, dane, błędy)
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
                # Automatyczne wykrywanie dialektu CSV
                sample = file.read(1024)
                file.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                    reader = csv.DictReader(file, dialect=dialect)
                except csv.Error:
                    reader = csv.DictReader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    # Walidacja każdego wiersza
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
        Zapisuje dane do pliku CSV
        
        Args:
            file_path: Ścieżka do pliku
            data: Lista słowników do zapisania
            fieldnames: Lista nazw kolumn (opcjonalne)
            
        Returns:
            Tuple[bool, List[str]]: (sukces, błędy)
        """
        errors = []
        
        try:
            if not data:
                errors.append("Brak danych do zapisania")
                return False, errors
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Zapisywanie pliku CSV: {file_path}")
            
            # Automatyczne wykrywanie nazw kolumn
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
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
        """Konwertuje element XML do słownika"""
        result = {}
        
        # Dodaj atrybuty
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Dodaj tekst
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Dodaj elementy potomne
        for child in element:
            child_data = self._xml_element_to_dict(child)
            
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _dict_to_xml_element(self, data: Any, parent: ET.Element):
        """Konwertuje słownik do elementów XML"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '@attributes':
                    parent.attrib.update(value)
                elif key == 'text':
                    parent.text = str(value)
                else:
                    child = ET.SubElement(parent, str(key))
                    self._dict_to_xml_element(value, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, 'item')
                self._dict_to_xml_element(item, child)
        else:
            parent.text = str(data)
    
    def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """
        Pobiera metadane pliku
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            FileMetadata lub None jeśli plik nie istnieje
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            
            return FileMetadata(
                path=str(path.absolute()),
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                format=path.suffix.lower(),
                encoding='utf-8'  # Domyślnie UTF-8
            )
            
        except Exception as e:
            self.logger.error(f"Błąd pobierania metadanych pliku {file_path}: {str(e)}")
            return None
    
    def create_backup(self, file_path: str, backup_dir: str = 'backups') -> Tuple[bool, str]:
        """
        Tworzy kopię zapasową pliku
        
        Args:
            file_path: Ścieżka do pliku
            backup_dir: Katalog kopii zapasowych
            
        Returns:
            Tuple[bool, str]: (sukces, ścieżka_kopii_lub_błąd)
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False, f"Plik nie istnieje: {file_path}"
            
            # Tworzenie katalogu kopii zapasowych
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Nazwa kopii zapasowej z timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_filename
            
            # Kopiowanie pliku
            shutil.copy2(source_path, backup_file_path)
            
            self.logger.info(f"Utworzono kopię zapasową: {backup_file_path}")
            return True, str(backup_file_path)
            
        except Exception as e:
            error_msg = f"Błąd tworzenia kopii zapasowej: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def compress_files(self, file_paths: List[str], archive_path: str) -> Tuple[bool, List[str]]:
        """
        Kompresuje pliki do archiwum ZIP
        
        Args:
            file_paths: Lista ścieżek do plików
            archive_path: Ścieżka do archiwum
            
        Returns:
            Tuple[bool, List[str]]: (sukces, błędy)
        """
        errors = []
        
        try:
            archive_path_obj = Path(archive_path)
            archive_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Tworzenie archiwum: {archive_path}")
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    path = Path(file_path)
                    if path.exists():
                        zipf.write(path, path.name)
                        self.logger.debug(f"Dodano do archiwum: {path.name}")
                    else:
                        errors.append(f"Plik nie istnieje: {file_path}")
            
            if len(errors) == 0:
                self.logger.info(f"Pomyślnie utworzono archiwum: {archive_path_obj.stat().st_size} bajtów")
            
        except Exception as e:
            error_msg = f"Błąd tworzenia archiwum: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, errors
    
    def extract_archive(self, archive_path: str, extract_dir: str) -> Tuple[bool, List[str]]:
        """
        Wypakowuje archiwum ZIP
        
        Args:
            archive_path: Ścieżka do archiwum
            extract_dir: Katalog docelowy
            
        Returns:
            Tuple[bool, List[str]]: (sukces, błędy)
        """
        errors = []
        
        try:
            archive_path_obj = Path(archive_path)
            if not archive_path_obj.exists():
                errors.append(f"Archiwum nie istnieje: {archive_path}")
                return False, errors
            
            extract_path = Path(extract_dir)
            extract_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Wypakowywanie archiwum: {archive_path}")
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_path)
            
            self.logger.info(f"Pomyślnie wypakowano archiwum do: {extract_dir}")
            
        except Exception as e:
            error_msg = f"Błąd wypakowywania archiwum: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return len(errors) == 0, errors
    
    def cleanup_old_files(self, directory: str, days_old: int, pattern: str = '*') -> Tuple[int, List[str]]:
        """
        Usuwa stare pliki z katalogu
        
        Args:
            directory: Katalog do czyszczenia
            days_old: Wiek plików w dniach
            pattern: Wzorzec nazw plików
            
        Returns:
            Tuple[int, List[str]]: (liczba_usuniętych, błędy)
        """
        errors = []
        deleted_count = 0
        
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                errors.append(f"Katalog nie istnieje: {directory}")
                return 0, errors
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            self.logger.debug(f"Usunięto stary plik: {file_path}")
                        except Exception as e:
                            errors.append(f"Nie można usunąć {file_path}: {str(e)}")
            
            self.logger.info(f"Usunięto {deleted_count} starych plików z {directory}")
            
        except Exception as e:
            error_msg = f"Błąd czyszczenia katalogu: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        return deleted_count, errors


# Globalna instancja procesora plików
_file_processor_instance = None

def get_file_processor() -> FileProcessor:
    """Zwraca globalną instancję procesora plików (singleton)"""
    global _file_processor_instance
    if _file_processor_instance is None:
        _file_processor_instance = FileProcessor()
    return _file_processor_instance 