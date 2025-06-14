from typing import Dict, Any

class TimeCalculator:
    """
    Klasa do obliczania szacowanego czasu przejścia trasy.
    
    Uwzględnia następujące czynniki:
    - Długość trasy
    - Przewyższenie
    - Typ terenu
    - Trudność szlaku
    - Warunki pogodowe
    
    Bazowa prędkość marszu: 4 km/h
    Modyfikatory:
    - Trudny teren: -1 km/h
    - Duże przewyższenie: -0.5 km/h
    - Złe warunki pogodowe: -0.5 km/h
    """
    
    @staticmethod
    def calculate_time(trail: Dict[str, Any]) -> float:
        """
        Oblicza szacowany czas przejścia trasy w godzinach.
        
        Algorytm:
        1. Ustal bazową prędkość
        2. Zastosuj modyfikatory terenu
        3. Zastosuj modyfikatory trudności
        4. Uwzględnij przewyższenie
        5. Oblicz finalny czas
        
        Args:
            trail: Słownik z danymi trasy zawierający:
                - length_km: długość trasy
                - difficulty: poziom trudności (1-3)
                - terrain_type: typ terenu
                - elevation_m: przewyższenie (opcjonalne)
                
        Returns:
            float: Szacowany czas w godzinach
        """
        # Bazowa prędkość: 4 km/h
        base_speed = 4.0

        # Modyfikatory prędkości bazowej
        terrain_modifiers = {            'górski': -1.0,   # Góry
            'pagórkowaty': -0.5,  # Pagórki
            'leśny': -0.2,    # Las
            'mieszany': -0.3, # Mieszany
            'urban': 0.0,     # Miejski
            'riverside': 0.0  # Nadrzeczny
        }

        # Korekta prędkości ze względu na teren
        terrain_type = trail.get('terrain_type', 'mixed').lower()
        speed = base_speed + terrain_modifiers.get(terrain_type, 0)

        # Korekta ze względu na trudność
        difficulty = trail.get('difficulty', 1)
        if difficulty > 1:
            speed -= (difficulty - 1) * 0.5

        # Korekta ze względu na przewyższenie
        elevation = trail.get('elevation_m', 0)
        if elevation > 500:
            speed -= 0.5
        elif elevation > 1000:
            speed -= 1.0

        # Oblicz czas w godzinach
        length = trail.get('length_km', 0)
        estimated_time = length / max(speed, 1.0)  # Zabezpieczenie przed dzieleniem przez 0

        return round(estimated_time, 2)
