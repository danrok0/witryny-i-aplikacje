"""
System celów i zadań dla City Builder.

Implementuje:
- Różne typy celów (populacja, ekonomia, budynki, etc.)
- System prerekvizytów (cele zależne od innych)
- Nagrody za ukończenie celów
- Śledzenie postępu
- Limity czasowe
"""
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class ObjectiveType(Enum):
    """
    Typy celów w grze.
    
    Każdy typ skupia się na innym aspekcie rozwoju miasta.
    """
    POPULATION = "population"          # cele populacyjne
    ECONOMY = "economy"               # cele ekonomiczne
    SATISFACTION = "satisfaction"      # cele zadowolenia mieszkańców
    BUILDINGS = "buildings"           # cele budowlane
    TECHNOLOGY = "technology"         # cele technologiczne
    SURVIVAL = "survival"             # cele przetrwania
    INFRASTRUCTURE = "infrastructure" # cele infrastrukturalne
    GROWTH = "growth"                 # cele wzrostu
    EFFICIENCY = "efficiency"         # cele efektywności
    CHALLENGE = "challenge"           # cele wyzwania

class ObjectiveStatus(Enum):
    """
    Statusy celów - określają czy cel jest dostępny, ukończony, etc.
    """
    ACTIVE = "active"       # cel aktywny (można go realizować)
    COMPLETED = "completed" # cel ukończony
    FAILED = "failed"       # cel nieudany
    LOCKED = "locked"       # cel zablokowany (wymaga prerekvizytów)

@dataclass
class Objective:
    """
    Reprezentuje pojedynczy cel w grze.
    
    @dataclass automatycznie generuje konstruktor i inne metody.
    """
    id: str                           # unikalne ID celu
    title: str                        # tytuł wyświetlany graczowi
    description: str                  # opis celu
    objective_type: ObjectiveType     # typ celu
    target_value: float               # wartość docelowa do osiągnięcia
    current_value: float = 0.0        # aktualny postęp
    status: ObjectiveStatus = ObjectiveStatus.ACTIVE  # status celu
    reward_money: int = 0             # nagroda pieniężna
    reward_satisfaction: int = 0      # nagroda zadowolenia
    reward_description: str = ""      # opis nagrody
    time_limit: Optional[int] = None  # limit tur (None = bez limitu)
    turns_remaining: Optional[int] = None  # pozostałe tury
    prerequisites: List[str] = None   # lista ID celów wymaganych
    
    def __post_init__(self):
        """
        Metoda wywoływana po inicjalizacji obiektu.
        
        Ustawia puste listy i inicjalne wartości jeśli nie zostały podane.
        """
        if self.prerequisites is None:
            self.prerequisites = []  # pusta lista prerekvizytów
        if self.time_limit:
            self.turns_remaining = self.time_limit  # ustaw pozostały czas

