from typing import List, Dict, Any
from functools import reduce

class WeatherStatistics:
    """Klasa do obliczania statystyk pogodowych."""
    
    @staticmethod
    def calculate_stats(weather_data: List[Dict[str, float]]) -> Dict[str, float]:
        """Oblicza statystyki pogodowe używając funkcji reduce."""
        if not weather_data:
            return {
                "avg_temp": 0.0,
                "total_precipitation": 0.0,
                "sunshine_hours": 0.0
            }

        count = len(weather_data)
        
        # Obliczanie średniej temperatury używając reduce
        total_temp = reduce(lambda acc, x: acc + x['temperature'], weather_data, 0.0)
        avg_temp = total_temp / count

        # Obliczanie całkowitych opadów używając reduce
        total_precipitation = reduce(lambda acc, x: acc + x['precipitation'], weather_data, 0.0)

        # Obliczanie średniej liczby godzin słonecznych używając reduce
        total_sunshine = reduce(lambda acc, x: acc + x['sunshine_hours'], weather_data, 0.0)
        avg_sunshine = total_sunshine / count

        return {
            "avg_temp": round(avg_temp, 2),
            "total_precipitation": round(total_precipitation, 2),
            "sunshine_hours": round(avg_sunshine, 2)
        }
        
    @staticmethod
    def calculate_region_stats(trails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Oblicza statystyki dla szlaków w danym regionie."""
        if not trails:
            return {
                "avg_length": 0.0,
                "avg_difficulty": 0.0,
                "total_trails": 0
            }
            
        count = len(trails)
        total_length = reduce(lambda acc, x: acc + x.get('length_km', 0), trails, 0.0)
        total_difficulty = reduce(lambda acc, x: acc + x.get('difficulty', 0), trails, 0.0)
        
        return {
            "avg_length": round(total_length / count, 2),
            "avg_difficulty": round(total_difficulty / count, 2),
            "total_trails": count
        }