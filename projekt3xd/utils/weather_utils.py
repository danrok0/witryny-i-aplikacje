from typing import Dict, Any, Optional
from datetime import datetime

class WeatherUtils:
    """
    Klasa narzędzi do przetwarzania danych pogodowych.
    
    Główne funkcjonalności:
    - Obliczanie indeksu komfortu dla wędrówek
    - Analiza najlepszych okresów dla różnych typów tras
    - Formatowanie i walidacja danych pogodowych
    - Określanie stanu pogody (słonecznie/deszczowo)
    """

    @staticmethod
    def format_weather_data(weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatuje dane pogodowe do bardziej czytelnej postaci.
        
        Args:
            weather_data: Surowe dane pogodowe z API
            
        Returns:
            Sformatowane dane z obliczonymi średnimi wartościami
        """
        if not weather_data:
            return {}
            
        return {
            'temperatura': {
                'min': round(weather_data.get('temperature_min', 0), 1),
                'max': round(weather_data.get('temperature_max', 0), 1),
                'średnia': round(weather_data.get('temperature', 0), 1)
            },
            'opady': round(weather_data.get('precipitation', 0), 1),
            'zachmurzenie': round(weather_data.get('cloud_cover', 0), 1),
            'godziny_słoneczne': round(weather_data.get('sunshine_hours', 0), 1),
            'prędkość_wiatru': round(weather_data.get('wind_speed', 0), 1)
        }
    
    @staticmethod
    def is_weather_suitable(weather_data: Dict[str, Any], 
                          max_precipitation: float,
                          min_temperature: float,
                          max_temperature: float) -> bool:
        """
        Sprawdza czy warunki pogodowe są odpowiednie dla wycieczki.
        
        Kryteria:
        - Temperatura w zadanym zakresie
        - Opady poniżej maksymalnego progu
        - Odpowiednie zachmurzenie
        """
        if not weather_data:
            return False
            
        avg_temp = weather_data.get('temperature', 0)
        precipitation = weather_data.get('precipitation', 0)
        
        return (min_temperature <= avg_temp <= max_temperature and 
                precipitation <= max_precipitation)
    
    @staticmethod
    def get_weather_summary(weather_data: Dict[str, Any]) -> str:
        """Tworzy podsumowanie warunków pogodowych."""
        if not weather_data:
            return "Brak danych pogodowych"
            
        temp_min = weather_data.get('temperature_min', 0)
        temp_max = weather_data.get('temperature_max', 0)
        precipitation = weather_data.get('precipitation', 0)
        cloud_cover = weather_data.get('cloud_cover', 0)
        sunshine = weather_data.get('sunshine_hours', 0)
        
        return (f"Temperatura: {temp_min:.1f}°C - {temp_max:.1f}°C\n"
                f"Opady: {precipitation:.1f} mm\n"
                f"Zachmurzenie: {cloud_cover:.1f}%\n"
                f"Godziny słoneczne: {sunshine:.1f} h")
    
    @staticmethod
    def get_weather_condition(weather_data: Dict[str, Any]) -> str:
        """Określa ogólny stan pogody."""
        if not weather_data:
            return "nieznany"
            
        precipitation = weather_data.get('precipitation', 0)
        cloud_cover = weather_data.get('cloud_cover', 0)
        sunshine = weather_data.get('sunshine_hours', 0)
        
        if precipitation > 5:
            return "deszczowo"
        elif cloud_cover > 70:
            return "pochmurno"
        elif sunshine > 6:
            return "słonecznie"
        else:
            return "umiarkowanie"
    @staticmethod
    def calculate_hiking_comfort(weather_data: Dict[str, Any]) -> float:
        """
        Oblicza indeks komfortu dla wędrówek (0-100) na podstawie warunków pogodowych.
        
        Algorytm wykorzystuje system wag:
        - Temperatura (40%): optymalna 15-18°C
        - Opady (35%): im mniejsze tym lepiej
        - Zachmurzenie (25%): optymalne 20-40%
        
        Args:
            weather_data: Słownik z danymi pogodowymi zawierający:
                - temperature/temperature_min/temperature_max: temperatura w °C
                - precipitation: opady w mm
                - cloud_cover: zachmurzenie w %
        
        Returns:
            float: Indeks komfortu w skali 0-100
        """
        if not weather_data:
            return 50.0  # Wartość domyślna przy braku danych
            
        try:
            # 1. Obliczanie składowej temperatury (40% wagi końcowej)
            temp_min = weather_data.get('temperature_min')
            temp_max = weather_data.get('temperature_max')

            if temp_min is not None and temp_max is not None:
                temp = (float(temp_min) + float(temp_max)) / 2
            else:
                temp = float(weather_data.get('temperature', 20))
            
            # Obliczanie punktów za temperaturę
            if 15 <= temp <= 18:  # Idealny zakres
                temp_score = 100
            elif temp < 15:  # Za zimno
                temp_score = max(0, 100 - abs(15 - temp) * 15)  # -15 punktów za każdy stopień poniżej
            else:  # Za ciepło
                temp_score = max(0, 100 - abs(temp - 18) * 18)  # -18 punktów za każdy stopień powyżej
            
            # 2. Obliczanie składowej opadów (35% wagi końcowej)
            precip = float(weather_data.get('precipitation', 0))
            precip_score = max(0, 100 - (precip * 40))  # -40 punktów za każdy mm opadów
            
            # 3. Obliczanie składowej zachmurzenia (25% wagi końcowej)
            cloud = float(weather_data.get('cloud_cover', 50))
            if cloud < 20:  # Prawie bezchmurnie (może być za gorąco)
                cloud_score = 80
            elif 20 <= cloud <= 40:  # Idealne zachmurzenie
                cloud_score = 100
            elif cloud < 60:  # Umiarkowane zachmurzenie
                cloud_score = 60
            else:  # Duże zachmurzenie
                cloud_score = max(0, 100 - ((cloud - 60) * 2))  # -2 punkty za każdy % powyżej 60
            
            # Oblicz końcowy wynik (średnia ważona)
            comfort_index = (
                temp_score * 0.4 +    # Temperatura ma największy wpływ
                precip_score * 0.35 + # Opady mają duży wpływ
                cloud_score * 0.25    # Zachmurzenie ma najmniejszy wpływ
            )
            
            return round(comfort_index, 1)
            
        except (ValueError, TypeError) as e:
            print(f"Błąd podczas obliczania indeksu komfortu: {e}")
            return 50.0  # Wartość domyślna w przypadku błędu
    @staticmethod
    def analyze_best_periods(weather_data: Dict[str, Dict[str, Any]], trail_type: str = None) -> Dict[str, Any]:
        """
        Analizuje dane pogodowe aby określić najlepsze okresy dla szlaku.
        
        Analiza uwzględnia:
        - Sezonowość (wiosna, lato, jesień, zima)
        - Typ szlaku (górski, leśny, nizinny)
        - Specjalne wymagania dla różnych typów tras
        - Długoterminowe trendy pogodowe
        
        Args:
            weather_data: Historyczne dane pogodowe
            trail_type: Typ szlaku (górski, leśny, nizinny, miejski)
            
        Returns:
            Dict zawierający:
            - best_dates: Lista dat z najlepszymi warunkami
            - average_comfort: Średni indeks komfortu
            - recommendations: Zalecenia dotyczące najlepszej pory roku
        """
        if not weather_data:
            return {
                "best_dates": [],
                "average_comfort": 0.0,
                "season_scores": {
                    "Wiosna": 0,
                    "Lato": 0,
                    "Jesień": 0,
                    "Zima": 0
                },
                "recommendations": "Brak wystarczających danych pogodowych"
            }

        # Oblicz indeks komfortu dla każdej daty
        comfort_scores = {}
        season_scores = {
            "Wiosna": [],  # Marzec-Maj
            "Lato": [],    # Czerwiec-Sierpień
            "Jesień": [],  # Wrzesień-Listopad
            "Zima": []     # Grudzień-Luty
        }
        
        # Analizuj każdy dzień
        for date_str, conditions in weather_data.items():
            try:
                # Oblicz podstawowy indeks komfortu
                comfort = WeatherUtils.calculate_hiking_comfort(conditions)
                
                # Dodatkowe modyfikatory w zależności od typu szlaku
                if trail_type:
                    if trail_type == 'górski':
                        # Kara za silny wiatr dla szlaków górskich
                        wind_penalty = max(0, (conditions.get('wind_speed', 0) - 15) * 2)
                        comfort = max(0, comfort - wind_penalty)
                    elif trail_type == 'leśny':
                        # Bonus dla szlaków leśnych (mniejszy wpływ zachmurzenia)
                        comfort = min(100, comfort + 10)

                comfort_scores[date_str] = comfort
                
                # Przypisz wynik do odpowiedniej pory roku
                date = datetime.strptime(date_str, "%Y-%m-%d")
                month = date.month
                
                if 3 <= month <= 5:
                    season_scores["Wiosna"].append(comfort)
                elif 6 <= month <= 8:
                    season_scores["Lato"].append(comfort)
                elif 9 <= month <= 11:
                    season_scores["Jesień"].append(comfort)
                else:
                    season_scores["Zima"].append(comfort)
                    
            except (ValueError, KeyError):
                continue

        # Znajdź najlepsze daty (z komfortem > 70)
        best_dates = sorted([
            (date, score) for date, score in comfort_scores.items()
            if score > 70
        ], key=lambda x: x[1], reverse=True)

        # Oblicz średnie dla sezonów
        season_averages = {}
        for season, scores in season_scores.items():
            season_averages[season] = round(sum(scores) / len(scores)) if scores else 0

        # Znajdź najlepszą porę roku
        best_season = max(season_averages.items(), key=lambda x: x[1])[0]
        
        # Przygotuj rekomendacje
        recommendations = []
        recommendations.append(f"Najlepsza pora roku: {best_season}")
        
        # Dodaj rekomendacje dla typu szlaku
        if trail_type == "górski":
            if best_season in ["Wiosna", "Jesień"]:
                recommendations.append("Idealne warunki dla tego typu trasy")
            elif best_season == "Lato":
                recommendations.append("Możliwe upały, zalecana wczesna pora dnia")
            else:
                recommendations.append("W zimie wymagane dodatkowe przygotowanie")
        elif trail_type in ["leśny", "nizinny"]:
            if best_season in ["Wiosna", "Lato"]:
                recommendations.append("Świetne warunki do wędrówek")
            else:
                recommendations.append("Sprawdź prognozę opadów przed wycieczką")

        # Oblicz średni komfort dla wszystkich dat
        avg_comfort = sum(comfort_scores.values()) / len(comfort_scores) if comfort_scores else 0

        # Dodaj ogólne zalecenia
        if avg_comfort < 50:
            recommendations.append("Zalecana duża ostrożność przy planowaniu wycieczki")
        elif avg_comfort > 70:
            recommendations.append("Bardzo dobre warunki przez większość czasu")

        return {
            "best_dates": [date for date, _ in best_dates[:5]],  # Top 5 najlepszych dat
            "average_comfort": round(avg_comfort, 2),
            "season_scores": season_averages,
            "recommendations": " | ".join(recommendations)
        }