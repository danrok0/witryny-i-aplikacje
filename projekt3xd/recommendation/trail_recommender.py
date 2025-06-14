from typing import List, Dict, Any, Optional
from functools import reduce
from datetime import datetime
import os
import sys

# Dodaj katalog projektu do ścieżki Pythona
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from data_handlers.trail_data import TrailDataHandler
from utils.weather_utils import WeatherUtils
from utils.weight_calculator import WeightCalculator
from utils.time_calculator import TimeCalculator

try:
    from reporters.pdf_report_generator import PDFReportGenerator
except ImportError:
    print("Ostrzeżenie: Nie można zaimportować PDFReportGenerator")
    PDFReportGenerator = None

class TrailRecommender:
    def __init__(self):
        """Inicjalizuje obiekt TrailRecommender z obsługą danych."""
        self.data_handler = TrailDataHandler()
        self.weight_calculator = WeightCalculator()
        
        # Inicjalizuj generator raportów PDF jeśli dostępny
        self.pdf_generator = PDFReportGenerator() if PDFReportGenerator else None
    
    def set_weights_from_user(self) -> Dict[str, float]:
        """
        Pobiera wagi od użytkownika i ustawia je w kalkulatorze.
        
        Returns:
            Dict[str, float]: Ustawione wagi
        """
        return self.weight_calculator.get_weights_from_user()

    def _categorize_trail(self, trail: Dict[str, Any]) -> str:
        """
        Kategoryzuje trasę na podstawie jej charakterystyki.
        
        Kryteria:
        - rodzinna: łatwe (trudność 1), krótkie trasy (<5km), małe przewyższenie (<200m)
        - widokowa: punkty widokowe, trasy turystyczne ze sceneriami
        - sportowa: średnie/długie trasy (5-15km), średnia trudność
        - ekstremalna: trudne trasy, duże przewyższenie, długie dystanse
        """
        difficulty = trail.get('difficulty', 1)
        length = trail.get('length_km', 0)
        elevation = trail.get('elevation_m', 0)
        tags = trail.get('tags', [])
        description = str(trail.get('description', '')).lower()
        
        # Zaczynamy od sprawdzenia trasy rodzinnej (najprostsze kryteria)
        if difficulty == 1 and length < 5 and elevation < 200:
            if (any(tag in ['leisure', 'park', 'playground', 'family'] for tag in tags) or
                any(keyword in description for keyword in ['rodzin', 'łatw', 'spokojna', 'dziec'])):
                return "rodzinna"
            
        # Następnie sprawdzamy trasę widokową
        if (length < 15 and  # Trasy widokowe zazwyczaj nie są zbyt długie
            (any(tag in ['viewpoint', 'scenic', 'tourism', 'view_point', 'panorama'] for tag in tags) or
             any(keyword in description for keyword in ['widok', 'panoram', 'scenic', 'krajobraz', 'punkt widokowy']))):
            return "widokowa"
            
        # Sprawdzamy trasę ekstremalną
        if (difficulty == 3 or length > 15 or elevation > 800 or
            any(tag in ['climbing', 'alpine', 'via_ferrata', 'extreme'] for tag in tags) or
            any(keyword in description for keyword in ['ekstre', 'trudna', 'wymagając', 'alpejsk'])):
            return "ekstremalna"
            
        # Jeśli trasa ma średnią trudność i długość, klasyfikujemy jako sportową
        if ((difficulty == 2 and 5 <= length <= 15) or
            any(keyword in description for keyword in ['sport', 'aktyw', 'kondycyj', 'wysiłk'])):
            return "sportowa"
            
        # Jeśli nie pasuje do żadnej kategorii, przypisujemy na podstawie długości i trudności
        if length < 5:
            return "rodzinna"
        elif length > 15 or difficulty == 3:
            return "ekstremalna"
        elif difficulty == 2 or 5 <= length <= 15:
            return "sportowa"
        else:
            # Jeśli naprawdę nie możemy określić, dajemy widokową jako najbezpieczniejszą opcję
            return "widokowa"

    def _calculate_comfort_indices(self, trails: List[Dict[str, Any]], 
                                weather: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Oblicza indeks komfortu dla każdej trasy na podstawie warunków pogodowych.
        
        Args:
            trails (List[Dict[str, Any]]): Lista tras
            weather (Optional[Dict[str, Any]]): Dane pogodowe
            
        Returns:
            List[Dict[str, Any]]: Lista tras z dodanym indeksem komfortu
        """
        if not weather:
            return trails

        # Dla każdej trasy oblicz indywidualny indeks komfortu
        for trail in trails:
            # Dostosuj warunki pogodowe do specyfiki trasy
            trail_weather = weather.copy()
            
            # Modyfikuj warunki w zależności od typu terenu i wysokości
            if trail.get('terrain_type') == 'górski':
                # W górach temperatura jest niższa (średnio o 0.6°C na 100m wysokości)
                elevation = trail.get('elevation', 0)
                temp_adjustment = (elevation / 100) * 0.6
                trail_weather['temperature_2m_mean'] = weather.get('temperature_2m_mean', 0) - temp_adjustment
                # W górach więcej opadów
                trail_weather['precipitation_sum'] = weather.get('precipitation_sum', 0) * 1.2
            
            # Oblicz indeks komfortu dla konkretnej trasy
            trail['comfort_index'] = WeatherUtils.calculate_hiking_comfort(trail_weather)
            
        return trails
    
    def _calculate_trail_time(self, trail: Dict[str, Any]) -> float:
        """
        Oblicza szacowany czas przejścia trasy w godzinach.
        
        Parametry brane pod uwagę:
        - Długość trasy (1km = 1h bazowego czasu)
        - Trudność (mnożnik 1.0-1.8)
        - Typ terenu (różne prędkości)
        
        Returns:
            float: Szacowany czas przejścia w godzinach
        """
        # Długość trasy w km
        length = trail.get('length_km', 0)
        
        # Mnożnik trudności (1-3 -> 1.0-1.8)
        difficulty = trail.get('difficulty', 1)
        difficulty_multiplier = 1.0 + (difficulty - 1) * 0.4  # 1.0, 1.4, lub 1.8
        
        # Mnożnik terenu
        terrain_multipliers = {
            'górski': 1.6,    # Najtrudniejszy teren
            'miejski': 0.8,   # Najłatwiejszy teren
            'leśny': 1.2,     # Średnio trudny teren
            'nizinny': 1.0,   # Bazowy teren
            'mixed': 1.3,     # Teren mieszany
            'riverside': 1.1   # Teren nadrzeczny
        }
        
        terrain_type = trail.get('terrain_type', 'mixed').lower()
        terrain_multiplier = terrain_multipliers.get(terrain_type, 1.3)
        
        # Obliczenie całkowitego czasu
        total_time = length * difficulty_multiplier * terrain_multiplier
        
        return round(total_time, 1)

    def recommend_trails(
        self,
        city: str,
        date: str,
        difficulty: Optional[int] = None,
        terrain_type: Optional[str] = None,
        min_length: Optional[float] = None,
        max_length: Optional[float] = None,
        min_sunshine: Optional[float] = None,
        max_precipitation: Optional[float] = None,
        min_temperature: Optional[float] = None,
        max_temperature: Optional[float] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Rekomenduje trasy na podstawie różnych kryteriów."""
        try:
            # Pobierz wszystkie trasy dla danego miasta
            trails = self.data_handler.get_trails_for_city(city)
            if not trails:
                print(f"Nie znaleziono tras dla miasta {city}")
                return []

            print(f"\nZnaleziono {len(trails)} szlaków dla miasta {city}")

            # Pobieranie prognozy pogody
            print(f"\nPobieranie danych pogodowych dla {city} na dzień {date}...")
            weather = self.data_handler.weather_api.get_weather_forecast(city, date)
            
            # Dodaj kategorię i szacowany czas przejścia do każdej trasy
            for trail in trails:
                trail['category'] = self._categorize_trail(trail)
                trail['estimated_time'] = TimeCalculator.calculate_time(trail)
            
            # Filtrowanie tras używając wyrażenia lambda
            filtered_trails = list(filter(
                lambda trail: (
                    (difficulty is None or trail.get('difficulty') == difficulty) and
                    (terrain_type is None or trail.get('terrain_type') == terrain_type) and
                    (min_length is None or trail.get('length_km', 0) >= min_length) and
                    (max_length is None or trail.get('length_km', 0) <= max_length) and
                    (category is None or trail.get('category') == category)
                ),
                trails
            ))

            # Dodawanie indeksu komfortu do tras
            if weather:
                filtered_trails = self._calculate_comfort_indices(filtered_trails, weather)
                
            # Sort trails using current weights (weights should be set externally)
            filtered_trails = self.weight_calculator.sort_trails_by_weights(filtered_trails, weather or {})
              # Informacja o liczbie znalezionych tras
            if filtered_trails:
                print(f"\nZnaleziono {len(filtered_trails)} tras spełniających kryteria.")
                return filtered_trails
                ResultExporter.export_results(city, date, filtered_trails, weather)
                print("\nWyświetlam szczegóły znalezionych tras:")
                print("=" * 50)

            return filtered_trails

        except Exception as e:
            print(f"Błąd podczas rekomendacji tras: {e}")
            return []
            
    def _save_recommendations_to_file(self, city: str, date: str, trails: List[Dict[str, Any]], 
                                    weather: Optional[Dict[str, Any]] = None):
        """Zapisuje rekomendacje do pliku result.txt."""
        try:
            with open("result.txt", "a", encoding="utf-8") as f:
                f.write(f"\n=== Rekomendacje dla {city} na dzień {date} ===\n")
                f.write(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if weather:
                    comfort_index = WeatherUtils.calculate_hiking_comfort(weather)
                    f.write("Dane pogodowe:\n")
                    f.write(f"Temperatura: {weather.get('temperature_min', 'N/A')}°C - {weather.get('temperature_max', 'N/A')}°C\n")
                    f.write(f"Średnia temperatura: {weather.get('temperature_avg', 'N/A')}°C\n")
                    f.write(f"Opady: {weather.get('precipitation', 'N/A')} mm\n")
                    f.write(f"Zachmurzenie: {weather.get('cloud_cover', 'N/A')}%\n")
                    f.write(f"Godziny słoneczne: {weather.get('sunshine_hours', 'N/A')} h\n")
                    f.write(f"Prędkość wiatru: {weather.get('wind_speed', 'N/A')} km/h\n")
                    f.write(f"Indeks komfortu wędrówki: {comfort_index}/100\n\n")

                f.write(f"Znaleziono {len(trails)} tras:\n\n")
                for i, trail in enumerate(trails, 1):
                    f.write(f"{i}. {trail['name']}\n")
                    f.write(f"   Długość: {trail.get('length_km', 'N/A')} km\n")
                    f.write(f"   Poziom trudności: {trail.get('difficulty', 'N/A')}/3\n")
                    f.write(f"   Typ terenu: {trail.get('terrain_type', 'N/A')}\n")
                    f.write(f"   Kategoria: {trail.get('category', 'N/A')}\n")
                    if 'comfort_index' in trail:
                        f.write(f"   Indeks komfortu: {trail['comfort_index']}/100\n")
                    if 'description' in trail:
                        f.write(f"   Opis: {trail['description']}\n")
                    f.write("\n")
                f.write("=" * 50 + "\n")
                
            print("\nRekomendacje zostały zapisane do pliku result.txt")
        except Exception as e:
            print(f"Błąd podczas zapisywania rekomendacji do pliku: {e}")

    def generate_comprehensive_report(
        self,
        city: str,
        date: str,
        trails: List[Dict[str, Any]],
        search_params: Dict[str, Any],
        weather: Optional[Dict[str, Any]] = None,
        output_filename: str = None
    ) -> Optional[str]:
        """
        Generuje kompleksowy raport PDF z rekomendacjami tras.
        
        Args:
            city: Nazwa miasta
            date: Data wyszukiwania
            trails: Lista rekomendowanych tras
            search_params: Parametry wyszukiwania
            weather: Dane pogodowe
            output_filename: Nazwa pliku wyjściowego
            
        Returns:
            Ścieżka do wygenerowanego raportu PDF lub None w przypadku błędu
        """
        if not self.pdf_generator:
            print("Generator raportów PDF nie jest dostępny")
            return None
            
        if not trails:
            print("Brak tras do wygenerowania raportu")
            return None
        
        try:
            # Rozszerz dane tras o analizę tekstu i recenzji
            enhanced_trails = []
            for trail in trails:
                enhanced_trail = self.data_handler.enhance_trail_with_analysis(trail)
                enhanced_trails.append(enhanced_trail)
            
            # Przygotuj parametry wyszukiwania dla raportu
            report_params = {
                'city': city,
                'date': date,
                **search_params
            }
            
            # Dodaj informacje pogodowe do parametrów
            if weather:
                report_params['weather'] = {
                    'temperature': weather.get('temperature_2m_mean', 'N/A'),
                    'precipitation': weather.get('precipitation_sum', 'N/A'),
                    'sunshine': weather.get('sunshine_duration', 'N/A')
                }
            
            # Generuj raport PDF
            print("\nGenerowanie raportu PDF...")
            
            if not output_filename:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"raport_rekomendacji_{city}_{timestamp}.pdf"
            
            pdf_path = self.pdf_generator.generate_pdf_report(
                enhanced_trails,
                report_params,
                output_filename
            )
            
            print(f"✅ Raport PDF został wygenerowany: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"❌ Błąd podczas generowania raportu PDF: {e}")
            return None
    
    def recommend_trails_with_report(
        self,
        city: str,
        date: str,
        difficulty: Optional[int] = None,
        terrain_type: Optional[str] = None,
        min_length: Optional[float] = None,
        max_length: Optional[float] = None,
        min_sunshine: Optional[float] = None,
        max_precipitation: Optional[float] = None,
        min_temperature: Optional[float] = None,
        max_temperature: Optional[float] = None,
        category: Optional[str] = None,
        generate_pdf: bool = False,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rekomenduje trasy i opcjonalnie generuje raport PDF.
        
        Returns:
            Słownik z rekomendowanymi trasami i ścieżką do raportu PDF
        """
        # Standardowe rekomendacje tras
        recommended_trails = self.recommend_trails(
            city, date, difficulty, terrain_type, min_length, max_length,
            min_sunshine, max_precipitation, min_temperature, max_temperature, category
        )
        
        result = {
            'trails': recommended_trails,
            'count': len(recommended_trails),
            'pdf_report': None
        }
        
        # Generuj raport PDF jeśli jest żądany
        if generate_pdf and recommended_trails:
            search_params = {
                'difficulty': difficulty,
                'terrain_type': terrain_type,
                'min_length': min_length,
                'max_length': max_length,
                'min_sunshine': min_sunshine,
                'max_precipitation': max_precipitation,
                'min_temperature': min_temperature,
                'max_temperature': max_temperature,
                'category': category
            }
            
            # Pobierz dane pogodowe dla raportu
            weather = self.data_handler.weather_api.get_weather_forecast(city, date)
            
            pdf_path = self.generate_comprehensive_report(
                city, date, recommended_trails, search_params, weather, output_filename
            )
            
            result['pdf_report'] = pdf_path
        
        return result