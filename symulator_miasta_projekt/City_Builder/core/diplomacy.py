"""
Rozszerzony system dyplomatyczny dla City Builder
Implementuje wojny, sojusze, misje dyplomatyczne i zaawansowane relacje
"""
from enum import Enum  # Import klasy Enum do definiowania enumeracji (wyliczeń)
from dataclasses import dataclass  # Import dekoratora dataclass do prostego tworzenia klas danych
from typing import Dict, List, Optional, Tuple  # Import typów do podpowiedzi typowania
import random  # Import modułu random do losowania
import math  # Import modułu math do operacji matematycznych
from datetime import datetime  # Import klasy datetime do obsługi dat i czasu

# === ENUMY OKREŚLAJĄCE STANY I TYPY W SYSTEMIE DYPLOMACJI ===
class RelationshipStatus(Enum):
    HOSTILE = "hostile"  # Wrogi
    NEUTRAL = "neutral"  # Neutralny
    FRIENDLY = "friendly"  # Przyjazny
    ALLIED = "allied"  # Sojusznik
    AT_WAR = "at_war"  # W stanie wojny

class MissionType(Enum):
    TRADE_AGREEMENT = "trade_agreement"  # Umowa handlowa
    ALLIANCE_PROPOSAL = "alliance_proposal"  # Propozycja sojuszu
    PEACE_TREATY = "peace_treaty"  # Traktat pokojowy
    SPY_MISSION = "spy_mission"  # Misja szpiegowska
    CULTURAL_EXCHANGE = "cultural_exchange"  # Wymiana kulturalna
    ECONOMIC_AID = "economic_aid"  # Pomoc ekonomiczna
    MILITARY_SUPPORT = "military_support"  # Wsparcie militarne

class MissionStatus(Enum):
    ACTIVE = "active"  # Aktywna
    COMPLETED = "completed"  # Zakończona
    FAILED = "failed"  # Nieudana
    CANCELLED = "cancelled"  # Anulowana

class WarType(Enum):
    TRADE_WAR = "trade_war"  # Wojna handlowa
    TERRITORIAL = "territorial"  # Wojna terytorialna
    RESOURCE_CONFLICT = "resource_conflict"  # Konflikt o zasoby
    IDEOLOGICAL = "ideological"  # Konflikt ideologiczny

# === KLASY DANYCH DLA MISJI I WOJEN ===
@dataclass
class DiplomaticMission:
    """
    Reprezentuje misję dyplomatyczną wysyłaną do innego miasta.
    Zawiera wszystkie parametry misji, jej status, koszty, nagrody i kary.
    """
    id: str  # Unikalny identyfikator misji
    target_city: str  # Nazwa miasta docelowego
    mission_type: MissionType  # Typ misji (enum)
    status: MissionStatus  # Status misji (enum)
    cost: float  # Koszt misji
    duration_turns: int  # Czas trwania misji w turach
    remaining_turns: int  # Pozostała liczba tur do zakończenia
    success_chance: float  # Szansa powodzenia (0-1)
    rewards: Dict[str, float]  # Słownik nagród za sukces
    penalties: Dict[str, float]  # Słownik kar za porażkę
    started_turn: int  # Numer tury rozpoczęcia
    description: str  # Opis misji
    
    def calculate_success(self, relationship_points: int, city_reputation: int) -> bool:
        """
        Oblicza czy misja zakończy się sukcesem na podstawie szansy bazowej,
        relacji z miastem i reputacji gracza.
        """
        base_chance = self.success_chance  # Bazowa szansa sukcesu
        # Modyfikator za relacje
        if relationship_points > 50:
            base_chance += 0.2  # Lepsze relacje zwiększają szansę
        elif relationship_points < -50:
            base_chance -= 0.3  # Bardzo złe relacje zmniejszają szansę
        # Modyfikator za reputację gracza
        reputation_modifier = (city_reputation - 50) / 100
        base_chance += reputation_modifier * 0.1
        # Modyfikator za typ misji (trudniejsze misje mają niższą szansę)
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
        # Losowy rzut - czy misja się powiodła
        return random.random() < max(0.1, min(0.9, base_chance))

