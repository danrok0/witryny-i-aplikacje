"""
System scenariuszy rozgrywki dla City Builder
Implementuje różne tryby gry, wyzwania i kampanie
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
import random

class ScenarioType(Enum):
    SANDBOX = "sandbox"
    CAMPAIGN = "campaign"
    CHALLENGE = "challenge"
    SURVIVAL = "survival"
    ECONOMIC = "economic"
    DISASTER = "disaster"

class DifficultyLevel(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"

@dataclass
class ScenarioObjective:
    """Cel scenariusza"""
    id: str
    title: str
    description: str
    target_value: float
    current_value: float = 0.0
    completed: bool = False
    optional: bool = False
    time_limit: Optional[int] = None  # Limit czasu w turach
    
    def check_completion(self, game_state: Dict) -> bool:
        """Sprawdza czy cel został osiągnięty"""
        # Implementacja sprawdzania celów
        if self.id == "population_target":
            self.current_value = game_state.get('population', 0)
        elif self.id == "money_target":
            self.current_value = game_state.get('money', 0)
        elif self.id == "satisfaction_target":
            self.current_value = game_state.get('satisfaction', 0)
        elif self.id == "buildings_target":
            self.current_value = len(game_state.get('buildings', []))
        elif self.id == "turns_survived":
            self.current_value = game_state.get('turn', 0)
        
        if self.current_value >= self.target_value:
            self.completed = True
        
        return self.completed

@dataclass
class ScenarioReward:
    """Nagroda za ukończenie scenariusza"""
    money: int = 0
    reputation: int = 0
    unlock_scenario: Optional[str] = None
    unlock_building: Optional[str] = None
    unlock_technology: Optional[str] = None
    achievement_id: Optional[str] = None

class Scenario:
    """Klasa reprezentująca scenariusz"""
    
    def __init__(self, scenario_id: str, title: str, description: str, 
                 scenario_type: ScenarioType, difficulty: DifficultyLevel):
        self.id = scenario_id
        self.title = title
        self.description = description
        self.type = scenario_type
        self.difficulty = difficulty
        self.objectives: List[ScenarioObjective] = []
        self.rewards = ScenarioReward()
        
        # Warunki początkowe
        self.starting_money = 10000
        self.starting_population = 100
        self.starting_buildings = []
        self.starting_technologies = []
        
        # Modyfikatory scenariusza
        self.cost_multiplier = 1.0
        self.income_multiplier = 1.0
        self.disaster_frequency = 1.0
        self.event_frequency = 1.0
        
        # Ograniczenia
        self.building_restrictions = []  # Lista zakazanych budynków
        self.technology_restrictions = []  # Lista zakazanych technologii
        self.max_turns = None  # Limit czasu
        
        # Specjalne warunki
        self.special_conditions = {}
        self.custom_events = []
        
        # Status
        self.unlocked = True
        self.completed = False
        self.best_score = 0
    
    def add_objective(self, objective: ScenarioObjective):
        """Dodaje cel do scenariusza"""
        self.objectives.append(objective)
    
    def check_completion(self, game_state: Dict) -> bool:
        """Sprawdza czy scenariusz został ukończony"""
        # Sprawdź wszystkie obowiązkowe cele
        mandatory_objectives = [obj for obj in self.objectives if not obj.optional]
        completed_mandatory = sum(1 for obj in mandatory_objectives if obj.check_completion(game_state))
        
        if completed_mandatory == len(mandatory_objectives):
            self.completed = True
            return True
        
        return False
    
    def check_failure(self, game_state: Dict) -> bool:
        """Sprawdza czy scenariusz został przegrany"""
        # Sprawdź limity czasowe
        current_turn = game_state.get('turn', 0)
        
        for objective in self.objectives:
            if objective.time_limit and current_turn > objective.time_limit and not objective.completed:
                return True
        
        # Sprawdź warunki porażki
        if self.max_turns and current_turn > self.max_turns:
            return True
        
        # Sprawdź bankructwo
        if game_state.get('money', 0) < -10000:
            return True
        
        # Sprawdź katastrofalne zadowolenie
        if game_state.get('satisfaction', 50) < 10:
            return True
        
        return False
    
    def get_progress(self) -> Dict:
        """Zwraca postęp scenariusza"""
        total_objectives = len([obj for obj in self.objectives if not obj.optional])
        completed_objectives = len([obj for obj in self.objectives if obj.completed and not obj.optional])
        
        return {
            'completed_objectives': completed_objectives,
            'total_objectives': total_objectives,
            'progress_percentage': (completed_objectives / max(total_objectives, 1)) * 100,
            'objectives_status': [{
                'id': obj.id,
                'title': obj.title,
                'completed': obj.completed,
                'progress': obj.current_value / max(obj.target_value, 1),
                'optional': obj.optional
            } for obj in self.objectives]
        }

class ScenarioManager:
    """Menedżer scenariuszy"""
    
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.current_scenario: Optional[Scenario] = None
        self.completed_scenarios: List[str] = []
        self.campaign_progress = 0
        
        self._initialize_scenarios()
    
    def _initialize_scenarios(self):
        """Inicjalizuje wszystkie scenariusze"""
        
        # SANDBOX - Tryb piaskownicy
        sandbox = Scenario(
            "sandbox", "Tryb Piaskownicy", 
            "Buduj miasto bez ograniczeń i eksperymentuj z różnymi strategiami. Nieograniczone środki finansowe!",
            ScenarioType.SANDBOX, DifficultyLevel.EASY
        )
        sandbox.starting_money = 1000000  # Milion startowych środków
        sandbox.special_conditions["unlimited_money"] = True  # Specjalny warunek nieograniczonych środków
        sandbox.special_conditions["no_bankruptcy"] = True   # Brak bankructwa
        self.scenarios["sandbox"] = sandbox
        
        # KAMPANIA - Scenariusze kampanii
        self._create_campaign_scenarios()
        
        # WYZWANIA - Specjalne wyzwania
        self._create_challenge_scenarios()
        
        # SURVIVAL - Tryby przetrwania
        self._create_survival_scenarios()
        
        # EKONOMICZNE - Wyzwania ekonomiczne
        self._create_economic_scenarios()
        
        # KATASTROFY - Scenariusze z katastrofami
        self._create_disaster_scenarios()
    
    def _create_campaign_scenarios(self):
        """Tworzy scenariusze kampanii"""
        
        # Kampania 1: Pierwsze kroki
        tutorial = Scenario(
            "campaign_01_tutorial", "Pierwsze Kroki",
            "Naucz się podstaw zarządzania miastem. Zbuduj swoje pierwsze miasto i poznaj mechaniki gry.",
            ScenarioType.CAMPAIGN, DifficultyLevel.EASY
        )
        tutorial.starting_money = 15000
        tutorial.add_objective(ScenarioObjective(
            "population_target", "Osiągnij populację 500 mieszkańców",
            "Zbuduj wystarczająco domów aby osiągnąć populację 500 mieszkańców", 500
        ))
        tutorial.add_objective(ScenarioObjective(
            "buildings_target", "Zbuduj 20 budynków",
            "Zbuduj łącznie 20 różnych budynków w swoim mieście", 20
        ))
        tutorial.rewards.money = 5000
        tutorial.rewards.unlock_scenario = "campaign_02_growth"
        self.scenarios["campaign_01_tutorial"] = tutorial
        
        # Kampania 2: Wzrost
        growth = Scenario(
            "campaign_02_growth", "Miasto w Rozwoju",
            "Rozwijaj swoje miasto i osiągnij wyższy poziom cywilizacji.",
            ScenarioType.CAMPAIGN, DifficultyLevel.NORMAL
        )
        growth.starting_money = 12000
        growth.unlocked = False
        growth.add_objective(ScenarioObjective(
            "population_target", "Osiągnij populację 2000 mieszkańców",
            "Rozbuduj miasto do 2000 mieszkańców", 2000
        ))
        growth.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 70%",
            "Zapewnij mieszkańcom wysoką jakość życia", 70
        ))
        growth.add_objective(ScenarioObjective(
            "money_target", "Zgromadź 50,000$",
            "Zbuduj silną ekonomię miasta", 50000
        ))
        growth.rewards.unlock_scenario = "campaign_03_crisis"
        self.scenarios["campaign_02_growth"] = growth
        
        # Kampania 3: Kryzys
        crisis = Scenario(
            "campaign_03_crisis", "Kryzys Ekonomiczny",
            "Poprowadź miasto przez trudny okres kryzysu ekonomicznego.",
            ScenarioType.CAMPAIGN, DifficultyLevel.HARD
        )
        crisis.starting_money = 5000
        crisis.unlocked = False
        crisis.income_multiplier = 0.5
        crisis.cost_multiplier = 1.3
        crisis.event_frequency = 2.0
        crisis.add_objective(ScenarioObjective(
            "turns_survived", "Przetrwaj 50 tur kryzysu",
            "Utrzymaj miasto przez 50 tur w trudnych warunkach", 50
        ))
        crisis.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 40%",
            "Nie pozwól na bunt mieszkańców", 40
        ))
        self.scenarios["campaign_03_crisis"] = crisis
    
    def _create_challenge_scenarios(self):
        """Tworzy scenariusze wyzwań"""
        
        # Wyzwanie: Szybki rozwój
        speed_build = Scenario(
            "challenge_speed_build", "Szybki Rozwój",
            "Zbuduj miasto 1000 mieszkańców w rekordowym czasie!",
            ScenarioType.CHALLENGE, DifficultyLevel.NORMAL
        )
        speed_build.max_turns = 30
        speed_build.add_objective(ScenarioObjective(
            "population_target", "Osiągnij 1000 mieszkańców w 30 tur",
            "Szybko rozbuduj miasto", 1000, time_limit=30
        ))
        self.scenarios["challenge_speed_build"] = speed_build
        
        # Wyzwanie: Ograniczone zasoby
        limited_resources = Scenario(
            "challenge_limited_resources", "Ograniczone Zasoby",
            "Zbuduj prosperujące miasto z minimalnym budżetem.",
            ScenarioType.CHALLENGE, DifficultyLevel.HARD
        )
        limited_resources.starting_money = 3000
        limited_resources.income_multiplier = 0.3
        limited_resources.add_objective(ScenarioObjective(
            "population_target", "Osiągnij 800 mieszkańców",
            "Rozbuduj miasto mimo ograniczeń", 800
        ))
        limited_resources.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 60%",
            "Zapewnij mieszkańcom dobre warunki", 60
        ))
        self.scenarios["challenge_limited_resources"] = limited_resources
        
        # Wyzwanie: Tylko mieszkania
        residential_only = Scenario(
            "challenge_residential_only", "Tylko Mieszkania",
            "Zbuduj miasto używając tylko budynków mieszkalnych i infrastruktury.",
            ScenarioType.CHALLENGE, DifficultyLevel.HARD
        )
        residential_only.building_restrictions = ["commercial", "industrial"]
        residential_only.add_objective(ScenarioObjective(
            "population_target", "Osiągnij 1500 mieszkańców",
            "Rozbuduj miasto bez budynków komercyjnych i przemysłowych", 1500
        ))
        self.scenarios["challenge_residential_only"] = residential_only
    
    def _create_survival_scenarios(self):
        """Tworzy scenariusze przetrwania"""
        
        # Przetrwanie: Seria katastrof
        disaster_survival = Scenario(
            "survival_disasters", "Seria Katastrof",
            "Przetrwaj serię niszczycielskich katastrof naturalnych.",
            ScenarioType.SURVIVAL, DifficultyLevel.EXTREME
        )
        disaster_survival.disaster_frequency = 5.0
        disaster_survival.add_objective(ScenarioObjective(
            "turns_survived", "Przetrwaj 100 tur",
            "Utrzymaj miasto przez 100 tur ciągłych katastrof", 100
        ))
        disaster_survival.add_objective(ScenarioObjective(
            "population_target", "Utrzymaj populację powyżej 500",
            "Nie pozwól na wyludnienie miasta", 500
        ))
        self.scenarios["survival_disasters"] = disaster_survival
        
        # Przetrwanie: Epidemia
        epidemic = Scenario(
            "survival_epidemic", "Epidemia",
            "Poprowadź miasto przez śmiertelną epidemię.",
            ScenarioType.SURVIVAL, DifficultyLevel.HARD
        )
        epidemic.special_conditions["epidemic_active"] = True
        epidemic.add_objective(ScenarioObjective(
            "turns_survived", "Przetrwaj 60 tur epidemii",
            "Utrzymaj miasto podczas epidemii", 60
        ))
        epidemic.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 30%",
            "Zapobiegnij panice i buntom", 30
        ))
        self.scenarios["survival_epidemic"] = epidemic
    
    def _create_economic_scenarios(self):
        """Tworzy scenariusze ekonomiczne"""
        
        # Ekonomiczne: Potęga handlowa
        trade_empire = Scenario(
            "economic_trade_empire", "Potęga Handlowa",
            "Zbuduj imperium handlowe i zdominuj rynki regionalne.",
            ScenarioType.ECONOMIC, DifficultyLevel.NORMAL
        )
        trade_empire.add_objective(ScenarioObjective(
            "money_target", "Zgromadź 200,000$",
            "Zbuduj potężną ekonomię", 200000
        ))
        trade_empire.add_objective(ScenarioObjective(
            "trade_volume", "Osiągnij 100,000$ obrotu handlowego",
            "Zdominuj handel regionalny", 100000
        ))
        self.scenarios["economic_trade_empire"] = trade_empire
        
        # Ekonomiczne: Bez podatków
        no_taxes = Scenario(
            "economic_no_taxes", "Miasto Bez Podatków",
            "Zbuduj prosperujące miasto bez pobierania podatków.",
            ScenarioType.ECONOMIC, DifficultyLevel.HARD
        )
        no_taxes.special_conditions["no_taxes"] = True
        no_taxes.add_objective(ScenarioObjective(
            "population_target", "Osiągnij 1200 mieszkańców",
            "Rozbuduj miasto bez dochodów podatkowych", 1200
        ))
        no_taxes.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 80%",
            "Zapewnij mieszkańcom doskonałe warunki", 80
        ))
        self.scenarios["economic_no_taxes"] = no_taxes
    
    def _create_disaster_scenarios(self):
        """Tworzy scenariusze z katastrofami"""
        
        # Katastrofa: Trzęsienie ziemi
        earthquake = Scenario(
            "disaster_earthquake", "Wielkie Trzęsienie Ziemi",
            "Odbuduj miasto po niszczycielskim trzęsieniu ziemi.",
            ScenarioType.DISASTER, DifficultyLevel.HARD
        )
        earthquake.starting_money = 8000
        earthquake.special_conditions["earthquake_damage"] = 0.7  # 70% budynków zniszczonych
        earthquake.add_objective(ScenarioObjective(
            "population_target", "Odbuduj populację do 1000 mieszkańców",
            "Przywróć miasto do życia", 1000
        ))
        earthquake.add_objective(ScenarioObjective(
            "buildings_target", "Zbuduj 50 nowych budynków",
            "Odbuduj infrastrukturę miasta", 50
        ))
        self.scenarios["disaster_earthquake"] = earthquake
        
        # Katastrofa: Powódź
        flood = Scenario(
            "disaster_flood", "Wielka Powódź",
            "Zarządzaj miastem podczas i po wielkiej powodzi.",
            ScenarioType.DISASTER, DifficultyLevel.HARD
        )
        flood.special_conditions["flood_active"] = True
        flood.cost_multiplier = 1.5  # Wyższe koszty budowy
        flood.add_objective(ScenarioObjective(
            "turns_survived", "Przetrwaj 40 tur powodzi",
            "Utrzymaj miasto podczas powodzi", 40
        ))
        flood.add_objective(ScenarioObjective(
            "satisfaction_target", "Utrzymaj zadowolenie powyżej 35%",
            "Zapobiegnij masowej emigracji", 35
        ))
        self.scenarios["disaster_flood"] = flood
    
    def start_scenario(self, scenario_id: str) -> Tuple[bool, str]:
        """Rozpoczyna scenariusz"""
        if scenario_id not in self.scenarios:
            return False, "Nieznany scenariusz"
        
        scenario = self.scenarios[scenario_id]
        
        if not scenario.unlocked:
            return False, "Scenariusz nie jest odblokowany"
        
        self.current_scenario = scenario
        
        # Reset celów scenariusza
        for objective in scenario.objectives:
            objective.current_value = 0.0
            objective.completed = False
        
        return True, f"Rozpoczęto scenariusz: {scenario.title}"
    
    def update_scenario(self, game_state: Dict) -> Dict:
        """Aktualizuje aktualny scenariusz"""
        if not self.current_scenario:
            return {}
        
        # Sprawdź cele
        scenario_completed = self.current_scenario.check_completion(game_state)
        scenario_failed = self.current_scenario.check_failure(game_state)
        
        result = {
            'scenario_id': self.current_scenario.id,
            'completed': scenario_completed,
            'failed': scenario_failed,
            'progress': self.current_scenario.get_progress()
        }
        
        if scenario_completed:
            self._complete_scenario(self.current_scenario.id)
            result['rewards'] = self._get_scenario_rewards(self.current_scenario)
        
        return result
    
    def _complete_scenario(self, scenario_id: str):
        """Oznacza scenariusz jako ukończony"""
        if scenario_id not in self.completed_scenarios:
            self.completed_scenarios.append(scenario_id)
        
        scenario = self.scenarios[scenario_id]
        scenario.completed = True
        
        # Odblokuj następne scenariusze
        if scenario.rewards.unlock_scenario:
            unlock_id = scenario.rewards.unlock_scenario
            if unlock_id in self.scenarios:
                self.scenarios[unlock_id].unlocked = True
        
        # Aktualizuj postęp kampanii
        if scenario.type == ScenarioType.CAMPAIGN:
            self.campaign_progress += 1
    
    def _get_scenario_rewards(self, scenario: Scenario) -> Dict:
        """Zwraca nagrody za ukończenie scenariusza"""
        return {
            'money': scenario.rewards.money,
            'reputation': scenario.rewards.reputation,
            'unlock_scenario': scenario.rewards.unlock_scenario,
            'unlock_building': scenario.rewards.unlock_building,
            'unlock_technology': scenario.rewards.unlock_technology,
            'achievement_id': scenario.rewards.achievement_id
        }
    
    def get_available_scenarios(self) -> List[Dict]:
        """Zwraca listę dostępnych scenariuszy"""
        return [{
            'id': scenario.id,
            'title': scenario.title,
            'description': scenario.description,
            'type': scenario.type.value,
            'difficulty': scenario.difficulty.value,
            'unlocked': scenario.unlocked,
            'completed': scenario.completed,
            'objectives_count': len(scenario.objectives)
        } for scenario in self.scenarios.values() if scenario.unlocked]
    
    def get_scenario_details(self, scenario_id: str) -> Optional[Dict]:
        """Zwraca szczegóły scenariusza"""
        if scenario_id not in self.scenarios:
            return None
        
        scenario = self.scenarios[scenario_id]
        return {
            'id': scenario.id,
            'title': scenario.title,
            'description': scenario.description,
            'type': scenario.type.value,
            'difficulty': scenario.difficulty.value,
            'starting_conditions': {
                'money': scenario.starting_money,
                'population': scenario.starting_population,
                'buildings': scenario.starting_buildings,
                'technologies': scenario.starting_technologies
            },
            'modifiers': {
                'cost_multiplier': scenario.cost_multiplier,
                'income_multiplier': scenario.income_multiplier,
                'disaster_frequency': scenario.disaster_frequency,
                'event_frequency': scenario.event_frequency
            },
            'objectives': [{
                'id': obj.id,
                'title': obj.title,
                'description': obj.description,
                'target_value': obj.target_value,
                'optional': obj.optional,
                'time_limit': obj.time_limit
            } for obj in scenario.objectives],
            'rewards': {
                'money': scenario.rewards.money,
                'reputation': scenario.rewards.reputation,
                'unlocks': {
                    'scenario': scenario.rewards.unlock_scenario,
                    'building': scenario.rewards.unlock_building,
                    'technology': scenario.rewards.unlock_technology
                }
            },
            'restrictions': {
                'buildings': scenario.building_restrictions,
                'technologies': scenario.technology_restrictions,
                'max_turns': scenario.max_turns
            },
            'special_conditions': scenario.special_conditions
        }
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan do słownika"""
        return {
            'completed_scenarios': self.completed_scenarios,
            'campaign_progress': self.campaign_progress,
            'current_scenario': self.current_scenario.id if self.current_scenario else None,
            'scenario_states': {
                scenario_id: {
                    'unlocked': scenario.unlocked,
                    'completed': scenario.completed,
                    'best_score': scenario.best_score
                }
                for scenario_id, scenario in self.scenarios.items()
            }
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan ze słownika"""
        self.completed_scenarios = data.get('completed_scenarios', [])
        self.campaign_progress = data.get('campaign_progress', 0)
        
        current_scenario_id = data.get('current_scenario')
        if current_scenario_id and current_scenario_id in self.scenarios:
            self.current_scenario = self.scenarios[current_scenario_id]
        
        scenario_states = data.get('scenario_states', {})
        for scenario_id, state in scenario_states.items():
            if scenario_id in self.scenarios:
                scenario = self.scenarios[scenario_id]
                scenario.unlocked = state.get('unlocked', scenario.unlocked)
                scenario.completed = state.get('completed', False)
                scenario.best_score = state.get('best_score', 0) 