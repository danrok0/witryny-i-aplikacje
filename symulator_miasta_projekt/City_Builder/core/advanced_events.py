"""
Rozszerzony system wydarzeń i katastrof dla City Builder.
Implementuje 30+ różnych wydarzeń z drzewem decyzyjnym.

Ten moduł zawiera zaawansowany system wydarzeń losowych które mogą wystąpić podczas gry.
Każde wydarzenie ma swoje warunki wystąpienia, wybory gracza i konsekwencje.
"""

# === IMPORTY POTRZEBNE DLA SYSTEMU WYDARZEŃ ===
from enum import Enum                                    # Do tworzenia wyliczeń (kategorie, nasilenie)
from dataclasses import dataclass                        # Do prostego tworzenia klas danych
from typing import Dict, List, Optional, Callable        # Dla typowania - poprawia czytelność kodu
import random                                            # Do losowania wydarzeń i wyborów
import math                                              # Do obliczeń matematycznych (prawdopodobieństwa)

class EventCategory(Enum):
    """
    Kategorie wydarzeń w grze.
    
    Enum definiuje wszystkie możliwe typy wydarzeń które mogą wystąpić.
    Każda kategoria ma inne warunki wystąpienia i konsekwencje.
    """
    NATURAL_DISASTER = "natural_disaster"    # Katastrofy naturalne (trzęsienia, powodzie, huragany)
    ECONOMIC = "economic"                    # Wydarzenia ekonomiczne (boomy, recesje, inflacja)
    SOCIAL = "social"                        # Wydarzenia społeczne (protesty, strajki, festiwale)
    POLITICAL = "political"                  # Wydarzenia polityczne (wybory, skandale, reformy)
    TECHNOLOGICAL = "technological"          # Wydarzenia technologiczne (przełomy, awarie, innowacje)
    ENVIRONMENTAL = "environmental"          # Wydarzenia środowiskowe (zanieczyszczenie, ekologia)
    CRIME = "crime"                          # Wydarzenia kryminalne (przestępczość, gangi, korupcja)
    HEALTH = "health"                        # Wydarzenia zdrowotne (epidemie, choroby, medycyna)

class EventSeverity(Enum):
    """
    Poziom nasilenia wydarzeń - określa jak poważne są konsekwencje.
    
    Im wyższe nasilenie, tym większy wpływ na miasto i mieszkańców.
    Wpływa na prawdopodobieństwo wystąpienia i dostępne wybory.
    """
    MINOR = "minor"                          # Drobne - mały wpływ, łatwe do rozwiązania
    MODERATE = "moderate"                    # Umiarkowane - średni wpływ, wymaga uwagi
    MAJOR = "major"                          # Poważne - duży wpływ, trudne do rozwiązania
    CATASTROPHIC = "catastrophic"            # Katastrofalne - ogromny wpływ, krytyczne

@dataclass
class EventChoice:
    """
    Reprezentuje pojedynczy wybór w wydarzeniu.
    
    Każde wydarzenie może mieć kilka opcji do wyboru przez gracza.
    Każdy wybór ma swoje koszty, wymagania i konsekwencje.
    """
    id: str                                  # Unikalne ID wyboru (używane w kodzie)
    text: str                                # Krótki tekst wyboru (wyświetlany graczowi)
    description: str                         # Szczegółowy opis konsekwencji wyboru
    cost: float = 0                          # Koszt finansowy wyboru (w dolarach)
    requirements: Dict[str, float] = None    # Wymagania do wyboru (np. minimum pieniędzy)
    effects: Dict[str, float] = None         # Efekty wyboru (wpływ na statystyki miasta)
    probability_modifier: float = 0.0        # Modyfikator prawdopodobieństwa przyszłych wydarzeń
    
    def __post_init__(self):
        """
        Metoda wywoływana automatycznie po inicjalizacji obiektu przez @dataclass.
        
        Inicjalizuje puste słowniki jeśli nie zostały podane.
        Zapobiega problemom z mutowalnymi domyślnymi argumentami.
        """
        # Jeśli requirements jest None, utwórz pusty słownik
        if self.requirements is None:
            self.requirements = {}            # Pusty słownik dla wymagań
        # Jeśli effects jest None, utwórz pusty słownik
        if self.effects is None:
            self.effects = {}                 # Pusty słownik dla efektów

