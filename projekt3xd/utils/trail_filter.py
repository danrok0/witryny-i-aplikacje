from typing import List, Dict, Any

class TrailFilter:
    """
    Klasa odpowiedzialna za filtrowanie i kategoryzację szlaków.
    Implementuje algorytmy klasyfikacji tras do różnych kategorii
    oraz filtrowanie według kryteriów użytkownika.
    """
    
    @staticmethod
    def filter_trails(
        trails: List[Dict[str, Any]],
        min_length: float = 0,
        max_length: float = float('inf'),
        difficulty: int = None
    ) -> List[Dict[str, Any]]:
        """
        Filtruje szlaki na podstawie podanych kryteriów.
        
        Args:
            trails: Lista słowników z danymi o szlakach
            min_length: Minimalna długość szlaku w km
            max_length: Maksymalna długość szlaku w km
            difficulty: Wymagany poziom trudności (1-3)
            
        Returns:
            Lista przefiltrowanych szlaków
        """
        filtered = trails

        # Filtrowanie po długości
        filtered = [
            trail for trail in filtered
            if min_length <= trail.get('length_km', 0) <= max_length
        ]

        # Filtrowanie po trudności jeśli określona
        if difficulty is not None:
            filtered = [
                trail for trail in filtered
                if trail.get('difficulty') == difficulty
            ]

        return filtered
    
    @staticmethod
    def classify_family_trail(trail: Dict[str, Any]) -> bool:
        """
        Klasyfikuje trasę jako rodzinną na podstawie systemu punktowego.
        
        Kryteria podstawowe (wszystkie muszą być spełnione):
        - Poziom trudności: 1 (łatwy)
        - Długość: < 5 km
        - Przewyższenie: < 200m
        
        System punktowy (minimum 40 punktów):
        - Znaczniki: leisure (+10), park (+10), playground (+15), family (+15)
        - Nawierzchnia utwardzona: +10
        - Udogodnienia na trasie: +5 za każde
        
        Args:
            trail: Słownik z danymi o trasie
            
        Returns:
            bool: True jeśli trasa spełnia kryteria trasy rodzinnej
        """
        # Sprawdź kryteria podstawowe (wymagane)
        if (trail.get('difficulty', 0) > 1 or 
            trail.get('length_km', 0) >= 5 or
            trail.get('elevation_gain', 0) >= 200):
            return False
            
        # Oblicz punkty za dodatkowe cechy
        points = 0
        
        # Punkty za znaczniki
        tags = trail.get('tags', [])
        if 'leisure' in tags: points += 10
        if 'park' in tags: points += 10
        if 'playground' in tags: points += 15
        if 'family' in tags: points += 15
        
        # Punkty za nawierzchnię
        if trail.get('surface', '') in ['paved', 'asphalt', 'concrete']:
            points += 10
            
        # Punkty za udogodnienia
        amenities = trail.get('amenities', [])
        points += len(amenities) * 5
        
        return points >= 40

    @staticmethod
    def classify_scenic_trail(trail: Dict[str, Any]) -> bool:
        """
        Klasyfikuje trasę jako widokową na podstawie systemu punktowego.
        
        Kryteria podstawowe:
        - Długość: preferowane < 15 km
        - Minimum jeden punkt widokowy
        
        System punktowy (minimum 50 punktów):
        - Każdy punkt widokowy: +20
        - Znaczniki: viewpoint (+15), scenic (+15), tourism (+10), panorama (+20)
        - Wysokość względna > 300m: +10
        - Lokalizacja w górach: +15
        
        Args:
            trail: Słownik z danymi o trasie
            
        Returns:
            bool: True jeśli trasa spełnia kryteria trasy widokowej
        """
        # Sprawdź czy trasa ma punkty widokowe
        if not trail.get('viewpoints', []):
            return False
            
        points = 0
        
        # Punkty za każdy punkt widokowy
        points += len(trail.get('viewpoints', [])) * 20
        
        # Punkty za znaczniki
        tags = trail.get('tags', [])
        if 'viewpoint' in tags: points += 15
        if 'scenic' in tags: points += 15
        if 'tourism' in tags: points += 10
        if 'panorama' in tags: points += 20
        
        # Punkty za wysokość
        if trail.get('elevation_gain', 0) > 300:
            points += 10
            
        # Punkty za lokalizację w górach
        if trail.get('terrain_type', '').lower() == 'górski':
            points += 15
            
        return points >= 50
        
    @staticmethod
    def classify_sport_trail(trail: Dict[str, Any]) -> bool:
        """
        Klasyfikuje trasę jako sportową.
        
        Kryteria (musi spełniać jedno z):
        1. Zestaw standardowy:
           - Długość: 5-15 km
           - Trudność: poziom 2
           - Przewyższenie: 200-800m
           
        2. Zestaw znaczników:
           - Znaczniki: sport, activity, training
           - Długość: > 5 km
        
        Args:
            trail: Słownik z danymi o trasie
            
        Returns:
            bool: True jeśli trasa spełnia kryteria trasy sportowej
        """
        # Kryteria standardowe
        length = trail.get('length_km', 0)
        difficulty = trail.get('difficulty', 0)
        elevation = trail.get('elevation_gain', 0)
        
        # Sprawdź zestaw standardowy
        if (5 <= length <= 15 and difficulty == 2 and 200 <= elevation <= 800):
            return True
        
        # Sprawdź zestaw znaczników
        tags = trail.get('tags', [])
        if ('sport' in tags or 'activity' in tags or 'training' in tags) and length > 5:
            return True
        
        return False
    
    @staticmethod
    def classify_extreme_trail(trail: Dict[str, Any]) -> bool:
        """
        Klasyfikuje trasę jako ekstremalną.
        
        Kryteria (musi spełniać jedno z):
        - Trudność: poziom 3
        - Długość: > 15 km
        - Przewyższenie: > 800m
        - Znaczniki: climbing, alpine, via_ferrata
        
        Args:
            trail: Słownik z danymi o trasie
            
        Returns:
            bool: True jeśli trasa spełnia kryteria trasy ekstremalnej
        """
        # Kryteria trudności
        difficulty = trail.get('difficulty', 0)
        length = trail.get('length_km', 0)
        elevation = trail.get('elevation_gain', 0)
        tags = trail.get('tags', [])
        
        # Sprawdź trudność poziom 3
        if difficulty == 3:
            return True
        
        # Sprawdź długość i przewyższenie
        if length > 15 or elevation > 800:
            return True
        
        # Sprawdź znaczniki
        if ('climbing' in tags or 'alpine' in tags or 'via_ferrata' in tags):
            return True
        
        return False