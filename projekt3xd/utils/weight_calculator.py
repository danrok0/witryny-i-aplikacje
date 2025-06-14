from typing import Dict, Any, List

class WeightCalculator:
    """
    Klasa odpowiedzialna za obliczanie wag i ocen dla różnych aspektów tras.
    Implementuje system wag i punktacji opisany w dokumentacji.
    """
    
    def __init__(self):
        """
        Inicjalizacja domyślnych wag dla różnych kryteriów.
        
        Domyślne wagi:
        - Długość trasy: 30%
        - Trudność: 25%
        - Warunki pogodowe: 25%
        - Typ terenu: 20%
        """
        self.default_weights = {
            'length': 0.30,
            'difficulty': 0.25,
            'weather': 0.25,
            'terrain': 0.20
        }
        self.weights = self.default_weights.copy()
    
    def get_weights_from_user(self) -> Dict[str, float]:
        """
        Pobiera i waliduje wagi od użytkownika.
        
        Proces:
        1. Wyświetla aktualne wagi
        2. Pozwala na modyfikację
        3. Normalizuje wagi do sumy 1.0
        4. Waliduje wprowadzone wartości
        
        Returns:
            Dict[str, float]: Znormalizowane wagi
        """
        print("\nAktualne wagi kryteriów:")
        for criterion, weight in self.weights.items():
            print(f"- {criterion}: {weight*100:.0f}%")

        print("\nPodaj nowe wagi (0-100) lub wciśnij ENTER dla wartości domyślnych:")
        
        try:
            # Pobierz wagi z obsługą pustych wartości
            length_input = input("Waga długości trasy: ").strip()
            difficulty_input = input("Waga trudności: ").strip()
            weather_input = input("Waga warunków pogodowych: ").strip()
            terrain_input = input("Waga typu terenu: ").strip()
            
            # Sprawdź czy wszystkie są puste (użytkownik chce domyślne)
            if not any([length_input, difficulty_input, weather_input, terrain_input]):
                print("✅ Użyto domyślnych wag")
                self.weights = self.default_weights.copy()
                return self.weights
            
            # Konwertuj niepuste wartości, użyj domyślnych dla pustych
            if length_input:
                self.weights['length'] = float(length_input) / 100
            if difficulty_input:
                self.weights['difficulty'] = float(difficulty_input) / 100
            if weather_input:
                self.weights['weather'] = float(weather_input) / 100
            if terrain_input:
                self.weights['terrain'] = float(terrain_input) / 100

            # Normalizacja wag
            total = sum(self.weights.values())
            if total > 0:
                for key in self.weights:
                    self.weights[key] /= total
                print("✅ Wagi zostały znormalizowane")
            else:
                print("❌ Suma wag nie może być zero. Użyto domyślnych wag.")
                self.weights = self.default_weights.copy()

        except ValueError as e:
            print(f"❌ Błąd w podanych wartościach: {e}")
            print("✅ Użyto domyślnych wag")
            self.weights = self.default_weights.copy()

        return self.weights
    
    @staticmethod
    def calculate_length_score(length_km: float) -> float:
        """
        Oblicza ocenę dla długości trasy.
        
        System punktacji:
        - Zakres optymalny (5-15 km): 100 punktów
        - Poniżej 5km: -5 punktów za każdy km różnicy
        - Powyżej 15km: -5 punktów za każdy km różnicy
        
        Args:
            length_km: Długość trasy w kilometrach
            
        Returns:
            float: Ocena w zakresie 0-100
        """
        if 5 <= length_km <= 15:
            return 100.0
        elif length_km < 5:
            return max(0, 100 - (5 - length_km) * 5)
        else:
            return max(0, 100 - (length_km - 15) * 5)
            
    @staticmethod
    def calculate_difficulty_score(difficulty: int, elevation_gain: float = 0) -> float:
        """
        Oblicza ocenę dla trudności trasy.
        
        System punktacji:
        - Poziom 1 (łatwy): 100 punktów
        - Poziom 2 (średni): 66.66 punktów
        - Poziom 3 (trudny): 33.33 punktów
        
        Modyfikatory za przewyższenie:
        - >500m: -10 punktów
        - >1000m: -20 punktów
        
        Args:
            difficulty: Poziom trudności (1-3)
            elevation_gain: Przewyższenie w metrach
            
        Returns:
            float: Ocena w zakresie 0-100
        """
        # Bazowa ocena za trudność
        base_score = {
            1: 100.0,
            2: 66.66,
            3: 33.33
        }.get(difficulty, 0.0)
        
        # Modyfikatory za przewyższenie
        if elevation_gain > 1000:
            base_score = max(0, base_score - 20)
        elif elevation_gain > 500:
            base_score = max(0, base_score - 10)
            
        return base_score
        
    @staticmethod
    def calculate_terrain_score(terrain_type: str, attributes: Dict[str, Any]) -> float:
        """
        Oblicza ocenę dla typu terenu.
        
        Punktacja bazowa:
        - Górski: 90 punktów
        - Leśny: 85 punktów
        - Mieszany: 80 punktów
        - Nadrzeczny: 75 punktów
        - Miejski: 70 punktów
        
        Modyfikatory:
        - Punkt widokowy: +10 punktów
        - Atrakcja turystyczna: +5 punktów
        
        Args:
            terrain_type: Typ terenu
            attributes: Słownik z dodatkowymi atrybutami trasy
            
        Returns:
            float: Ocena w zakresie 0-100
        """
        # Bazowa ocena za typ terenu
        base_score = {
            'górski': 90.0,
            'leśny': 85.0,
            'mieszany': 80.0,
            'nadrzeczny': 75.0,
            'miejski': 70.0
        }.get(terrain_type.lower(), 70.0)
        
        # Dodaj punkty za dodatkowe atrybuty
        viewpoints = attributes.get('viewpoints', [])
        attractions = attributes.get('attractions', [])
        
        bonus_points = (len(viewpoints) * 10) + (len(attractions) * 5)
        
        return min(100, base_score + bonus_points)
        
    @staticmethod
    def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """
        Oblicza końcową ważoną ocenę trasy.
        
        Wzór: suma(ocena * waga) dla każdego komponentu
        
        Args:
            scores: Słownik z ocenami poszczególnych komponentów
            weights: Słownik z wagami poszczególnych komponentów
            
        Returns:
            float: Końcowa ważona ocena w zakresie 0-100
        """
        if not scores or not weights:
            return 0.0
            
        weighted_sum = sum(
            scores.get(component, 0) * weights.get(component, 0)
            for component in set(scores.keys()) & set(weights.keys())
        )
        
        total_weight = sum(weights.values())
        
        return round(weighted_sum / total_weight if total_weight > 0 else 0, 2)
    
    def calculate_weighted_score(self, trail: Dict[str, Any], weather: Dict[str, Any]) -> float:
        """
        Oblicza ważony wynik dla trasy na podstawie różnych kryteriów.
        
        Składowe oceny:
        1. Długość (normalizowana do 0-100)
        2. Trudność (przeliczana na skalę 0-100)
        3. Warunki pogodowe (indeks komfortu 0-100)
        4. Typ terenu (ocena dopasowania 0-100)
        
        Args:
            trail: Dane trasy
            weather: Dane pogodowe
            
        Returns:
            float: Ważony wynik w skali 0-100
        """
        # Ocena długości (preferowane 5-15km)
        length = trail.get('length_km', 0)
        if 5 <= length <= 15:
            length_score = 100
        else:
            length_score = max(0, 100 - abs(length - 10) * 5)

        # Ocena trudności (1-3 -> 0-100)
        difficulty = trail.get('difficulty', 1)
        difficulty_score = (4 - difficulty) * 33.33  # 1->100, 2->66.66, 3->33.33

        # Ocena pogody (użyj indeksu komfortu)
        weather_score = weather.get('comfort_index', 50)

        # Ocena terenu
        terrain_scores = {
            'mountain': 90,
            'forest': 85,
            'mixed': 80,
            'urban': 70,
            'riverside': 75
        }
        terrain_score = terrain_scores.get(trail.get('terrain_type', 'mixed'), 70)

        # Oblicz ważony wynik
        weighted_score = (
            self.weights['length'] * length_score +
            self.weights['difficulty'] * difficulty_score +
            self.weights['weather'] * weather_score +
            self.weights['terrain'] * terrain_score
        )

        return round(weighted_score, 2)
    
    def sort_trails_by_weights(self, trails: List[Dict[str, Any]], weather: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sortuje trasy według ich ważonych wyników.
        
        Proces:
        1. Oblicza wynik ważony dla każdej trasy
        2. Dodaje wynik do danych trasy
        3. Sortuje malejąco według wyniku
        
        Args:
            trails: Lista tras do posortowania
            weather: Dane pogodowe
            
        Returns:
            List[Dict[str, Any]]: Posortowane trasy z dodanymi wynikami
        """
        for trail in trails:
            trail['weighted_score'] = self.calculate_weighted_score(trail, weather)
        
        return sorted(trails, key=lambda x: x.get('weighted_score', 0), reverse=True)