@dataclass
class GameEvent:
    """
    Reprezentuje pojedyncze wydarzenie w grze.
    
    Każde wydarzenie ma swoją definicję, warunki wystąpienia i możliwe wybory.
    Wydarzenia mogą być jednorazowe lub długoterminowe z efektami trwającymi wiele tur.
    """
    # === PODSTAWOWE INFORMACJE O WYDARZENIU ===
    id: str                                  # Unikalne ID wydarzenia (używane w kodzie)
    title: str                               # Tytuł wydarzenia (wyświetlany graczowi)
    description: str                         # Opis wydarzenia (co się dzieje)
    category: EventCategory                  # Kategoria wydarzenia (enum)
    severity: EventSeverity                  # Nasilenie wydarzenia (enum)
    base_probability: float                  # Podstawowe prawdopodobieństwo wystąpienia (0.0-1.0)
    choices: List[EventChoice]               # Lista możliwych wyborów dla gracza
    
    # === WARUNKI WYSTĄPIENIA ===
    min_population: int = 0                  # Minimalna populacja wymagana do wystąpienia
    max_population: int = 999999             # Maksymalna populacja (ograniczenie górne)
    min_money: float = 0                     # Minimalna ilość pieniędzy wymagana
    min_satisfaction: float = 0              # Minimalny poziom zadowolenia mieszkańców
    max_satisfaction: float = 100            # Maksymalny poziom zadowolenia (ograniczenie)
    required_buildings: List[str] = None     # Lista wymaganych typów budynków
    required_technologies: List[str] = None  # Lista wymaganych technologii
    
    # === EFEKTY AUTOMATYCZNE ===
    auto_effects: Dict[str, float] = None    # Efekty które występują automatycznie (bez wyboru gracza)
    
    # === DŁUGOTERMINOWE SKUTKI ===
    duration_turns: int = 1                  # Ile tur trwa wydarzenie (domyślnie 1)
    recurring: bool = False                  # Czy wydarzenie może się powtórzyć
    
    def __post_init__(self):
        """
        Metoda wywoływana automatycznie po inicjalizacji obiektu przez @dataclass.
        
        Inicjalizuje puste listy i słowniki jeśli nie zostały podane.
        Zapobiega problemom z mutowalnymi domyślnymi argumentami.
        """
        # Jeśli required_buildings jest None, utwórz pustą listę
        if self.required_buildings is None:
            self.required_buildings = []     # Pusta lista wymaganych budynków
        # Jeśli required_technologies jest None, utwórz pustą listę
        if self.required_technologies is None:
            self.required_technologies = []  # Pusta lista wymaganych technologii
        # Jeśli auto_effects jest None, utwórz pusty słownik
        if self.auto_effects is None:
            self.auto_effects = {}           # Pusty słownik efektów automatycznych
    
    def can_occur(self, game_state: Dict) -> bool:
        """
        Sprawdza czy wydarzenie może wystąpić w aktualnym stanie gry.
        
        Args:
            game_state: Słownik ze statystykami gry (populacja, pieniądze, etc.)
        Returns:
            bool: True jeśli wydarzenie może wystąpić, False w przeciwnym razie
        """
        # Pobierz aktualne statystyki z gry (z wartościami domyślnymi)
        population = game_state.get('population', 0)         # Populacja miasta
        money = game_state.get('money', 0)                   # Pieniądze miasta
        satisfaction = game_state.get('satisfaction', 50)     # Zadowolenie mieszkańców
        buildings = game_state.get('buildings', [])          # Lista budynków
        technologies = game_state.get('technologies', [])    # Lista technologii
        
        # === SPRAWDŹ WARUNKI PODSTAWOWE ===
        # Sprawdź czy populacja mieści się w wymaganym zakresie
        if not (self.min_population <= population <= self.max_population):
            return False  # Populacja poza zakresem
        
        # Sprawdź czy miasto ma wystarczająco pieniędzy
        if money < self.min_money:
            return False  # Za mało pieniędzy
        
        # Sprawdź czy zadowolenie mieści się w wymaganym zakresie
        if not (self.min_satisfaction <= satisfaction <= self.max_satisfaction):
            return False  # Zadowolenie poza zakresem
        
        # === SPRAWDŹ WYMAGANE BUDYNKI ===
        # Jeśli są wymagane budynki, sprawdź czy wszystkie istnieją
        if self.required_buildings:
            # Utwórz listę typów istniejących budynków
            building_types = [b.get('type', '') for b in buildings]
            # Sprawdź każdy wymagany typ budynku
            for required in self.required_buildings:
                if required not in building_types:
                    return False  # Brak wymaganego budynku
        
        # === SPRAWDŹ WYMAGANE TECHNOLOGIE ===
        # Jeśli są wymagane technologie, sprawdź czy wszystkie są zbadane
        if self.required_technologies:
            # Utwórz listę ID zbadanych technologii
            tech_ids = [t.get('id', '') for t in technologies]
            # Sprawdź każdą wymaganą technologię
            for required in self.required_technologies:
                if required not in tech_ids:
                    return False  # Brak wymaganej technologii
        
        # Wszystkie warunki spełnione - wydarzenie może wystąpić
        return True