class ObjectiveManager:
    """
    Menedżer systemu celów - zarządza wszystkimi celami w grze.
    
    Funkcje:
    - Tworzenie i zarządzanie celami
    - Sprawdzanie postępu
    - Odblokowanie nowych celów
    - Przyznawanie nagród
    - Śledzenie limitów czasowych
    """
    
    def __init__(self):
        """
        Konstruktor menedżera celów.
        
        Inicjalizuje puste kolekcje i tworzy podstawowe cele.
        """
        self.objectives = {}              # słownik wszystkich celów {id: Objective}
        self.completed_objectives = []    # lista ukończonych celów
        self.failed_objectives = []       # lista nieudanych celów
        self.current_turn = 0            # aktualna tura gry
        
        # Inicjalizuj podstawowe cele
        self._initialize_objectives()
    
    def _initialize_objectives(self):
        """
        Inicjalizuje podstawowe cele gry.
        
        Tworzy hierarchię celów od podstawowych do zaawansowanych,
        z systemem prerekvizytów łączącym je w logiczną sekwencję.
        """
        
        # === CELE POCZĄTKOWE (Poziom 1) - zwiększone wymagania ===
        self.add_objective(Objective(
            id="first_population",
            title="Pierwsi Mieszkańcy",
            description="Osiągnij populację 250 mieszkańców",
            objective_type=ObjectiveType.POPULATION,
            target_value=250,
            reward_money=1000,
            reward_satisfaction=5,
            reward_description="Bonus za pierwsze 250 mieszkańców"
        ))
        
        self.add_objective(Objective(
            id="basic_economy",
            title="Stabilna Ekonomia",
            description="Zgromadź 75000$ w budżecie miasta",
            objective_type=ObjectiveType.ECONOMY,
            target_value=75000,
            reward_money=2000,
            reward_satisfaction=3,
            reward_description="Bonus za stabilną ekonomię"
        ))
        
        self.add_objective(Objective(
            id="first_services",
            title="Podstawowe Usługi",
            description="Zbuduj szkołę, szpital i 15 domów",
            objective_type=ObjectiveType.BUILDINGS,
            target_value=17,  # 2 usługi + 15 domów
            reward_money=1500,
            reward_satisfaction=10,
            reward_description="Bonus za podstawowe usługi"
        ))
        
        self.add_objective(Objective(
            id="first_roads",
            title="Pierwsza Infrastruktura",
            description="Zbuduj 20 segmentów dróg",
            objective_type=ObjectiveType.INFRASTRUCTURE,
            target_value=20,
            reward_money=1000,
            reward_satisfaction=5,
            reward_description="Bonus za pierwszą infrastrukturę"
        ))
        
        # === CELE ŚREDNIE (Poziom 2) - wymagają ukończenia celów z poziomu 1 ===
        self.add_objective(Objective(
            id="growing_city",
            title="Rozwijające się Miasto",
            description="Osiągnij populację 1000 mieszkańców",
            objective_type=ObjectiveType.POPULATION,
            target_value=1000,
            reward_money=3000,
            reward_satisfaction=8,
            reward_description="Bonus za rozwijające się miasto",
            prerequisites=["first_population"],    # wymaga ukończenia "first_population"
            status=ObjectiveStatus.LOCKED         # zablokowany na początku
        ))
        
        self.add_objective(Objective(
            id="happy_citizens",
            title="Zadowoleni Mieszkańcy",
            description="Utrzymaj zadowolenie powyżej 75% przez 15 tur",
            objective_type=ObjectiveType.SATISFACTION,
            target_value=75,
            time_limit=15,                        # limit czasowy: 15 tur
            reward_money=2500,
            reward_satisfaction=15,
            reward_description="Bonus za zadowolonych mieszkańców",
            prerequisites=["first_services"],     # wymaga podstawowych usług
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="economic_powerhouse",
            title="Potęga Ekonomiczna",
            description="Zgromadź 150000$ w budżecie miasta",
            objective_type=ObjectiveType.ECONOMY,
            target_value=150000,
            reward_money=5000,
            reward_satisfaction=5,
            reward_description="Bonus za potęgę ekonomiczną",
            prerequisites=["basic_economy"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # === CELE ZAAWANSOWANE (Poziom 3) - wymagają wielu prerekvizytów ===
        self.add_objective(Objective(
            id="metropolis",
            title="Metropolia",
            description="Osiągnij populację 2000 mieszkańców",
            objective_type=ObjectiveType.POPULATION,
            target_value=2000,
            reward_money=10000,
            reward_satisfaction=20,
            reward_description="Bonus za metropolię",
            prerequisites=["growing_city", "happy_citizens"],  # wymaga 2 celów
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="tech_advancement",
            title="Postęp Technologiczny",
            description="Odblokuj 3 technologie",
            objective_type=ObjectiveType.TECHNOLOGY,
            target_value=3,
            reward_money=7500,
            reward_satisfaction=12,
            reward_description="Bonus za postęp technologiczny",
            prerequisites=["economic_powerhouse"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # === CELE WYZWANIA (specjalne cele trudniejsze) ===
        self.add_objective(Objective(
            id="crisis_survival",
            title="Przetrwanie Kryzysu",
            description="Przetrwaj 5 tur z budżetem poniżej 1000$",
            objective_type=ObjectiveType.SURVIVAL,
            target_value=5,
            reward_money=5000,
            reward_satisfaction=25,
            reward_description="Bonus za przetrwanie kryzysu"
            # brak prerekvizytów - dostępne od początku
        ))
        
        # === CELE INFRASTRUKTURALNE (Poziom 4) ===
        self.add_objective(Objective(
            id="road_network",
            title="Sieć Drogowa",
            description="Zbuduj 50 segmentów dróg",
            objective_type=ObjectiveType.INFRASTRUCTURE,
            target_value=50,
            reward_money=3000,
            reward_satisfaction=8,
            reward_description="Bonus za rozwiniętą sieć drogową",
            prerequisites=["growing_city"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="diverse_economy",
            title="Zróżnicowana Ekonomia",
            description="Zbuduj po 5 budynków każdego typu (mieszkalne, przemysłowe, usługowe)",
            objective_type=ObjectiveType.BUILDINGS,
            target_value=15,  # 5+5+5
            reward_money=4000,
            reward_satisfaction=12,
            reward_description="Bonus za zróżnicowaną ekonomię",
            prerequisites=["economic_powerhouse"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="mega_city",
            title="Megamiasto",
            description="Osiągnij populację 5000 mieszkańców",
            objective_type=ObjectiveType.POPULATION,
            target_value=5000,
            reward_money=15000,
            reward_satisfaction=30,
            reward_description="Bonus za megamiasto",
            prerequisites=["metropolis"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # CELE EFEKTYWNOŚCI (Poziom 5)
        self.add_objective(Objective(
            id="efficient_city",
            title="Efektywne Miasto",
            description="Utrzymaj zadowolenie powyżej 80% przez 20 tur",
            objective_type=ObjectiveType.SATISFACTION,
            target_value=80,
            time_limit=20,
            reward_money=8000,
            reward_satisfaction=20,
            reward_description="Bonus za efektywne zarządzanie",
            prerequisites=["happy_citizens", "tech_advancement"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="economic_giant",
            title="Gigant Ekonomiczny",
            description="Zgromadź 300000$ w budżecie miasta",
            objective_type=ObjectiveType.ECONOMY,
            target_value=300000,
            reward_money=25000,
            reward_satisfaction=15,
            reward_description="Bonus za giganta ekonomicznego",
            prerequisites=["economic_powerhouse", "diverse_economy"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="tech_master",
            title="Mistrz Technologii",
            description="Odblokuj wszystkie 5 technologii",
            objective_type=ObjectiveType.TECHNOLOGY,
            target_value=5,
            reward_money=12000,
            reward_satisfaction=25,
            reward_description="Bonus za mistrzostwo technologiczne",
            prerequisites=["tech_advancement"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # CELE WZROSTU (Poziom 6)
        self.add_objective(Objective(
            id="population_boom",
            title="Boom Demograficzny",
            description="Zwiększ populację o 1000 mieszkańców w ciągu 15 tur",
            objective_type=ObjectiveType.GROWTH,
            target_value=1000,
            time_limit=15,
            reward_money=10000,
            reward_satisfaction=18,
            reward_description="Bonus za boom demograficzny",
            prerequisites=["mega_city"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="construction_spree",
            title="Szał Budowy",
            description="Zbuduj 100 budynków",
            objective_type=ObjectiveType.BUILDINGS,
            target_value=100,
            reward_money=8000,
            reward_satisfaction=10,
            reward_description="Bonus za intensywną rozbudowę",
            prerequisites=["diverse_economy"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # CELE WYZWAŃ SPECJALNYCH (Poziom 7)
        self.add_objective(Objective(
            id="economic_rollercoaster",
            title="Kolejka Ekonomiczna",
            description="Przetrwaj 3 okresy z budżetem poniżej 5000$ i powyżej 50000$",
            objective_type=ObjectiveType.CHALLENGE,
            target_value=3,
            reward_money=15000,
            reward_satisfaction=30,
            reward_description="Bonus za przetrwanie wahań ekonomicznych",
            prerequisites=["economic_giant"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="satisfaction_master",
            title="Mistrz Zadowolenia",
            description="Utrzymaj zadowolenie powyżej 90% przez 30 tur",
            objective_type=ObjectiveType.SATISFACTION,
            target_value=90,
            time_limit=30,
            reward_money=20000,
            reward_satisfaction=40,
            reward_description="Bonus za mistrzowskie zarządzanie zadowoleniem",
            prerequisites=["efficient_city"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="ultimate_city",
            title="Ostateczne Miasto",
            description="Osiągnij populację 10000 mieszkańców",
            objective_type=ObjectiveType.POPULATION,
            target_value=10000,
            reward_money=50000,
            reward_satisfaction=50,
            reward_description="Bonus za ostateczne miasto",
            prerequisites=["population_boom", "satisfaction_master", "tech_master"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # CELE DŁUGOTERMINOWE (Poziom 8)
        self.add_objective(Objective(
            id="millionaire_mayor",
            title="Burmistrz Milioner",
            description="Zgromadź 1000000$ w budżecie miasta",
            objective_type=ObjectiveType.ECONOMY,
            target_value=1000000,
            reward_money=100000,
            reward_satisfaction=25,
            reward_description="Bonus za zostanie milionerem",
            prerequisites=["economic_giant", "construction_spree"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="infrastructure_king",
            title="Król Infrastruktury",
            description="Zbuduj 200 segmentów dróg i 50 budynków usługowych",
            objective_type=ObjectiveType.INFRASTRUCTURE,
            target_value=250,  # 200 + 50
            reward_money=30000,
            reward_satisfaction=35,
            reward_description="Bonus za króla infrastruktury",
            prerequisites=["road_network", "construction_spree"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # CELE PRZETRWANIA EKSTREMALNEGO
        self.add_objective(Objective(
            id="disaster_survivor",
            title="Ocalały z Katastrofy",
            description="Przetrwaj 10 tur z zadowoleniem poniżej 30%",
            objective_type=ObjectiveType.SURVIVAL,
            target_value=10,
            reward_money=12000,
            reward_satisfaction=40,
            reward_description="Bonus za przetrwanie katastrofy",
            prerequisites=["crisis_survival"],
            status=ObjectiveStatus.LOCKED
        ))
        
        self.add_objective(Objective(
            id="phoenix_city",
            title="Miasto Feniks",
            description="Odbuduj miasto: spadnij poniżej 500 mieszkańców, a następnie osiągnij 3000",
            objective_type=ObjectiveType.CHALLENGE,
            target_value=1,  # Specjalny cel - sprawdzany osobno
            reward_money=25000,
            reward_satisfaction=50,
            reward_description="Bonus za odbudowę miasta z popiołów",
            prerequisites=["disaster_survivor"],
            status=ObjectiveStatus.LOCKED
        ))
        
        # Ustaw początkowe statusy
        self._update_objective_availability()
    
    def add_objective(self, objective: Objective):
        """Dodaje cel do managera"""
        self.objectives[objective.id] = objective
    
    def update_objectives(self, game_state: Dict):
        """Aktualizuje postęp wszystkich celów na podstawie stanu gry"""
        self.current_turn = game_state.get('turn', 0)
        
        # Nie sprawdzaj celów w pierwszych 2 turach, żeby gracz miał czas na rozgrywkę
        if self.current_turn < 2:
            return
        
        for obj_id, objective in self.objectives.items():
            if objective.status != ObjectiveStatus.ACTIVE:
                continue
            
            # Aktualizuj wartość bieżącą na podstawie typu celu
            if objective.objective_type == ObjectiveType.POPULATION:
                objective.current_value = game_state.get('population', 0)
            
            elif objective.objective_type == ObjectiveType.ECONOMY:
                objective.current_value = game_state.get('money', 0)
            
            elif objective.objective_type == ObjectiveType.SATISFACTION:
                satisfaction = game_state.get('satisfaction', 0)
                if obj_id == "happy_citizens":
                    # Specjalna logika dla celu zadowolenia
                    if satisfaction >= objective.target_value:
                        if not hasattr(objective, 'satisfaction_turns'):
                            objective.satisfaction_turns = 0
                        objective.satisfaction_turns += 1
                        objective.current_value = objective.satisfaction_turns
                    else:
                        objective.satisfaction_turns = 0
                        objective.current_value = 0
                elif obj_id == "efficient_city":
                    # Cel efektywnego miasta
                    if satisfaction >= objective.target_value:
                        if not hasattr(objective, 'efficiency_turns'):
                            objective.efficiency_turns = 0
                        objective.efficiency_turns += 1
                        objective.current_value = objective.efficiency_turns
                    else:
                        objective.efficiency_turns = 0
                        objective.current_value = 0
                elif obj_id == "satisfaction_master":
                    # Cel mistrza zadowolenia
                    if satisfaction >= objective.target_value:
                        if not hasattr(objective, 'master_turns'):
                            objective.master_turns = 0
                        objective.master_turns += 1
                        objective.current_value = objective.master_turns
                    else:
                        objective.master_turns = 0
                        objective.current_value = 0
                else:
                    objective.current_value = satisfaction
            
            elif objective.objective_type == ObjectiveType.BUILDINGS:
                buildings = game_state.get('buildings', [])
                if obj_id == "first_services":
                    # Policz szkoły, szpitale i domy
                    service_count = 0
                    house_count = 0
                    for building in buildings:
                        building_type = building.building_type.value.lower() if hasattr(building, 'building_type') else str(building).lower()
                        
                        if 'school' in building_type or 'hospital' in building_type:
                            service_count += 1
                        elif 'house' in building_type:
                            house_count += 1
                    
                    objective.current_value = service_count + house_count
                elif obj_id == "diverse_economy":
                    # Policz różne typy budynków
                    residential = 0
                    industrial = 0
                    commercial = 0
                    
                    for building in buildings:
                        building_type = building.building_type.value.lower() if hasattr(building, 'building_type') else str(building).lower()
                        
                        if 'house' in building_type or 'apartment' in building_type:
                            residential += 1
                        elif 'factory' in building_type or 'warehouse' in building_type:
                            industrial += 1
                        elif 'shop' in building_type or 'office' in building_type:
                            commercial += 1
                    
                    # Sprawdź czy każdy typ ma co najmniej 5 budynków
                    if residential >= 5 and industrial >= 5 and commercial >= 5:
                        objective.current_value = 15  # Cel osiągnięty
                    else:
                        objective.current_value = min(residential, 5) + min(industrial, 5) + min(commercial, 5)
                else:
                    objective.current_value = len(buildings)
            
            elif objective.objective_type == ObjectiveType.TECHNOLOGY:
                technologies = game_state.get('unlocked_technologies', [])
                objective.current_value = len(technologies)
            
            elif objective.objective_type == ObjectiveType.SURVIVAL:
                if obj_id == "crisis_survival":
                    money = game_state.get('money', 0)
                    if money < 1000:
                        if not hasattr(objective, 'crisis_turns'):
                            objective.crisis_turns = 0
                        objective.crisis_turns += 1
                        objective.current_value = objective.crisis_turns
                    else:
                        if hasattr(objective, 'crisis_turns'):
                            objective.crisis_turns = 0
                        objective.current_value = 0
                elif obj_id == "disaster_survivor":
                    satisfaction = game_state.get('satisfaction', 0)
                    if satisfaction < 30:
                        if not hasattr(objective, 'disaster_turns'):
                            objective.disaster_turns = 0
                        objective.disaster_turns += 1
                        objective.current_value = objective.disaster_turns
                    else:
                        if hasattr(objective, 'disaster_turns'):
                            objective.disaster_turns = 0
                        objective.current_value = 0
            
            elif objective.objective_type == ObjectiveType.INFRASTRUCTURE:
                buildings = game_state.get('buildings', [])
                if obj_id == "road_network":
                    # Policz drogi
                    road_count = 0
                    for building in buildings:
                        building_type = building.building_type.value.lower() if hasattr(building, 'building_type') else str(building).lower()
                        
                        if 'road' in building_type:
                            road_count += 1
                    
                    objective.current_value = road_count
                elif obj_id == "infrastructure_king":
                    # Policz drogi i budynki usługowe
                    road_count = 0
                    service_count = 0
                    
                    for building in buildings:
                        building_type = building.building_type.value.lower() if hasattr(building, 'building_type') else str(building).lower()
                        
                        if 'road' in building_type:
                            road_count += 1
                        elif any(service in building_type for service in ['school', 'hospital', 'police', 'fire', 'park']):
                            service_count += 1
                    
                    objective.current_value = road_count + service_count
            
            elif objective.objective_type == ObjectiveType.GROWTH:
                if obj_id == "population_boom":
                    current_pop = game_state.get('population', 0)
                    if not hasattr(objective, 'start_population'):
                        objective.start_population = current_pop
                        objective.current_value = 0
                    else:
                        growth = current_pop - objective.start_population
                        objective.current_value = max(0, growth)
            
            elif objective.objective_type == ObjectiveType.EFFICIENCY:
                # Cele efektywności - obecnie obsługiwane w SATISFACTION
                pass
            
            elif objective.objective_type == ObjectiveType.CHALLENGE:
                if obj_id == "economic_rollercoaster":
                    money = game_state.get('money', 0)
                    if not hasattr(objective, 'rollercoaster_cycles'):
                        objective.rollercoaster_cycles = 0
                        objective.in_low_phase = False
                        objective.in_high_phase = False
                    
                    # Sprawdź fazy ekonomiczne
                    if money < 5000 and not objective.in_low_phase:
                        objective.in_low_phase = True
                        objective.in_high_phase = False
                    elif money > 50000 and objective.in_low_phase and not objective.in_high_phase:
                        objective.in_high_phase = True
                        objective.rollercoaster_cycles += 1
                        objective.in_low_phase = False
                    elif money < 5000 and objective.in_high_phase:
                        objective.in_high_phase = False
                    
                    objective.current_value = objective.rollercoaster_cycles
                
                elif obj_id == "phoenix_city":
                    current_pop = game_state.get('population', 0)
                    if not hasattr(objective, 'phoenix_phase'):
                        objective.phoenix_phase = "waiting_for_fall"  # waiting_for_fall, fell, rising
                        objective.min_population = current_pop
                    
                    if objective.phoenix_phase == "waiting_for_fall":
                        if current_pop < 500:
                            objective.phoenix_phase = "fell"
                            objective.min_population = current_pop
                    elif objective.phoenix_phase == "fell":
                        if current_pop >= 3000:
                            objective.phoenix_phase = "risen"
                            objective.current_value = 1
                    
                    # Jeśli populacja spadnie ponownie, resetuj
                    if current_pop < objective.min_population:
                        objective.min_population = current_pop
            
            # Sprawdź czy cel został ukończony
            if objective.current_value >= objective.target_value:
                self._complete_objective(obj_id)
            
            # Sprawdź limit czasu
            if objective.time_limit and objective.turns_remaining is not None:
                objective.turns_remaining -= 1
                if objective.turns_remaining <= 0 and objective.status == ObjectiveStatus.ACTIVE:
                    self._fail_objective(obj_id)
        
        # Aktualizuj dostępność celów
        self._update_objective_availability()
    
    def _complete_objective(self, obj_id: str):
        """Oznacza cel jako ukończony i przyznaje nagrody"""
        objective = self.objectives[obj_id]
        objective.status = ObjectiveStatus.COMPLETED
        self.completed_objectives.append(obj_id)
        
        return {
            'money_reward': objective.reward_money,
            'satisfaction_reward': objective.reward_satisfaction,
            'description': objective.reward_description
        }
    
    def _fail_objective(self, obj_id: str):
        """Oznacza cel jako nieudany"""
        objective = self.objectives[obj_id]
        objective.status = ObjectiveStatus.FAILED
        self.failed_objectives.append(obj_id)
    
    def _update_objective_availability(self):
        """Aktualizuje dostępność celów na podstawie prerequisitów"""
        for obj_id, objective in self.objectives.items():
            if objective.status == ObjectiveStatus.LOCKED:
                # Sprawdź czy wszystkie prerequisity są ukończone
                if all(prereq in self.completed_objectives for prereq in objective.prerequisites):
                    objective.status = ObjectiveStatus.ACTIVE
    
    def get_active_objectives(self) -> List[Objective]:
        """Zwraca listę aktywnych celów"""
        return [obj for obj in self.objectives.values() if obj.status == ObjectiveStatus.ACTIVE]
    
    def get_completed_objectives(self) -> List[Objective]:
        """Zwraca listę ukończonych celów"""
        return [obj for obj in self.objectives.values() if obj.status == ObjectiveStatus.COMPLETED]
    
    def get_objective_progress(self, obj_id: str) -> float:
        """Zwraca postęp celu jako procent (0.0 - 1.0)"""
        if obj_id not in self.objectives:
            return 0.0
        
        objective = self.objectives[obj_id]
        if objective.target_value == 0:
            return 1.0
        
        return min(1.0, objective.current_value / objective.target_value)
    
    def get_objectives_summary(self) -> Dict:
        """Zwraca podsumowanie wszystkich celów"""
        return {
            'active': len(self.get_active_objectives()),
            'completed': len(self.get_completed_objectives()),
            'failed': len(self.failed_objectives),
            'total': len(self.objectives),
            'completion_rate': len(self.completed_objectives) / len(self.objectives) if self.objectives else 0
        } 