@dataclass
class War:
    """
    Reprezentuje wojnę pomiędzy miastami.
    Przechowuje wszystkie dane o konflikcie, jego przebiegu i skutkach.
    """
    id: str  # Unikalny identyfikator wojny
    enemy_city: str  # Nazwa miasta przeciwnika
    war_type: WarType  # Typ wojny (enum)
    started_turn: int  # Tura rozpoczęcia wojny
    duration_turns: int  # Liczba tur trwania wojny
    our_strength: float  # Siła militarna gracza
    enemy_strength: float  # Siła militarna przeciwnika
    casualties_us: int  # Straty własne
    casualties_enemy: int  # Straty przeciwnika
    economic_cost: float  # Koszt ekonomiczny wojny
    war_exhaustion: float  # Wyczerpanie wojną (0-1)
    active: bool = True  # Czy wojna jest aktywna
    
    def calculate_battle_outcome(self) -> Dict:
        """
        Oblicza wynik bitwy na podstawie sił stron i losowości.
        Zwraca słownik z informacjami o wyniku bitwy.
        """
        strength_ratio = self.our_strength / max(self.enemy_strength, 1)  # Stosunek sił
        win_chance = 0.5 + (strength_ratio - 1) * 0.2  # Bazowa szansa wygranej
        win_chance = max(0.1, min(0.9, win_chance))  # Ograniczenie szansy do 10-90%
        victory = random.random() < win_chance  # Czy wygraliśmy?
        base_casualties = random.randint(10, 50)  # Bazowe straty
        if victory:
            our_casualties = int(base_casualties * 0.3)  # Mniejsze straty własne
            enemy_casualties = int(base_casualties * 1.2)  # Większe straty przeciwnika
        else:
            our_casualties = int(base_casualties * 1.2)  # Większe straty własne
            enemy_casualties = int(base_casualties * 0.3)  # Mniejsze straty przeciwnika
        self.casualties_us += our_casualties  # Dodaj straty do sumy
        self.casualties_enemy += enemy_casualties
        self.war_exhaustion = min(1.0, self.war_exhaustion + 0.05)  # Zwiększ wyczerpanie
        battle_cost = random.randint(1000, 5000)  # Koszt bitwy
        self.economic_cost += battle_cost
        return {
            'victory': victory,  # Czy wygraliśmy bitwę
            'our_casualties': our_casualties,  # Straty własne
            'enemy_casualties': enemy_casualties,  # Straty przeciwnika
            'cost': battle_cost,  # Koszt bitwy
            'war_exhaustion': self.war_exhaustion  # Aktualne wyczerpanie wojną
        }

class DiplomaticCity:
    """
    Rozszerzona klasa miasta z systemem dyplomatycznym.
    Przechowuje wszystkie informacje o relacjach, sile, preferencjach i stanie wojny.
    """
    def __init__(self, city_id: str, name: str, specialization=None):
        self.city_id = city_id  # Unikalny identyfikator miasta
        self.name = name  # Nazwa miasta
        self.specialization = specialization  # Specjalizacja miasta (np. przemysł, kultura)
        self.relationship_points = 0  # Punkty relacji z graczem (-100 do +100)
        self.relationship_status = RelationshipStatus.NEUTRAL  # Status relacji (enum)
        self.trade_volume = 0.0  # Wolumen handlu z miastem
        self.reputation = 50  # Reputacja miasta (0-100)
        self.military_strength = random.randint(500, 1500)  # Siła militarna miasta (losowana)
        self.economic_power = random.randint(1000, 5000)  # Siła ekonomiczna miasta (losowana)
        self.population = random.randint(10000, 100000)  # Populacja miasta (losowana)
        self.last_interaction_turn = 0  # Ostatnia tura interakcji
        # Dyplomatyczne
        self.alliance_expires_turn = None  # Tura wygaśnięcia sojuszu
        self.at_war = False  # Czy miasto jest w stanie wojny
        self.war_started_turn = None  # Tura rozpoczęcia wojny
        self.peace_treaty_expires = None  # Tura wygaśnięcia pokoju
        self.trade_embargo = False  # Czy obowiązuje embargo handlowe
        # Preferencje dyplomatyczne
        self.aggression_level = random.uniform(0.2, 0.8)  # Skłonność do konfliktów (losowana)
        self.cooperation_level = random.uniform(0.3, 0.9)  # Skłonność do współpracy (losowana)
        self.economic_focus = random.uniform(0.4, 1.0)     # Priorytet ekonomii (losowany)

    def update_relationship(self, points_change: int, turn: int):
        """
        Aktualizuje relacje z miastem na podstawie zmiany punktów i ustawia status.
        """
        self.relationship_points = max(-100, min(100, self.relationship_points + points_change))  # Ogranicz do [-100, 100]
        self.last_interaction_turn = turn  # Zapisz turę ostatniej interakcji
        # Ustal status relacji na podstawie punktów i stanu wojny
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
        """
        Sprawdza czy można wypowiedzieć wojnę temu miastu.
        """
        return (not self.at_war and 
                self.relationship_status != RelationshipStatus.ALLIED and
                self.alliance_expires_turn is None)

    def get_war_strength(self) -> float:
        """
        Oblicza siłę militarną miasta na podstawie kilku czynników.
        """
        base_strength = self.military_strength  # Bazowa siła militarna
        economic_bonus = self.economic_power * 0.1  # Premia za ekonomię
        population_bonus = self.population * 0.001  # Premia za populację
        return base_strength + economic_bonus + population_bonus

