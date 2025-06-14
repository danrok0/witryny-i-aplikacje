from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import os

class BaseStorage:
    """Bazowa klasa dla przechowywania danych."""
    
    def __init__(self, directory: str):
        self._directory = directory
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    def _get_file_path(self, filename: str) -> str:
        """Pobiera pełną ścieżkę do pliku."""
        return os.path.join(self._directory, filename)
        
    def save_json(self, data: Dict[str, Any], filename: str) -> None:
        """Zapisuje dane w formacie JSON."""
        try:
            filepath = self._get_file_path(filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd podczas zapisywania danych JSON: {e}")
            
    def load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """Wczytuje dane z pliku JSON."""
        try:
            filepath = self._get_file_path(filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd podczas wczytywania danych JSON: {e}")
            return None

class ResultStorage(BaseStorage):
    """Klasa do przechowywania wyników rekomendacji."""
    
    def __init__(self, output_file: str = 'result.txt'):
        super().__init__(os.path.dirname(output_file) or '.')
        self._output_file = output_file
    
    def save_trails_to_file(self, trails: List[Dict[str, Any]], region: str, 
                           weather: Optional[Dict[str, Any]] = None) -> None:
        """
        Zapisuje rekomendowane trasy do pliku wynikowego.
        
        Args:
            trails: Lista słowników z trasami
            region: Nazwa wybranego regionu
            weather: Opcjonalny słownik z danymi pogodowymi
        """
        try:
            with open(self._output_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Rekomendacje szlaków dla regionu {region} ===\n")
                f.write(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if weather:
                    from utils.weather_utils import WeatherUtils
                    comfort_index = WeatherUtils.calculate_hiking_comfort(weather)
                    
                    f.write("Warunki pogodowe:\n")
                    f.write(f"  Temperatura: {weather.get('temperature', 'brak danych')}°C\n")
                    f.write(f"  Opady: {weather.get('precipitation', 'brak danych')} mm\n")
                    f.write(f"  Godziny słoneczne: {weather.get('sunshine_hours', 'brak danych')}\n")
                    f.write(f"  Indeks komfortu wędrówki: {comfort_index}/100\n\n")
                
                if not trails:
                    f.write("Nie znaleziono szlaków spełniających podane kryteria.\n")
                    return
                    
                for i, trail in enumerate(trails, 1):
                    f.write(f"\n{i}. {trail['name']}\n")
                    f.write(f"   Długość: {trail.get('length_km', 'brak danych')} km\n")
                    f.write(f"   Trudność: {trail.get('difficulty', 'brak danych')}/3\n")
                    f.write(f"   Przewidywany czas przejścia: {trail.get('estimated_time', 'brak danych')} godz.\n")
                    f.write(f"   Przewyższenie: {trail.get('elevation', 'brak danych')} m\n")
                    if trail.get('description'):
                        f.write(f"   Opis: {trail['description']}\n")
                    
                f.write(f"\nŁącznie znaleziono {len(trails)} tras spełniających kryteria.\n")
                
        except Exception as e:
            print(f"Błąd podczas zapisywania wyników do pliku: {e}")

def save_results_to_file(trails: List[Dict[str, Any]], region: str, 
                        weather: Optional[Dict[str, Any]] = None,
                        output_file: str = 'result.txt') -> None:
    """Funkcja pomocnicza do zapisywania wyników."""
    storage = ResultStorage(output_file)
    storage.save_trails_to_file(trails, region, weather)