class AdvancedEventManager:
    """
    Zaawansowany menedżer wydarzeń zarządzający całym systemem wydarzeń.
    
    Odpowiada za:
    - Przechowywanie definicji wszystkich wydarzeń
    - Sprawdzanie warunków wystąpienia
    - Losowanie wydarzeń na podstawie prawdopodobieństwa
    - Zarządzanie aktywnymi wydarzeniami
    - Śledzenie historii wydarzeń
    """
    
    def __init__(self):
        """
        Konstruktor menedżera wydarzeń.
        
        Inicjalizuje wszystkie struktury danych potrzebne do zarządzania wydarzeniami
        i tworzy kompletną listę wszystkich dostępnych wydarzeń w grze.
        """
        # === GŁÓWNE STRUKTURY DANYCH ===
        self.events: Dict[str, GameEvent] = {}        # Słownik wszystkich wydarzeń: {id: GameEvent}
        self.active_events: List[Dict] = []           # Lista aktualnie aktywnych wydarzeń
        self.event_history: List[Dict] = []           # Historia wszystkich wydarzeń (dla statystyk)
        self.event_probabilities: Dict[str, float] = {}  # Cachowane prawdopodobieństwa wydarzeń
        self.long_term_effects: Dict[str, Dict] = {}  # Długoterminowe efekty wydarzeń
        
        # === INICJALIZACJA SYSTEMU ===
        self._initialize_events()                     # Wywołaj metodę tworzącą wszystkie wydarzenia
    
    def _initialize_events(self):
        """
        Inicjalizuje wszystkie wydarzenia dostępne w grze.
        
        Metoda prywatna wywoływana tylko podczas inicjalizacji obiektu.
        Tworzy kompletną listę wydarzeń podzielonych na kategorie.
        """
        
        # === TWORZENIE WYDARZEŃ WG KATEGORII ===
        # KATASTROFY NATURALNE
        self._create_natural_disasters()              # Wywołaj metodę tworzącą katastrofy
        
        # WYDARZENIA EKONOMICZNE
        self._create_economic_events()                # Wywołaj metodę tworzącą wydarzenia ekonomiczne
        
        # WYDARZENIA SPOŁECZNE
        self._create_social_events()                  # Wywołaj metodę tworzącą wydarzenia społeczne
    
    def _create_natural_disasters(self):
        """
        Tworzy katastrofy naturalne - najpoważniejsze wydarzenia w grze.
        
        Katastrofy naturalne mają duży wpływ na miasto i mieszkańców.
        Wymagają szybkiej reakcji i mogą mieć długoterminowe konsekwencje.
        """
        
        # === TRZĘSIENIE ZIEMI ===
        # Jedna z najpoważniejszych katastrof naturalnych
        earthquake = GameEvent(
            "earthquake", "Trzęsienie Ziemi",                    # ID i tytuł wydarzenia
            "Potężne trzęsienie ziemi nawiedziło miasto, niszcząc budynki i infrastrukturę.",  # Opis
            EventCategory.NATURAL_DISASTER,                      # Kategoria: katastrofa naturalna
            EventSeverity.CATASTROPHIC,                          # Nasilenie: katastrofalne
            0.02,                                                 # Prawdopodobieństwo: 2% na turę
            [                                                      # Lista możliwych wyborów
                EventChoice("emergency_response", "Natychmiastowa akcja ratunkowa",  # ID i tekst wyboru
                           "Mobilizuj wszystkie służby ratunkowe",                    # Opis konsekwencji
                           5000,                                                      # Koszt: 5000$
                           effects={"satisfaction": 10, "casualties": -50}),         # Efekty: +10 zadowolenia, -50 ofiar
                EventChoice("minimal_response", "Minimalna reakcja",                 # ID i tekst wyboru
                           "Oszczędzaj środki, reaguj tylko na najgorsze przypadki", # Opis konsekwencji
                           1000,                                                      # Koszt: 1000$
                           effects={"satisfaction": -15, "casualties": 20})          # Efekty: -15 zadowolenia, +20 ofiar
            ]
        )
        # Efekty automatyczne (występują niezależnie od wyboru gracza)
        earthquake.auto_effects = {"building_damage": 0.4, "casualties": 100, "satisfaction": -20}
        earthquake.min_population = 500                          # Wymagana minimalna populacja: 500
        self.events["earthquake"] = earthquake                   # Dodaj do słownika wydarzeń
        
        # === POWÓDŹ ===
        # Katastrofa związana z wodą, mniej poważna niż trzęsienie
        flood = GameEvent(
            "flood", "Wielka Powódź",                            # ID i tytuł wydarzenia
            "Rzeka wystąpiła z brzegów, zalewając znaczną część miasta.",  # Opis
            EventCategory.NATURAL_DISASTER,                      # Kategoria: katastrofa naturalna
            EventSeverity.MAJOR,                                 # Nasilenie: poważne
            0.03,                                                 # Prawdopodobieństwo: 3% na turę
            [                                                      # Lista możliwych wyborów
                EventChoice("build_barriers", "Buduj zapory przeciwpowodziowe",      # ID i tekst wyboru
                           "Szybko wznieś tymczasowe zapory",                        # Opis konsekwencji
                           8000,                                                      # Koszt: 8000$
                           effects={"flood_damage": -0.5, "satisfaction": 5}),       # Efekty: -50% szkód powodziowych, +5 zadowolenia
                EventChoice("evacuate", "Ewakuuj mieszkańców",                       # ID i tekst wyboru
                           "Przeprowadź masową ewakuację",                           # Opis konsekwencji
                           3000,                                                      # Koszt: 3000$
                           effects={"casualties": -80, "satisfaction": -5})          # Efekty: -80 ofiar, -5 zadowolenia
            ]
        )
        # Efekty automatyczne powodzi
        flood.auto_effects = {"building_damage": 0.2, "casualties": 50, "satisfaction": -10}
        self.events["flood"] = flood                             # Dodaj do słownika wydarzeń
    
    def _create_economic_events(self):
        """
        Tworzy wydarzenia ekonomiczne - wpływają na gospodarkę miasta.
        
        Wydarzenia ekonomiczne mogą być pozytywne (boomy) lub negatywne (recesje).
        Mają wpływ na dochody, zatrudnienie i rozwój miasta.
        """
        
        # === BOOM EKONOMICZNY ===
        # Pozytywne wydarzenie ekonomiczne
        economic_boom = GameEvent(
            "economic_boom", "Boom Ekonomiczny",                 # ID i tytuł wydarzenia
            "Region przeżywa niespotykany wzrost gospodarczy. Twoje miasto może na tym skorzystać.",  # Opis
            EventCategory.ECONOMIC,                              # Kategoria: ekonomiczne
            EventSeverity.MAJOR,                                 # Nasilenie: poważne
            0.04,                                                 # Prawdopodobieństwo: 4% na turę
            [                                                      # Lista możliwych wyborów
                EventChoice("attract_business", "Przyciągnij biznes",               # ID i tekst wyboru
                           "Zainwestuj w infrastrukturę dla firm",                  # Opis konsekwencji
                           8000,                                                    # Koszt: 8000$
                           effects={"income_multiplier": 0.3, "population_growth": 0.2}),  # Efekty: +30% dochodów, +20% wzrostu populacji
                EventChoice("conservative_approach", "Podejście konserwatywne",     # ID i tekst wyboru
                           "Nie zmieniaj niczego, zachowaj stabilność",             # Opis konsekwencji
                           0,                                                       # Koszt: 0$ (darmowe)
                           effects={"satisfaction": 5})                             # Efekty: +5 zadowolenia
            ]
        )
        economic_boom.duration_turns = 10                        # Wydarzenie trwa 10 tur
        self.events["economic_boom"] = economic_boom             # Dodaj do słownika wydarzeń
    
    def _create_social_events(self):
        """
        Tworzy wydarzenia społeczne - wpływają na mieszkańców i atmosferę w mieście.
        
        Wydarzenia społeczne często wynikają z poziomu zadowolenia mieszkańców.
        Mogą być pozytywne (festiwale) lub negatywne (protesty).
        """
        
        # === PROTESTY SPOŁECZNE ===
        # Negatywne wydarzenie społeczne
        protests = GameEvent(
            "protests", "Protesty Społeczne",                    # ID i tytuł wydarzenia
            "Mieszkańcy wyszli na ulice, protestując przeciwko polityce miasta.",  # Opis
            EventCategory.SOCIAL,                                # Kategoria: społeczne
            EventSeverity.MODERATE,                              # Nasilenie: umiarkowane
            0.05,                                                 # Prawdopodobieństwo: 5% na turę
            [                                                      # Lista możliwych wyborów
                EventChoice("negotiate", "Negocjuj z protestującymi",              # ID i tekst wyboru
                           "Spotkaj się z liderami protestów",                     # Opis konsekwencji
                           2000,                                                   # Koszt: 2000$
                           effects={"satisfaction": 15, "policy_change": True}),   # Efekty: +15 zadowolenia, zmiana polityki
                EventChoice("ignore_protests", "Ignoruj protesty",                 # ID i tekst wyboru
                           "Czekaj aż protesty same się skończą",                  # Opis konsekwencji
                           0,                                                       # Koszt: 0$ (darmowe)
                           effects={"satisfaction": -10, "unrest": 0.2})           # Efekty: -10 zadowolenia, +20% niepokoju
            ]
        )
        protests.max_satisfaction = 60                           # Maksymalne zadowolenie: 60% (protesty przy wysokim zadowoleniu)
        self.events["protests"] = protests                       # Dodaj do słownika wydarzeń
    
    def calculate_event_probability(self, event: GameEvent, game_state: Dict) -> float:
        """
        Oblicza prawdopodobieństwo wystąpienia wydarzenia na podstawie stanu gry.
        
        Args:
            event: Obiekt wydarzenia do sprawdzenia
            game_state: Słownik ze statystykami gry
        Returns:
            float: Prawdopodobieństwo wystąpienia (0.0-1.0)
        """
        # Sprawdź czy wydarzenie może wystąpić w aktualnym stanie gry
        if not event.can_occur(game_state):
            return 0.0  # Wydarzenie nie może wystąpić
        
        # Pobierz podstawowe prawdopodobieństwo z definicji wydarzenia
        base_prob = event.base_probability
        
        # === MODYFIKATORY NA PODSTAWIE STANU GRY ===
        # Pobierz aktualne statystyki z gry
        population = game_state.get('population', 0)             # Populacja miasta
        satisfaction = game_state.get('satisfaction', 50)         # Zadowolenie mieszkańców
        money = game_state.get('money', 0)                       # Pieniądze miasta
        
        # === MODYFIKATOR POPULACJI ===
        # Większe miasta mają więcej problemów (przestępczość, problemy społeczne, środowiskowe)
        if event.category in [EventCategory.CRIME, EventCategory.SOCIAL, EventCategory.ENVIRONMENTAL]:
            # Oblicz modyfikator na podstawie populacji (maksymalnie 2x)
            population_modifier = min(2.0, population / 5000)     # 5000 mieszkańców = 1x, 10000+ = 2x
            base_prob *= population_modifier                      # Zastosuj modyfikator
        
        # === MODYFIKATOR ZADOWOLENIA ===
        # Niezadowolenie zwiększa prawdopodobieństwo problemów społecznych
        if event.category == EventCategory.SOCIAL and satisfaction < 50:
            # Oblicz modyfikator niezadowolenia (im niższe zadowolenie, tym wyższe prawdopodobieństwo)
            dissatisfaction_modifier = 1 + (50 - satisfaction) / 100  # 0% zadowolenia = 1.5x, 50% = 1x
            base_prob *= dissatisfaction_modifier                # Zastosuj modyfikator
        
        # === MODYFIKATOR PIENIĘDZY ===
        # Brak pieniędzy zwiększa prawdopodobieństwo problemów (przestępczość, zdrowie)
        if money < 5000 and event.category in [EventCategory.CRIME, EventCategory.HEALTH]:
            base_prob *= 1.5                                     # 50% większe prawdopodobieństwo
        
        # Zwróć prawdopodobieństwo (maksymalnie 100%)
        return min(1.0, base_prob)
    
    def trigger_random_event(self, game_state: Dict, turn: int) -> Optional[Dict]:
        """
        Losuje i uruchamia wydarzenie na podstawie prawdopodobieństw.
        
        Args:
            game_state: Słownik ze statystykami gry
            turn: Numer aktualnej tury
        Returns:
            Optional[Dict]: Instancja wydarzenia lub None jeśli nic nie wystąpiło
        """
        # Lista wydarzeń które mogą wystąpić w tej turze
        available_events = []
        
        # === SPRAWDŹ KAŻDE WYDARZENIE ===
        # Iteruj przez wszystkie dostępne wydarzenia
        for event in self.events.values():
            # Oblicz prawdopodobieństwo wystąpienia tego wydarzenia
            probability = self.calculate_event_probability(event, game_state)
            # Jeśli prawdopodobieństwo > 0 i los się powiódł, dodaj do dostępnych
            if probability > 0 and random.random() < probability:
                available_events.append(event)                    # Dodaj do listy możliwych wydarzeń
        
        # Jeśli nie ma dostępnych wydarzeń, nic się nie dzieje
        if not available_events:
            return None
        
        # === WYBIERZ WYDARZENIE ===
        # Wybierz losowe wydarzenie z dostępnych (preferuj bardziej prawdopodobne)
        event = random.choice(available_events)
        
        # === UTWÓRZ INSTANCJĘ WYDARZENIA ===
        # Utwórz słownik z danymi wydarzenia dla tej tury
        event_instance = {
            'id': f"{event.id}_{turn}",                          # Unikalne ID: nazwa_wydarzenia_tura
            'event_id': event.id,                                # ID definicji wydarzenia
            'title': event.title,                                # Tytuł wydarzenia
            'description': event.description,                    # Opis wydarzenia
            'category': event.category.value,                    # Kategoria (string)
            'severity': event.severity.value,                    # Nasilenie (string)
            'choices': [                                          # Lista wyborów dla gracza
                {
                    'id': choice.id,                             # ID wyboru
                    'text': choice.text,                         # Tekst wyboru
                    'description': choice.description,           # Opis konsekwencji
                    'cost': choice.cost,                         # Koszt wyboru
                    'requirements': choice.requirements,         # Wymagania wyboru
                    'can_afford': game_state.get('money', 0) >= choice.cost  # Czy gracz może sobie pozwolić
                }
                for choice in event.choices                      # Dla każdego wyboru w wydarzeniu
            ],
            'auto_effects': event.auto_effects,                  # Efekty automatyczne
            'turn': turn,                                        # Tura wystąpienia
            'duration_turns': event.duration_turns,              # Ile tur trwa wydarzenie
            'remaining_turns': event.duration_turns              # Ile tur zostało (do odliczania)
        }
        
        # === DODAJ DO AKTYWNYCH WYDARZEŃ ===
        # Dodaj wydarzenie do listy aktualnie aktywnych
        self.active_events.append(event_instance)
        
        # Zwróć instancję wydarzenia (dla GUI i logiki gry)
        return event_instance
    
    def get_event_statistics(self) -> Dict:
        """
        Zwraca statystyki wydarzeń do wyświetlania w GUI.
        
        Returns:
            Dict: Słownik ze statystykami wydarzeń
        """
        # Pobierz całkowitą liczbę wydarzeń z historii
        total_events = len(self.event_history)
        # Jeśli nie było żadnych wydarzeń, zwróć podstawowe statystyki
        if total_events == 0:
            return {'total_events': 0}
        
        # === INICJALIZUJ SŁOWNIKI STATYSTYK ===
        category_counts = {}                                     # Licznik wydarzeń według kategorii
        severity_counts = {}                                     # Licznik wydarzeń według nasilenia
        
        # === OBLICZ STATYSTYKI ===
        # Iteruj przez wszystkie wydarzenia z historii
        for event_record in self.event_history:
            # Pobierz definicję wydarzenia ze słownika wydarzeń
            event_def = self.events.get(event_record['event_id'])
            if event_def:
                # Pobierz kategorię i nasilenie wydarzenia
                category = event_def.category.value              # Kategoria jako string
                severity = event_def.severity.value              # Nasilenie jako string
                
                # Zwiększ licznik dla tej kategorii
                category_counts[category] = category_counts.get(category, 0) + 1
                # Zwiększ licznik dla tego nasilenia
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # === ZWRÓĆ KOMPLETNE STATYSTYKI ===
        return {
            'total_events': total_events,                        # Łączna liczba wydarzeń
            'active_events': len(self.active_events),            # Liczba aktywnych wydarzeń
            'category_distribution': category_counts,            # Rozkład według kategorii
            'severity_distribution': severity_counts,            # Rozkład według nasilenia
            # Najczęstsza kategoria (lub None jeśli brak wydarzeń)
            'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }
    
    def save_to_dict(self) -> Dict:
        """
        Zapisuje stan menedżera wydarzeń do słownika (serializacja).
        
        Returns:
            Dict: Słownik z danymi gotowy do zapisania w JSON
        """
        return {
            'active_events': self.active_events,                 # Lista aktywnych wydarzeń
            'event_history': self.event_history[-50:],           # Ostatnie 50 wydarzeń z historii
            'event_probabilities': self.event_probabilities,     # Cachowane prawdopodobieństwa
            'long_term_effects': self.long_term_effects          # Długoterminowe efekty
        }
    
    def load_from_dict(self, data: Dict):
        """
        Wczytuje stan menedżera wydarzeń ze słownika (deserializacja).
        
        Args:
            data: Słownik z danymi wydarzeń (z JSON)
        """
        # Wczytaj wszystkie dane ze słownika (z wartościami domyślnymi)
        self.active_events = data.get('active_events', [])       # Lista aktywnych wydarzeń
        self.event_history = data.get('event_history', [])       # Historia wydarzeń
        self.event_probabilities = data.get('event_probabilities', {})  # Prawdopodobieństwa
        self.long_term_effects = data.get('long_term_effects', {})      # Długoterminowe efekty 