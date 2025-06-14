from typing import Dict, List, Any
import json
import csv
from datetime import datetime

class ResultExporter:
    """
    Klasa odpowiedzialna za eksport wyników rekomendacji do różnych formatów.
    
    Obsługiwane formaty:
    - TXT: Czytelny format tekstowy z pełnymi opisami
    - JSON: Format do dalszego przetwarzania danych
    - CSV: Format tabelaryczny do analizy w arkuszach kalkulacyjnych
    
    Każdy format zawiera:
    - Dane podstawowe szlaku (nazwa, długość, trudność)
    - Dane pogodowe (jeśli dostępne)
    - Obliczone wartości (indeks komfortu, ocena ważona)
    """
    @staticmethod
    def export_results(
        trails_by_city: Dict[str, List[Dict[str, Any]]], 
        date: str,
        weather_by_city: Dict[str, Dict[str, Any]]
    ):
        """
        Eksportuje wyniki rekomendacji do różnych formatów plików.
        
        Args:
            trails_by_city: Słownik z trasami dla każdego miasta {miasto: [trasy]}
            date: Data, dla której generowane są rekomendacje
            weather_by_city: Słownik z danymi pogodowymi dla każdego miasta
        """
        try:
            # Generuj timestamp raz dla wszystkich plików
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Zapisz do TXT
            ResultExporter._save_to_txt(trails_by_city, date, weather_by_city)
            
            # Zapisz do JSON
            ResultExporter._save_to_json(trails_by_city, date, weather_by_city)
            
            # Zapisz do CSV z timestampem
            ResultExporter._save_to_csv(trails_by_city, date, weather_by_city, timestamp)
        except Exception as e:
            print(f"Błąd podczas eksportu wyników: {e}")    @staticmethod
    def _save_to_txt(trails_by_city: Dict[str, List[Dict[str, Any]]], 
                     date: str,
                     weather_by_city: Dict[str, Dict[str, Any]],
                     timestamp: str = None):
        """
        Zapisuje rekomendacje do pliku TXT.
        
        Args:
            trails_by_city: Słownik tras pogrupowanych według miast
            date: Data dla której generowane są rekomendacje
            weather_by_city: Dane pogodowe dla każdego miasta
            timestamp: Opcjonalny znacznik czasowy do nazwy pliku
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recommendations_{timestamp}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== Rekomendacje szlaków na dzień {date} ===\n")
                f.write(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Dla każdego miasta
                for city, trails in trails_by_city.items():
                    f.write(f"=== {city} ===\n")
                    weather = weather_by_city.get(city, {})
                    
                    if weather:
                        f.write("\nDane pogodowe:\n")
                        f.write(f"Temperatura: {weather.get('temperature_min', 'N/A')}°C - {weather.get('temperature_max', 'N/A')}°C\n")
                        f.write(f"Średnia temperatura: {weather.get('temperature_avg', 'N/A')}°C\n")
                        f.write(f"Opady: {weather.get('precipitation', 'N/A')} mm\n")
                        f.write(f"Zachmurzenie: {weather.get('cloud_cover', 'N/A')}%\n")
                        f.write(f"Godziny słoneczne: {weather.get('sunshine_hours', 'N/A')} h\n")
                        f.write(f"Prędkość wiatru: {weather.get('wind_speed', 'N/A')} km/h\n\n")
                    
                    if not trails:
                        f.write("Nie znaleziono tras spełniających kryteria.\n")
                    else:
                        f.write(f"\nZnaleziono {len(trails)} tras:\n")
                        for i, trail in enumerate(trails, 1):
                            f.write(f"\n{i}. {trail['name']}\n")
                            f.write(f"   Miasto: {trail.get('region', city)}\n")
                            f.write(f"   Długość: {trail.get('length_km', 'N/A')} km\n")
                            f.write(f"   Poziom trudności: {trail.get('difficulty', 'N/A')}/3\n")
                            f.write(f"   Typ terenu: {trail.get('terrain_type', 'N/A')}\n")
                            f.write(f"   Kategoria: {trail.get('category', 'nieskategoryzowana').upper()}\n")
                            if 'comfort_index' in trail:
                                f.write(f"   Indeks komfortu: {trail['comfort_index']}/100\n")
                            if 'weighted_score' in trail:
                                f.write(f"   Wynik ważony: {trail['weighted_score']}/100\n")
                            if 'description' in trail:
                                f.write(f"   Opis: {trail['description']}\n")
                            if 'estimated_time' in trail:
                                hours = int(trail['estimated_time'])
                                minutes = int((trail['estimated_time'] - hours) * 60)
                                if hours > 0 and minutes > 0:
                                    f.write(f"   Szacowany czas przejścia: {hours}h {minutes}min\n")
                                elif hours > 0:
                                    f.write(f"   Szacowany czas przejścia: {hours}h\n")
                                else:
                                    f.write(f"   Szacowany czas przejścia: {minutes}min\n")
                    f.write("\n" + "="*50 + "\n")
                
            print(f"\nRekomendacje zostały zapisane do pliku {filename}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania do pliku TXT: {e}")
    @staticmethod
    def _save_to_json(trails_by_city: Dict[str, List[Dict[str, Any]]], 
                     date: str,
                     weather_by_city: Dict[str, Dict[str, Any]],
                     timestamp: str = None):
        """Zapisuje rekomendacje do pliku JSON."""
        try:
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data = {
                "metadata": {
                    "date": date,
                    "generated_at": datetime.now().isoformat()
                },
                "cities": {}
            }
            
            for city in trails_by_city:
                data["cities"][city] = {
                    "weather": weather_by_city.get(city, {}),
                    "trails": trails_by_city[city]
                }
            
            filename = f"recommendations_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f"Rekomendacje zostały zapisane do pliku {filename}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania do pliku JSON: {e}")
    
    @staticmethod
    def _save_to_csv(trails_by_city: Dict[str, List[Dict[str, Any]]], 
                     date: str,
                     weather_by_city: Dict[str, Dict[str, Any]],
                     timestamp: str):
        """Zapisuje rekomendacje do pliku CSV."""
        try:
            filename = f"recommendations_{timestamp}.csv"
            with open(filename, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                
                # Zapisz nagłówki
                headers = ["Miasto", "Nazwa", "Długość (km)", "Trudność", "Typ terenu", 
                          "Kategoria", "Indeks komfortu", "Wynik ważony", "Szacowany czas"]
                writer.writerow(headers)
                
                # Zapisz dane tras dla wszystkich miast
                for city, trails in trails_by_city.items():
                    for trail in trails:
                        row = [
                            city,
                            trail.get('name', ''),
                            trail.get('length_km', ''),
                            f"{trail.get('difficulty', '')}/3",
                            trail.get('terrain_type', ''),
                            trail.get('category', '').upper(),
                            f"{trail.get('comfort_index', '')}/100" if 'comfort_index' in trail else '',
                            f"{trail.get('weighted_score', '')}/100" if 'weighted_score' in trail else '',
                            ResultExporter._format_time(trail.get('estimated_time', 0))
                        ]
                        writer.writerow(row)
                    
            print(f"Rekomendacje zostały zapisane do pliku {filename}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania do pliku CSV: {e}")

    @staticmethod
    def _format_time(time_in_hours: float) -> str:
        """Formatuje czas z godzin na format 'Xh Ymin'."""
        if not time_in_hours:
            return ""
        hours = int(time_in_hours)
        minutes = int((time_in_hours - hours) * 60)
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}min"
