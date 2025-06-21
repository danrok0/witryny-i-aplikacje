"""
Rozszerzony system dyplomatyczny dla City Builder
Implementuje wojny, sojusze, misje dyplomatyczne i zaawansowane relacje
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random
import math
from datetime import datetime

class RelationshipStatus(Enum):
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"
    AT_WAR = "at_war"

class MissionType(Enum):
    TRADE_AGREEMENT = "trade_agreement"
    ALLIANCE_PROPOSAL = "alliance_proposal"
    PEACE_TREATY = "peace_treaty"
    SPY_MISSION = "spy_mission"
    CULTURAL_EXCHANGE = "cultural_exchange"
    ECONOMIC_AID = "economic_aid"
    MILITARY_SUPPORT = "military_support"

class MissionStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WarType(Enum):
    TRADE_WAR = "trade_war"
    TERRITORIAL = "territorial"
    RESOURCE_CONFLICT = "resource_conflict"
    IDEOLOGICAL = "ideological"

@dataclass
class DiplomaticMission:
    """Reprezentuje misję dyplomatyczną"""
    id: str
    target_city: str
    mission_type: MissionType
    status: MissionStatus
    cost: float
    duration_turns: int
    remaining_turns: int
    success_chance: float
    rewards: Dict[str, float]
    penalties: Dict[str, float]
    started_turn: int
    description: str
    
    def calculate_success(self, relationship_points: int, city_reputation: int) -> bool:
        """Oblicza czy misja się powiodła"""
        # Bazowa szansa sukcesu
        base_chance = self.success_chance
        
        # Modyfikatory na podstawie relacji
        if relationship_points > 50:
            base_chance += 0.2
        elif relationship_points < -50:
            base_chance -= 0.3
        
        # Modyfikator reputacji
        reputation_modifier = (city_reputation - 50) / 100
        base_chance += reputation_modifier * 0.1
        
        # Modyfikator typu misji
        mission_difficulty = {
            MissionType.TRADE_AGREEMENT: 0.0,
            MissionType.CULTURAL_EXCHANGE: 0.1,
            MissionType.ECONOMIC_AID: -0.1,
            MissionType.ALLIANCE_PROPOSAL: -0.2,
            MissionType.PEACE_TREATY: -0.3,
            MissionType.SPY_MISSION: -0.4,
            MissionType.MILITARY_SUPPORT: -0.3
        }
        
        base_chance += mission_difficulty.get(self.mission_type, 0)
        
        # Losowy element
        return random.random() < max(0.1, min(0.9, base_chance))

@dataclass
class War:
    """Reprezentuje wojnę między miastami"""
    id: str
    enemy_city: str
    war_type: WarType
    started_turn: int
    duration_turns: int
    our_strength: float
    enemy_strength: float
    casualties_us: int
    casualties_enemy: int
    economic_cost: float
    war_exhaustion: float  # 0-1, wpływa na zadowolenie
    active: bool = True
    
    def calculate_battle_outcome(self) -> Dict:
        """Oblicza wynik bitwy"""
        # Porównaj siły
        strength_ratio = self.our_strength / max(self.enemy_strength, 1)
        
        # Bazowa szansa wygranej
        win_chance = 0.5 + (strength_ratio - 1) * 0.2
        win_chance = max(0.1, min(0.9, win_chance))
        
        victory = random.random() < win_chance
        
        # Oblicz straty
        base_casualties = random.randint(10, 50)
        if victory:
            our_casualties = int(base_casualties * 0.3)
            enemy_casualties = int(base_casualties * 1.2)
        else:
            our_casualties = int(base_casualties * 1.2)
            enemy_casualties = int(base_casualties * 0.3)
        
        self.casualties_us += our_casualties
        self.casualties_enemy += enemy_casualties
        
        # Zwiększ wyczerpanie wojną
        self.war_exhaustion = min(1.0, self.war_exhaustion + 0.05)
        
        # Koszt ekonomiczny
        battle_cost = random.randint(1000, 5000)
        self.economic_cost += battle_cost
        
        return {
            'victory': victory,
            'our_casualties': our_casualties,
            'enemy_casualties': enemy_casualties,
            'cost': battle_cost,
            'war_exhaustion': self.war_exhaustion
        }

class DiplomaticCity:
    """Rozszerzona klasa miasta z systemem dyplomatycznym"""
    
    def __init__(self, city_id: str, name: str, specialization=None):
        self.city_id = city_id
        self.name = name
        self.specialization = specialization
        self.relationship_points = 0  # -100 do +100
        self.relationship_status = RelationshipStatus.NEUTRAL
        self.trade_volume = 0.0
        self.reputation = 50  # 0-100
        self.military_strength = random.randint(500, 1500)
        self.economic_power = random.randint(1000, 5000)
        self.population = random.randint(10000, 100000)
        self.last_interaction_turn = 0
        
        # Dyplomatyczne
        self.alliance_expires_turn = None
        self.at_war = False
        self.war_started_turn = None
        self.peace_treaty_expires = None
        self.trade_embargo = False
        
        # Preferencje dyplomatyczne
        self.aggression_level = random.uniform(0.2, 0.8)  # Skłonność do konfliktów
        self.cooperation_level = random.uniform(0.3, 0.9)  # Skłonność do współpracy
        self.economic_focus = random.uniform(0.4, 1.0)     # Priorytet ekonomii
        
    def update_relationship(self, points_change: int, turn: int):
        """Aktualizuje relacje z miastem"""
        self.relationship_points = max(-100, min(100, self.relationship_points + points_change))
        self.last_interaction_turn = turn
        
        # Aktualizuj status relacji
        if self.at_war:
            self.relationship_status = RelationshipStatus.AT_WAR
        elif self.relationship_points >= 80:
            self.relationship_status = RelationshipStatus.ALLIED
        elif self.relationship_points >= 40:
            self.relationship_status = RelationshipStatus.FRIENDLY
        elif self.relationship_points <= -40:
            self.relationship_status = RelationshipStatus.HOSTILE
        else:
            self.relationship_status = RelationshipStatus.NEUTRAL
    
    def can_declare_war(self) -> bool:
        """Sprawdza czy można wypowiedzieć wojnę"""
        return (not self.at_war and 
                self.relationship_status != RelationshipStatus.ALLIED and
                self.alliance_expires_turn is None)
    
    def get_war_strength(self) -> float:
        """Oblicza siłę militarną miasta"""
        base_strength = self.military_strength
        economic_bonus = self.economic_power * 0.1
        population_bonus = self.population * 0.001
        return base_strength + economic_bonus + population_bonus

class DiplomacyManager:
    """Menedżer systemu dyplomatycznego"""
    
    def __init__(self):
        self.cities: Dict[str, DiplomaticCity] = {}
        self.active_missions: List[DiplomaticMission] = []
        self.mission_history: List[DiplomaticMission] = []
        self.active_wars: List[War] = []
        self.war_history: List[War] = []
        self.diplomatic_reputation = 50  # Globalna reputacja gracza
        self.peace_treaties: Dict[str, int] = {}  # miasto -> tura wygaśnięcia
        
        self._initialize_cities()
    
    def _initialize_cities(self):
        """Inicjalizuje miasta dyplomatyczne"""
        cities_data = [
            ("agropolis", "Agropolis", "agricultural"),
            ("steelburg", "Steelburg", "industrial"),
            ("energyville", "Energyville", "energy"),
            ("luxuria", "Luxuria", "luxury"),
            ("techcity", "TechCity", "technology"),
            ("servicetown", "ServiceTown", "services"),
            ("militaria", "Militaria", "military"),
            ("culturalis", "Culturalis", "cultural")
        ]
        
        for city_id, name, specialization in cities_data:
            self.cities[city_id] = DiplomaticCity(city_id, name, specialization)
    
    def create_mission(self, target_city: str, mission_type: MissionType, 
                      investment: float = 0) -> Optional[DiplomaticMission]:
        """Tworzy nową misję dyplomatyczną"""
        
        if target_city not in self.cities:
            return None
        
        city = self.cities[target_city]
        
        # Sprawdź czy można wysłać misję
        if city.at_war and mission_type != MissionType.PEACE_TREATY:
            return None
        
        # Oblicz parametry misji
        base_costs = {
            MissionType.TRADE_AGREEMENT: 2000,
            MissionType.ALLIANCE_PROPOSAL: 5000,
            MissionType.PEACE_TREATY: 3000,
            MissionType.SPY_MISSION: 1500,
            MissionType.CULTURAL_EXCHANGE: 1000,
            MissionType.ECONOMIC_AID: 4000,
            MissionType.MILITARY_SUPPORT: 6000
        }
        
        base_durations = {
            MissionType.TRADE_AGREEMENT: 3,
            MissionType.ALLIANCE_PROPOSAL: 5,
            MissionType.PEACE_TREATY: 4,
            MissionType.SPY_MISSION: 2,
            MissionType.CULTURAL_EXCHANGE: 4,
            MissionType.ECONOMIC_AID: 3,
            MissionType.MILITARY_SUPPORT: 6
        }
        
        base_success_rates = {
            MissionType.TRADE_AGREEMENT: 0.7,
            MissionType.ALLIANCE_PROPOSAL: 0.4,
            MissionType.PEACE_TREATY: 0.6,
            MissionType.SPY_MISSION: 0.3,
            MissionType.CULTURAL_EXCHANGE: 0.8,
            MissionType.ECONOMIC_AID: 0.9,
            MissionType.MILITARY_SUPPORT: 0.5
        }
        
        cost = base_costs[mission_type] + investment
        duration = base_durations[mission_type]
        success_chance = base_success_rates[mission_type]
        
        # Inwestycja zwiększa szanse sukcesu
        if investment > 0:
            success_chance += min(0.3, investment / 10000)
        
        # Generuj nagrody i kary
        rewards, penalties = self._generate_mission_outcomes(mission_type, city, investment)
        
        mission = DiplomaticMission(
            id=f"mission_{len(self.active_missions)}_{target_city}",
            target_city=target_city,
            mission_type=mission_type,
            status=MissionStatus.ACTIVE,
            cost=cost,
            duration_turns=duration,
            remaining_turns=duration,
            success_chance=success_chance,
            rewards=rewards,
            penalties=penalties,
            started_turn=0,  # Będzie ustawione przy starcie
            description=self._get_mission_description(mission_type, city.name)
        )
        
        return mission
    
    def _generate_mission_outcomes(self, mission_type: MissionType, 
                                 city: DiplomaticCity, investment: float) -> Tuple[Dict, Dict]:
        """Generuje możliwe wyniki misji"""
        rewards = {}
        penalties = {}
        
        if mission_type == MissionType.TRADE_AGREEMENT:
            rewards = {
                'relationship_points': 20,
                'trade_bonus': 0.2,
                'money': investment * 0.5
            }
            penalties = {
                'relationship_points': -5,
                'reputation': -2
            }
        
        elif mission_type == MissionType.ALLIANCE_PROPOSAL:
            rewards = {
                'relationship_points': 40,
                'alliance_duration': 50,  # tur
                'military_support': city.military_strength * 0.1,
                'trade_bonus': 0.3
            }
            penalties = {
                'relationship_points': -15,
                'reputation': -5
            }
        
        elif mission_type == MissionType.PEACE_TREATY:
            rewards = {
                'end_war': True,
                'relationship_points': 30,
                'peace_duration': 30  # tur
            }
            penalties = {
                'relationship_points': -10,
                'reputation': -3,
                'money': -5000  # Reparacje
            }
        
        elif mission_type == MissionType.SPY_MISSION:
            rewards = {
                'intelligence': True,
                'enemy_weakness': True,
                'technology_steal': 0.1
            }
            penalties = {
                'relationship_points': -30,
                'reputation': -10,
                'war_risk': 0.3
            }
        
        elif mission_type == MissionType.CULTURAL_EXCHANGE:
            rewards = {
                'relationship_points': 15,
                'happiness_bonus': 5,
                'tourism_income': 1000
            }
            penalties = {
                'relationship_points': -3
            }
        
        elif mission_type == MissionType.ECONOMIC_AID:
            rewards = {
                'relationship_points': 25,
                'reputation': 5,
                'trade_bonus': 0.15
            }
            penalties = {
                'money': -investment,
                'relationship_points': -5
            }
        
        elif mission_type == MissionType.MILITARY_SUPPORT:
            rewards = {
                'relationship_points': 30,
                'military_alliance': True,
                'defense_bonus': 0.2
            }
            penalties = {
                'relationship_points': -10,
                'money': -investment * 0.5
            }
        
        return rewards, penalties
    
    def _get_mission_description(self, mission_type: MissionType, city_name: str) -> str:
        """Generuje opis misji"""
        descriptions = {
            MissionType.TRADE_AGREEMENT: f"Negocjuj korzystne umowy handlowe z {city_name}",
            MissionType.ALLIANCE_PROPOSAL: f"Zaproponuj sojusz militarny z {city_name}",
            MissionType.PEACE_TREATY: f"Wynegocjuj traktat pokojowy z {city_name}",
            MissionType.SPY_MISSION: f"Przeprowadź tajną misję wywiadowczą w {city_name}",
            MissionType.CULTURAL_EXCHANGE: f"Zorganizuj wymianę kulturalną z {city_name}",
            MissionType.ECONOMIC_AID: f"Udziel pomocy ekonomicznej dla {city_name}",
            MissionType.MILITARY_SUPPORT: f"Zaoferuj wsparcie militarne dla {city_name}"
        }
        return descriptions.get(mission_type, f"Misja dyplomatyczna do {city_name}")
    
    def start_mission(self, mission: DiplomaticMission, turn: int, economy) -> Tuple[bool, str]:
        """Rozpoczyna misję dyplomatyczną"""
        
        # Sprawdź czy można pokryć koszty
        if not economy.can_afford(mission.cost):
            return False, "Niewystarczające środki na misję"
        
        # Pobierz opłatę
        economy.spend_money(mission.cost)
        
        # Ustaw turę startu
        mission.started_turn = turn
        
        # Dodaj do aktywnych misji
        self.active_missions.append(mission)
        
        return True, f"Misja {mission.mission_type.value} do {mission.target_city} rozpoczęta"
    
    def update_missions(self, turn: int) -> List[Dict]:
        """Aktualizuje aktywne misje"""
        completed_missions = []
        results = []
        
        for mission in self.active_missions:
            mission.remaining_turns -= 1
            
            if mission.remaining_turns <= 0:
                # Misja zakończona - sprawdź wynik
                city = self.cities[mission.target_city]
                success = mission.calculate_success(city.relationship_points, self.diplomatic_reputation)
                
                if success:
                    mission.status = MissionStatus.COMPLETED
                    self._apply_mission_rewards(mission, city, turn)
                    results.append({
                        'mission': mission,
                        'success': True,
                        'message': f"Misja {mission.mission_type.value} do {city.name} zakończona sukcesem!"
                    })
                else:
                    mission.status = MissionStatus.FAILED
                    self._apply_mission_penalties(mission, city, turn)
                    results.append({
                        'mission': mission,
                        'success': False,
                        'message': f"Misja {mission.mission_type.value} do {city.name} zakończona niepowodzeniem."
                    })
                
                completed_missions.append(mission)
                self.mission_history.append(mission)
        
        # Usuń zakończone misje
        for mission in completed_missions:
            self.active_missions.remove(mission)
        
        return results
    
    def _apply_mission_rewards(self, mission: DiplomaticMission, city: DiplomaticCity, turn: int):
        """Aplikuje nagrody za udaną misję"""
        for reward_type, value in mission.rewards.items():
            if reward_type == 'relationship_points':
                city.update_relationship(int(value), turn)
            elif reward_type == 'alliance_duration':
                city.alliance_expires_turn = turn + int(value)
                city.relationship_status = RelationshipStatus.ALLIED
            elif reward_type == 'end_war':
                self._end_war(city.city_id, turn)
            elif reward_type == 'peace_duration':
                self.peace_treaties[city.city_id] = turn + int(value)
            elif reward_type == 'reputation':
                self.diplomatic_reputation = min(100, self.diplomatic_reputation + int(value))
    
    def _apply_mission_penalties(self, mission: DiplomaticMission, city: DiplomaticCity, turn: int):
        """Aplikuje kary za nieudaną misję"""
        for penalty_type, value in mission.penalties.items():
            if penalty_type == 'relationship_points':
                city.update_relationship(int(value), turn)
            elif penalty_type == 'reputation':
                self.diplomatic_reputation = max(0, self.diplomatic_reputation + int(value))
            elif penalty_type == 'war_risk':
                if random.random() < value:
                    self._declare_war(city.city_id, WarType.IDEOLOGICAL, turn)
    
    def declare_war(self, target_city: str, war_type: WarType, turn: int) -> Tuple[bool, str]:
        """Wypowiada wojnę miastu"""
        if target_city not in self.cities:
            return False, "Nieznane miasto"
        
        city = self.cities[target_city]
        
        if not city.can_declare_war():
            return False, "Nie można wypowiedzieć wojny temu miastu"
        
        return self._declare_war(target_city, war_type, turn)
    
    def _declare_war(self, target_city: str, war_type: WarType, turn: int) -> Tuple[bool, str]:
        """Wewnętrzna metoda wypowiadania wojny"""
        city = self.cities[target_city]
        
        # Utwórz wojnę
        war = War(
            id=f"war_{turn}_{target_city}",
            enemy_city=target_city,
            war_type=war_type,
            started_turn=turn,
            duration_turns=0,
            our_strength=1000,  # Bazowa siła gracza
            enemy_strength=city.get_war_strength(),
            casualties_us=0,
            casualties_enemy=0,
            economic_cost=0,
            war_exhaustion=0.0
        )
        
        self.active_wars.append(war)
        
        # Aktualizuj relacje
        city.at_war = True
        city.war_started_turn = turn
        city.update_relationship(-50, turn)
        
        # Wpływ na reputację
        self.diplomatic_reputation -= 10
        
        return True, f"Wojna z {city.name} została wypowiedziana!"
    
    def _end_war(self, target_city: str, turn: int):
        """Kończy wojnę z miastem"""
        city = self.cities[target_city]
        city.at_war = False
        city.war_started_turn = None
        
        # Znajdź i zakończ wojnę
        for war in self.active_wars:
            if war.enemy_city == target_city and war.active:
                war.active = False
                war.duration_turns = turn - war.started_turn
                self.war_history.append(war)
                self.active_wars.remove(war)
                break
    
    def process_wars(self, turn: int) -> List[Dict]:
        """Przetwarza aktywne wojny"""
        war_results = []
        
        for war in self.active_wars:
            if war.active:
                # Przeprowadź bitwę co kilka tur
                if (turn - war.started_turn) % 3 == 0:
                    battle_result = war.calculate_battle_outcome()
                    war_results.append({
                        'war': war,
                        'battle_result': battle_result,
                        'city_name': self.cities[war.enemy_city].name
                    })
                
                # Sprawdź warunki zakończenia wojny
                if war.war_exhaustion > 0.8 or war.duration_turns > 50:
                    # Automatyczne zakończenie wojny
                    self._end_war(war.enemy_city, turn)
                    war_results.append({
                        'war': war,
                        'ended': True,
                        'reason': 'exhaustion' if war.war_exhaustion > 0.8 else 'duration'
                    })
        
        return war_results
    
    def propose_peace(self, target_city: str, terms: Dict, turn: int) -> Tuple[bool, str]:
        """Proponuje pokój"""
        if target_city not in self.cities:
            return False, "Nieznane miasto"
        
        city = self.cities[target_city]
        
        if not city.at_war:
            return False, "Nie jesteś w stanie wojny z tym miastem"
        
        # Oblicz szanse na przyjęcie pokoju
        base_chance = 0.3
        
        # Modyfikatory
        war = next((w for w in self.active_wars if w.enemy_city == target_city), None)
        if war:
            if war.war_exhaustion > 0.5:
                base_chance += 0.3
            if war.casualties_enemy > war.casualties_us * 1.5:
                base_chance += 0.2
        
        # Warunki pokoju
        reparations = terms.get('reparations', 0)
        if reparations > 0:
            base_chance -= 0.2
        
        territory = terms.get('territory', False)
        if territory:
            base_chance -= 0.3
        
        # Sprawdź czy pokój zostanie przyjęty
        if random.random() < base_chance:
            self._end_war(target_city, turn)
            city.update_relationship(20, turn)
            return True, f"Pokój z {city.name} został zawarty"
        else:
            city.update_relationship(-10, turn)
            return False, f"{city.name} odrzuciło propozycję pokoju"
    
    def get_diplomatic_summary(self) -> Dict:
        """Zwraca podsumowanie dyplomatyczne"""
        return {
            'reputation': self.diplomatic_reputation,
            'active_missions': len(self.active_missions),
            'active_wars': len(self.active_wars),
            'allies': len([c for c in self.cities.values() if c.relationship_status == RelationshipStatus.ALLIED]),
            'enemies': len([c for c in self.cities.values() if c.relationship_status == RelationshipStatus.HOSTILE]),
            'neutral': len([c for c in self.cities.values() if c.relationship_status == RelationshipStatus.NEUTRAL]),
            'peace_treaties': len(self.peace_treaties)
        }
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan do słownika"""
        return {
            'diplomatic_reputation': self.diplomatic_reputation,
            'cities': {
                city_id: {
                    'relationship_points': city.relationship_points,
                    'relationship_status': city.relationship_status.value,
                    'trade_volume': city.trade_volume,
                    'reputation': city.reputation,
                    'at_war': city.at_war,
                    'alliance_expires_turn': city.alliance_expires_turn,
                    'last_interaction_turn': city.last_interaction_turn
                }
                for city_id, city in self.cities.items()
            },
            'peace_treaties': self.peace_treaties,
            'active_wars': [{
                'id': war.id,
                'enemy_city': war.enemy_city,
                'war_type': war.war_type.value,
                'started_turn': war.started_turn,
                'casualties_us': war.casualties_us,
                'casualties_enemy': war.casualties_enemy,
                'economic_cost': war.economic_cost,
                'war_exhaustion': war.war_exhaustion
            } for war in self.active_wars]
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan ze słownika"""
        self.diplomatic_reputation = data.get('diplomatic_reputation', 50)
        self.peace_treaties = data.get('peace_treaties', {})
        
        # Wczytaj miasta
        cities_data = data.get('cities', {})
        for city_id, city_data in cities_data.items():
            if city_id in self.cities:
                city = self.cities[city_id]
                city.relationship_points = city_data.get('relationship_points', 0)
                city.relationship_status = RelationshipStatus(city_data.get('relationship_status', 'neutral'))
                city.trade_volume = city_data.get('trade_volume', 0.0)
                city.reputation = city_data.get('reputation', 50)
                city.at_war = city_data.get('at_war', False)
                city.alliance_expires_turn = city_data.get('alliance_expires_turn')
                city.last_interaction_turn = city_data.get('last_interaction_turn', 0) 