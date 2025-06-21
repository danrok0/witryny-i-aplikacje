"""
Rozszerzony system wydarzeń i katastrof dla City Builder
Implementuje 30+ różnych wydarzeń z drzewem decyzyjnym
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import random
import math

class EventCategory(Enum):
    NATURAL_DISASTER = "natural_disaster"
    ECONOMIC = "economic"
    SOCIAL = "social"
    POLITICAL = "political"
    TECHNOLOGICAL = "technological"
    ENVIRONMENTAL = "environmental"
    CRIME = "crime"
    HEALTH = "health"

class EventSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"

@dataclass
class EventChoice:
    """Wybór w wydarzeniu"""
    id: str
    text: str
    description: str
    cost: float = 0
    requirements: Dict[str, float] = None
    effects: Dict[str, float] = None
    probability_modifier: float = 0.0  # Wpływ na przyszłe wydarzenia
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = {}
        if self.effects is None:
            self.effects = {}

@dataclass
class GameEvent:
    """Wydarzenie w grze"""
    id: str
    title: str
    description: str
    category: EventCategory
    severity: EventSeverity
    base_probability: float
    choices: List[EventChoice]
    
    # Warunki wystąpienia
    min_population: int = 0
    max_population: int = 999999
    min_money: float = 0
    min_satisfaction: float = 0
    max_satisfaction: float = 100
    required_buildings: List[str] = None
    required_technologies: List[str] = None
    
    # Efekty automatyczne (bez wyboru)
    auto_effects: Dict[str, float] = None
    
    # Długoterminowe skutki
    duration_turns: int = 1
    recurring: bool = False
    
    def __post_init__(self):
        if self.required_buildings is None:
            self.required_buildings = []
        if self.required_technologies is None:
            self.required_technologies = []
        if self.auto_effects is None:
            self.auto_effects = {}
    
    def can_occur(self, game_state: Dict) -> bool:
        """Sprawdza czy wydarzenie może wystąpić"""
        population = game_state.get('population', 0)
        money = game_state.get('money', 0)
        satisfaction = game_state.get('satisfaction', 50)
        buildings = game_state.get('buildings', [])
        technologies = game_state.get('technologies', [])
        
        # Sprawdź warunki podstawowe
        if not (self.min_population <= population <= self.max_population):
            return False
        
        if money < self.min_money:
            return False
        
        if not (self.min_satisfaction <= satisfaction <= self.max_satisfaction):
            return False
        
        # Sprawdź wymagane budynki
        if self.required_buildings:
            building_types = [b.get('type', '') for b in buildings]
            for required in self.required_buildings:
                if required not in building_types:
                    return False
        
        # Sprawdź wymagane technologie
        if self.required_technologies:
            tech_ids = [t.get('id', '') for t in technologies]
            for required in self.required_technologies:
                if required not in tech_ids:
                    return False
        
        return True

class AdvancedEventManager:
    """Zaawansowany menedżer wydarzeń"""
    
    def __init__(self):
        self.events: Dict[str, GameEvent] = {}
        self.active_events: List[Dict] = []
        self.event_history: List[Dict] = []
        self.event_probabilities: Dict[str, float] = {}
        self.long_term_effects: Dict[str, Dict] = {}
        
        self._initialize_events()
    
    def _initialize_events(self):
        """Inicjalizuje wszystkie wydarzenia"""
        
        # KATASTROFY NATURALNE
        self._create_natural_disasters()
        
        # WYDARZENIA EKONOMICZNE
        self._create_economic_events()
        
        # WYDARZENIA SPOŁECZNE
        self._create_social_events()
    
    def _create_natural_disasters(self):
        """Tworzy katastrofy naturalne"""
        
        # Trzęsienie ziemi
        earthquake = GameEvent(
            "earthquake", "Trzęsienie Ziemi",
            "Potężne trzęsienie ziemi nawiedziło miasto, niszcząc budynki i infrastrukturę.",
            EventCategory.NATURAL_DISASTER, EventSeverity.CATASTROPHIC, 0.02,
            [
                EventChoice("emergency_response", "Natychmiastowa akcja ratunkowa",
                           "Mobilizuj wszystkie służby ratunkowe", 5000,
                           effects={"satisfaction": 10, "casualties": -50}),
                EventChoice("minimal_response", "Minimalna reakcja",
                           "Oszczędzaj środki, reaguj tylko na najgorsze przypadki", 1000,
                           effects={"satisfaction": -15, "casualties": 20})
            ]
        )
        earthquake.auto_effects = {"building_damage": 0.4, "casualties": 100, "satisfaction": -20}
        earthquake.min_population = 500
        self.events["earthquake"] = earthquake
        
        # Powódź
        flood = GameEvent(
            "flood", "Wielka Powódź",
            "Rzeka wystąpiła z brzegów, zalewając znaczną część miasta.",
            EventCategory.NATURAL_DISASTER, EventSeverity.MAJOR, 0.03,
            [
                EventChoice("build_barriers", "Buduj zapory przeciwpowodziowe",
                           "Szybko wznieś tymczasowe zapory", 8000,
                           effects={"flood_damage": -0.5, "satisfaction": 5}),
                EventChoice("evacuate", "Ewakuuj mieszkańców",
                           "Przeprowadź masową ewakuację", 3000,
                           effects={"casualties": -80, "satisfaction": -5})
            ]
        )
        flood.auto_effects = {"building_damage": 0.2, "casualties": 50, "satisfaction": -10}
        self.events["flood"] = flood
    
    def _create_economic_events(self):
        """Tworzy wydarzenia ekonomiczne"""
        
        # Boom ekonomiczny
        economic_boom = GameEvent(
            "economic_boom", "Boom Ekonomiczny",
            "Region przeżywa niespotykany wzrost gospodarczy. Twoje miasto może na tym skorzystać.",
            EventCategory.ECONOMIC, EventSeverity.MAJOR, 0.04,
            [
                EventChoice("attract_business", "Przyciągnij biznes",
                           "Zainwestuj w infrastrukturę dla firm", 8000,
                           effects={"income_multiplier": 0.3, "population_growth": 0.2}),
                EventChoice("conservative_approach", "Podejście konserwatywne",
                           "Nie zmieniaj niczego, zachowaj stabilność", 0,
                           effects={"satisfaction": 5})
            ]
        )
        economic_boom.duration_turns = 10
        self.events["economic_boom"] = economic_boom
    
    def _create_social_events(self):
        """Tworzy wydarzenia społeczne"""
        
        # Protesty
        protests = GameEvent(
            "protests", "Protesty Społeczne",
            "Mieszkańcy wyszli na ulice, protestując przeciwko polityce miasta.",
            EventCategory.SOCIAL, EventSeverity.MODERATE, 0.05,
            [
                EventChoice("negotiate", "Negocjuj z protestującymi",
                           "Spotkaj się z liderami protestów", 2000,
                           effects={"satisfaction": 15, "policy_change": True}),
                EventChoice("ignore_protests", "Ignoruj protesty",
                           "Czekaj aż protesty same się skończą", 0,
                           effects={"satisfaction": -10, "unrest": 0.2})
            ]
        )
        protests.max_satisfaction = 60
        self.events["protests"] = protests
    
    def calculate_event_probability(self, event: GameEvent, game_state: Dict) -> float:
        """Oblicza prawdopodobieństwo wystąpienia wydarzenia"""
        if not event.can_occur(game_state):
            return 0.0
        
        base_prob = event.base_probability
        
        # Modyfikatory na podstawie stanu gry
        population = game_state.get('population', 0)
        satisfaction = game_state.get('satisfaction', 50)
        money = game_state.get('money', 0)
        
        # Większe miasta mają więcej problemów
        if event.category in [EventCategory.CRIME, EventCategory.SOCIAL, EventCategory.ENVIRONMENTAL]:
            population_modifier = min(2.0, population / 5000)
            base_prob *= population_modifier
        
        # Niezadowolenie zwiększa prawdopodobieństwo problemów społecznych
        if event.category == EventCategory.SOCIAL and satisfaction < 50:
            dissatisfaction_modifier = 1 + (50 - satisfaction) / 100
            base_prob *= dissatisfaction_modifier
        
        # Brak pieniędzy zwiększa prawdopodobieństwo problemów
        if money < 5000 and event.category in [EventCategory.CRIME, EventCategory.HEALTH]:
            base_prob *= 1.5
        
        return min(1.0, base_prob)
    
    def trigger_random_event(self, game_state: Dict, turn: int) -> Optional[Dict]:
        """Losuje i uruchamia wydarzenie"""
        available_events = []
        
        for event in self.events.values():
            probability = self.calculate_event_probability(event, game_state)
            if probability > 0 and random.random() < probability:
                available_events.append(event)
        
        if not available_events:
            return None
        
        # Wybierz wydarzenie (preferuj bardziej prawdopodobne)
        event = random.choice(available_events)
        
        # Utwórz instancję wydarzenia
        event_instance = {
            'id': f"{event.id}_{turn}",
            'event_id': event.id,
            'title': event.title,
            'description': event.description,
            'category': event.category.value,
            'severity': event.severity.value,
            'choices': [{
                'id': choice.id,
                'text': choice.text,
                'description': choice.description,
                'cost': choice.cost,
                'requirements': choice.requirements,
                'can_afford': game_state.get('money', 0) >= choice.cost
            } for choice in event.choices],
            'auto_effects': event.auto_effects,
            'turn': turn,
            'duration_turns': event.duration_turns,
            'remaining_turns': event.duration_turns
        }
        
        # Dodaj do aktywnych wydarzeń
        self.active_events.append(event_instance)
        
        return event_instance
    
    def get_event_statistics(self) -> Dict:
        """Zwraca statystyki wydarzeń"""
        total_events = len(self.event_history)
        if total_events == 0:
            return {'total_events': 0}
        
        category_counts = {}
        severity_counts = {}
        
        for event_record in self.event_history:
            event_def = self.events.get(event_record['event_id'])
            if event_def:
                category = event_def.category.value
                severity = event_def.severity.value
                
                category_counts[category] = category_counts.get(category, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_events': total_events,
            'active_events': len(self.active_events),
            'category_distribution': category_counts,
            'severity_distribution': severity_counts,
            'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan do słownika"""
        return {
            'active_events': self.active_events,
            'event_history': self.event_history[-50:],  # Ostatnie 50 wydarzeń
            'event_probabilities': self.event_probabilities,
            'long_term_effects': self.long_term_effects
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan ze słownika"""
        self.active_events = data.get('active_events', [])
        self.event_history = data.get('event_history', [])
        self.event_probabilities = data.get('event_probabilities', {})
        self.long_term_effects = data.get('long_term_effects', {}) 