class DiplomacyManager:
    """
    Menedżer systemu dyplomatycznego.
    Zarządza wszystkimi miastami, misjami, wojnami i reputacją gracza.
    """
    def __init__(self):
        self.cities: Dict[str, DiplomaticCity] = {}  # Słownik miast dyplomatycznych
        self.active_missions: List[DiplomaticMission] = []  # Aktywne misje
        self.mission_history: List[DiplomaticMission] = []  # Historia misji
        self.active_wars: List[War] = []  # Aktywne wojny
        self.war_history: List[War] = []  # Historia wojen
        self.diplomatic_reputation = 50  # Globalna reputacja gracza
        self.peace_treaties: Dict[str, int] = {}  # Słownik: miasto -> tura wygaśnięcia pokoju
        self._initialize_cities()  # Inicjalizacja miast

    def _initialize_cities(self):
        """
        Inicjalizuje miasta dyplomatyczne na podstawie predefiniowanej listy.
        """
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

    def create_mission(self, target_city: str, mission_type: MissionType, investment: float = 0) -> Optional[DiplomaticMission]:
        """
        Tworzy nową misję dyplomatyczną do wybranego miasta.
        Zwraca obiekt misji lub None jeśli nie można utworzyć.
        """
        if target_city not in self.cities:
            return None  # Nieznane miasto
        city = self.cities[target_city]
        # Nie można wysłać misji jeśli trwa wojna (poza pokojem)
        if city.at_war and mission_type != MissionType.PEACE_TREATY:
            return None
        # Ustal bazowe parametry misji
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
        cost = base_costs[mission_type] + investment  # Całkowity koszt
        duration = base_durations[mission_type]  # Czas trwania
        success_chance = base_success_rates[mission_type]  # Bazowa szansa sukcesu
        # Inwestycja zwiększa szansę sukcesu (do +0.3)
        if investment > 0:
            success_chance += min(0.3, investment / 10000)
        # Generuj nagrody i kary
        rewards, penalties = self._generate_mission_outcomes(mission_type, city, investment)
        # Utwórz obiekt misji
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

    def _generate_mission_outcomes(self, mission_type: MissionType, city: DiplomaticCity, investment: float) -> Tuple[Dict, Dict]:
        """
        Generuje słowniki nagród i kar dla danej misji w zależności od typu i inwestycji.
        """
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
        """
        Generuje opis misji na podstawie typu i nazwy miasta.
        """
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
        """
        Rozpoczyna misję dyplomatyczną, pobiera opłatę i dodaje do aktywnych misji.
        """
        if not economy.can_afford(mission.cost):
            return False, "Niewystarczające środki na misję"
        economy.spend_money(mission.cost)  # Pobierz opłatę
        mission.started_turn = turn  # Ustaw turę startu
        self.active_missions.append(mission)  # Dodaj do aktywnych
        return True, f"Misja {mission.mission_type.value} do {mission.target_city} rozpoczęta"

    def update_missions(self, turn: int) -> List[Dict]:
        """
        Aktualizuje aktywne misje, sprawdza ich zakończenie i stosuje nagrody/kary.
        """
        completed_missions = []  # Lista zakończonych misji
        results = []  # Wyniki do zwrócenia
        for mission in self.active_missions:
            mission.remaining_turns -= 1  # Zmniejsz liczbę pozostałych tur
            if mission.remaining_turns <= 0:
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
        for mission in completed_missions:
            self.active_missions.remove(mission)
        return results

    def _apply_mission_rewards(self, mission: DiplomaticMission, city: DiplomaticCity, turn: int):
        """
        Aplikuje nagrody za udaną misję do miasta i reputacji gracza.
        """
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
        """
        Aplikuje kary za nieudaną misję do miasta i reputacji gracza.
        """
        for penalty_type, value in mission.penalties.items():
            if penalty_type == 'relationship_points':
                city.update_relationship(int(value), turn)
            elif penalty_type == 'reputation':
                self.diplomatic_reputation = max(0, self.diplomatic_reputation + int(value))
            elif penalty_type == 'war_risk':
                if random.random() < value:
                    self._declare_war(city.city_id, WarType.IDEOLOGICAL, turn)

    def declare_war(self, target_city: str, war_type: WarType, turn: int) -> Tuple[bool, str]:
        """
        Wypowiada wojnę wybranemu miastu, jeśli to możliwe.
        """
        if target_city not in self.cities:
            return False, "Nieznane miasto"
        city = self.cities[target_city]
        if not city.can_declare_war():
            return False, "Nie można wypowiedzieć wojny temu miastu"
        return self._declare_war(target_city, war_type, turn)

    def _declare_war(self, target_city: str, war_type: WarType, turn: int) -> Tuple[bool, str]:
        """
        Wewnętrzna metoda wypowiadania wojny i tworzenia obiektu wojny.
        """
        city = self.cities[target_city]
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
        city.at_war = True
        city.war_started_turn = turn
        city.update_relationship(-50, turn)
        self.diplomatic_reputation -= 10  # Spadek reputacji
        return True, f"Wojna z {city.name} została wypowiedziana!"

    def _end_war(self, target_city: str, turn: int):
        """
        Kończy wojnę z wybranym miastem i aktualizuje historię.
        """
        city = self.cities[target_city]
        city.at_war = False
        city.war_started_turn = None
        for war in self.active_wars:
            if war.enemy_city == target_city and war.active:
                war.active = False
                war.duration_turns = turn - war.started_turn
                self.war_history.append(war)
                self.active_wars.remove(war)
                break

    def process_wars(self, turn: int) -> List[Dict]:
        """
        Przetwarza aktywne wojny, przeprowadza bitwy i sprawdza warunki zakończenia.
        """
        war_results = []
        for war in self.active_wars:
            if war.active:
                if (turn - war.started_turn) % 3 == 0:
                    battle_result = war.calculate_battle_outcome()
                    war_results.append({
                        'war': war,
                        'battle_result': battle_result,
                        'city_name': self.cities[war.enemy_city].name
                    })
                if war.war_exhaustion > 0.8 or war.duration_turns > 50:
                    self._end_war(war.enemy_city, turn)
                    war_results.append({
                        'war': war,
                        'ended': True,
                        'reason': 'exhaustion' if war.war_exhaustion > 0.8 else 'duration'
                    })
        return war_results

    def propose_peace(self, target_city: str, terms: Dict, turn: int) -> Tuple[bool, str]:
        """
        Proponuje pokój wybranemu miastu na określonych warunkach.
        """
        if target_city not in self.cities:
            return False, "Nieznane miasto"
        city = self.cities[target_city]
        if not city.at_war:
            return False, "Nie jesteś w stanie wojny z tym miastem"
        base_chance = 0.3  # Bazowa szansa na przyjęcie pokoju
        war = next((w for w in self.active_wars if w.enemy_city == target_city), None)
        if war:
            if war.war_exhaustion > 0.5:
                base_chance += 0.3
            if war.casualties_enemy > war.casualties_us * 1.5:
                base_chance += 0.2
        reparations = terms.get('reparations', 0)
        if reparations > 0:
            base_chance -= 0.2
        territory = terms.get('territory', False)
        if territory:
            base_chance -= 0.3
        if random.random() < base_chance:
            self._end_war(target_city, turn)
            city.update_relationship(20, turn)
            return True, f"Pokój z {city.name} został zawarty"
        else:
            city.update_relationship(-10, turn)
            return False, f"{city.name} odrzuciło propozycję pokoju"

    def get_diplomatic_summary(self) -> Dict:
        """
        Zwraca podsumowanie dyplomatyczne gracza i miast.
        """
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
        """
        Zapisuje stan dyplomacji do słownika (do zapisu gry).
        """
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
        """
        Wczytuje stan dyplomacji ze słownika (np. z pliku zapisu).
        """
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