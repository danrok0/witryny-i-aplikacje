import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class DataStorage:
    """Klasa do zarządzania przechowywaniem danych w plikach cache."""

    def __init__(self, data_dir: str = "data"):
        """Inicjalizuje obiekt DataStorage z określonym katalogiem danych."""
        self._data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    @property
    def data_dir(self) -> str:
        """Zwraca ścieżkę do katalogu z danymi."""
        return self._data_dir

    def _get_cache_path(self, filename: str) -> str:
        """Pobiera pełną ścieżkę do pliku cache."""
        return os.path.join(self._data_dir, filename)

    def save_data(self, filename: str, data: Dict[str, Any]) -> None:
        """Zapisuje dane do pliku JSON w określonym katalogu."""
        filepath = self._get_cache_path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self, filename: str) -> Dict[str, Any]:
        """Wczytuje dane z pliku JSON z określonego katalogu."""
        filepath = self._get_cache_path(filename)
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def append_data(self, filename: str, new_data: Dict[str, Any]) -> None:
        """Dodaje nowe dane do istniejącego pliku JSON."""
        existing_data = self.load_data(filename)
        existing_data.update(new_data)
        self.save_data(filename, existing_data)

    def clear_data(self, filename: str) -> None:
        """Czyści dane w pliku JSON."""
        self.save_data(filename, {})

    def get_all_files(self) -> List[str]:
        """Zwraca listę wszystkich plików w katalogu danych."""
        return [f for f in os.listdir(self._data_dir) if f.endswith('.json')]

    def save_data_to_cache(self, data: Any, filename: str) -> None:
        """Zapisuje dane do pliku JSON, łącząc z istniejącymi danymi jeśli są obecne."""
        filepath = self._get_cache_path(filename)
        
        # Próba wczytania istniejących danych
        existing_data = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                pass

        # Przygotowanie nowego wpisu danych
        new_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # Jeśli plik istnieje i zawiera listę, dodaj nowe dane
        if isinstance(existing_data.get('data'), list):
            existing_data['data'] = data  # Nadpisz stare dane nowymi
        else:
            existing_data = new_entry

        # Zapisz zaktualizowane dane
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def load_data_from_cache(self, filename: str, max_age_hours: Optional[int] = None) -> Optional[Any]:
        """Wczytuje dane z pliku JSON jeśli istnieje i nie jest zbyt stary."""
        filepath = self._get_cache_path(filename)
        
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            if max_age_hours is not None:
                cache_time = datetime.fromisoformat(cached['timestamp'])
                if datetime.now() - cache_time > timedelta(hours=max_age_hours):
                    return None

            return cached['data']
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def clear_cache(self, filename: str = None) -> None:
        """Czyści pliki cache. Jeśli filename jest None, czyści wszystkie pliki cache."""
        if filename:
            filepath = self._get_cache_path(filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        else:
            for file in os.listdir(self._data_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self._data_dir, file))

    def merge_json_files(self, output_file: str = "all_data.json") -> None:
        """Łączy wszystkie pliki JSON w katalogu cache w jeden plik."""
        all_data = {
            'timestamp': datetime.now().isoformat(),
            'trails': [],
            'weather': {}
        }

        for filename in os.listdir(self._data_dir):
            if not filename.endswith('.json'):
                continue

            filepath = self._get_cache_path(filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                if filename.startswith('trails_'):
                    # Dodaj dane o szlakach
                    if isinstance(file_data.get('data'), list):
                        all_data['trails'].extend(file_data['data'])
                elif filename.startswith('weather_'):
                    # Dodaj dane pogodowe
                    city = filename[8:-5]  # Usuń 'weather_' i '.json'
                    if file_data.get('data'):
                        all_data['weather'][city] = file_data['data']

            except (json.JSONDecodeError, KeyError):
                continue

        # Zapisz połączone dane
        output_path = self._get_cache_path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)