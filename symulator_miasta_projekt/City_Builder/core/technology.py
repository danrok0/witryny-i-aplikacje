"""
System technologii dla City Builder - rozszerzony system badań naukowych.

Implementuje zaawansowane drzewko technologiczne z 25+ technologiami, 
zależnościami między nimi oraz wpływem na rozwój miasta.

Główne funkcje:
- Badanie nowych technologii
- System prerekvizytów (technologie wymagane do odblokowania innych)
- Kategorie technologii (infrastruktura, ekonomia, społeczeństwo, etc.)
- Efekty technologii na miasto (bonusy, nowe budynki)
- Kolejka badań i system punktów badawczych
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

class TechnologyCategory(Enum):
    """
    Kategorie technologii w grze.
    
    Każda kategoria skupia się na innym aspekcie rozwoju miasta:
    """
    INFRASTRUCTURE = "infrastructure"  # infrastruktura - drogi, budynki, transport
    ECONOMY = "economy"               # ekonomia - finanse, handel, przemysł
    SOCIAL = "social"                 # społeczeństwo - edukacja, zdrowie, kultura
    ENVIRONMENT = "environment"       # środowisko - ekologia, energia odnawialna
    MILITARY = "military"             # wojsko - obrona, bezpieczeństwo
    SCIENCE = "science"               # nauka - badania, laboratoria, uniwersytety

@dataclass
class Technology:
    """
    Reprezentuje pojedynczą technologię w drzewku badań.
    
    @dataclass automatycznie generuje konstruktor i inne metody.
    Każda technologia ma:
    - Unikalne ID i nazwę
    - Koszt i czas badania
    - Wymagania (inne technologie potrzebne do odblokowania)
    - Efekty na miasto
    - Lista budynków i technologii które odblokuje
    """
    id: str                           # unikalne ID technologii
    name: str                         # nazwa wyświetlana graczowi
    description: str                  # opis efektów technologii
    category: TechnologyCategory      # kategoria (infrastruktura, ekonomia, etc.)
    cost: int                         # koszt badania w punktach badawczych
    research_time: int                # liczba tur potrzebnych do badania
    prerequisites: List[str]          # lista ID technologii wymaganych
    effects: Dict[str, float]         # efekty technologii (np. {"tax_bonus": 0.1})
    unlocks_buildings: List[str] = None     # budynki odblokowane przez technologię
    unlocks_technologies: List[str] = None  # technologie odblokowane przez tę
    is_researched: bool = False       # czy technologia została już zbadana
    research_progress: int = 0        # aktualny postęp badań (0 do research_time)
    
    def __post_init__(self):
        """
        Metoda wywoływana po inicjalizacji obiektu.
        
        Ustawia puste listy jeśli nie zostały podane, zapobiega błędom
        przy dostępie do list budynków i technologii.
        """
        if self.unlocks_buildings is None:
            self.unlocks_buildings = []   # pusta lista budynków
        if self.unlocks_technologies is None:
            self.unlocks_technologies = [] # pusta lista technologii

class TechnologyManager:
    """
    Menedżer systemu technologii - zarządza badaniami i drzewkiem technologicznym.
    
    Odpowiada za:
    - Przechowywanie wszystkich dostępnych technologii
    - Kolejkę badań (jakie technologie są aktualnie badane)
    - Sprawdzanie prerekvizytów
    - Aktualizację postępu badań co turę
    - Odblokowanie nowych technologii i budynków
    - Zastosowanie efektów technologii na miasto
    """
    
    def __init__(self):
        """
        Konstruktor menedżera technologii.
        
        Inicjalizuje pusty system technologii i wywołuje metodę
        tworzącą wszystkie dostępne technologie.
        """
        self.technologies = {}              # słownik wszystkich technologii {id: Technology}
        self.research_queue = []            # kolejka technologii do zbadania
        self.current_research = None        # aktualnie badana technologia
        self.research_points_per_turn = 1   # punkty badawcze generowane co turę
        self.total_research_investment = 0  # całkowite inwestycje w badania
        
        self._initialize_technologies()     # utwórz wszystkie technologie
    
    def _initialize_technologies(self):
        """
        Inicjalizuje wszystkie dostępne technologie w grze.
        
        Tworzy kompletne drzewko technologiczne z zależnościami między nimi.
        Technologie są podzielone na poziomy (TIER) - od podstawowych do zaawansowanych.
        
        Metoda prywatna (podkreślnik _) - używana tylko wewnątrz klasy.
        """
        
        # TIER 1 - Podstawowe technologie (dostępne od początku gry)
        technologies_data = [
            # === KATEGORIA: INFRASTRUKTURA ===
            {
                "id": "basic_construction",
                "name": "Podstawowe Budownictwo",
                "description": "Ulepszone techniki budowlane zwiększają efektywność budowy o 10%",
                "category": TechnologyCategory.INFRASTRUCTURE,
                "cost": 500,                    # 500 punktów badawczych
                "research_time": 3,             # 3 tury badania
                "prerequisites": [],            # brak wymagań - dostępna od początku
                "effects": {                    # efekty technologii:
                    "construction_cost_reduction": 0.1,  # -10% kosztu budowy
                    "building_efficiency": 0.05          # +5% efektywności budynków
                },
                "unlocks_buildings": ["improved_house"]  # odblokuje ulepszone domy
            },
            {
                "id": "road_engineering",
                "name": "Inżynieria Drogowa",
                "description": "Zaawansowane techniki budowy dróg, mostów i infrastruktury transportowej",
                "category": TechnologyCategory.INFRASTRUCTURE,
                "cost": 800,
                "research_time": 4,
                "prerequisites": ["basic_construction"],  # wymaga podstawowego budownictwa
                "effects": {
                    "traffic_efficiency": 0.2,          # +20% efektywności ruchu
                    "transport_cost_reduction": 0.15    # -15% kosztów transportu
                },
                "unlocks_buildings": ["highway", "bridge"]  # odblokuje autostrady i mosty
            },
            {
                "id": "urban_planning",
                "name": "Planowanie Urbanistyczne",
                "description": "Efektywne planowanie przestrzeni miejskiej i zagospodarowania terenu",
                "category": TechnologyCategory.INFRASTRUCTURE,
                "cost": 1200,
                "research_time": 5,
                "prerequisites": ["road_engineering"],
                "effects": {
                    "city_efficiency": 0.1,      # +10% ogólnej efektywności miasta
                    "happiness_bonus": 0.05      # +5% bonusu do zadowolenia
                },
                "unlocks_buildings": ["city_center", "plaza"]  # centrum miasta i place
            },
            
            # === KATEGORIA: EKONOMIA ===
            {
                "id": "basic_economics",
                "name": "Podstawy Ekonomii",
                "description": "Lepsze zrozumienie mechanizmów ekonomicznych i zarządzania finansami",
                "category": TechnologyCategory.ECONOMY,
                "cost": 600,
                "research_time": 3,
                "prerequisites": [],  # technologia podstawowa
                "effects": {
                    "tax_efficiency": 0.1,    # +10% efektywności poboru podatków
                    "trade_bonus": 0.05       # +5% bonusu do handlu
                },
                "unlocks_buildings": ["bank"]  # odblokuje banki
            },
            {
                "id": "banking",
                "name": "System Bankowy",
                "description": "Rozwój systemu bankowego zwiększa przepływ kapitału w mieście",
                "category": TechnologyCategory.ECONOMY,
                "cost": 1000,
                "research_time": 4,
                "prerequisites": ["basic_economics"],
                "effects": {
                    "interest_rate_reduction": 0.2,  # -20% oprocentowania kredytów
                    "loan_capacity": 0.3             # +30% dostępności kredytów
                },
                "unlocks_buildings": ["central_bank", "stock_exchange"]  # bank centralny, giełda
            },
            {
                "id": "industrialization",
                "name": "Industrializacja",
                "description": "Rozwój przemysłu ciężkiego zwiększa produkcję i tworzy miejsca pracy",
                "category": TechnologyCategory.ECONOMY,
                "cost": 1500,
                "research_time": 6,
                "prerequisites": ["banking", "basic_construction"],  # wymaga 2 technologii
                "effects": {
                    "industrial_efficiency": 0.25,  # +25% efektywności przemysłu
                    "job_creation": 0.2              # +20% tworzenia miejsc pracy
                },
                "unlocks_buildings": ["steel_mill", "chemical_plant"]  # huty, zakłady chemiczne
            },
            
            # === KATEGORIA: SPOŁECZEŃSTWO ===
            {
                "id": "public_education",
                "name": "Edukacja Publiczna",
                "description": "System powszechnej edukacji dla wszystkich mieszkańców miasta",
                "category": TechnologyCategory.SOCIAL,
                "cost": 800,
                "research_time": 4,
                "prerequisites": [],
                "effects": {
                    "education_efficiency": 0.2,  # +20% efektywności edukacji
                    "research_speed": 0.1          # +10% szybkości badań
                },
                "unlocks_buildings": ["public_school", "library"]  # szkoły publiczne, biblioteki
            },
            {
                "id": "healthcare_system",
                "name": "System Opieki Zdrowotnej",
                "description": "Zorganizowana opieka medyczna poprawia zdrowie mieszkańców",
                "category": TechnologyCategory.SOCIAL,
                "cost": 1000,
                "research_time": 5,
                "prerequisites": ["public_education"],
                "effects": {
                    "health_efficiency": 0.25,    # +25% efektywności służby zdrowia
                    "population_growth": 0.1      # +10% wzrostu populacji
                },
                "unlocks_buildings": ["clinic", "pharmacy"]  # kliniki, apteki
            },
            {
                "id": "social_services",
                "name": "Usługi Społeczne",
                "description": "Kompleksowe wsparcie społeczne dla potrzebujących mieszkańców",
                "category": TechnologyCategory.SOCIAL,
                "cost": 1200,
                "research_time": 5,
                "prerequisites": ["healthcare_system"],
                "effects": {
                    "happiness_bonus": 0.15,    # +15% bonusu do zadowolenia
                    "crime_reduction": 0.1      # -10% przestępczości
                },
                "unlocks_buildings": ["social_center", "elderly_home"]  # centra społeczne, domy starców
            },
            
            # === KATEGORIA: ŚRODOWISKO ===
            {
                "id": "environmental_awareness",
                "name": "Świadomość Ekologiczna",
                "description": "Podstawowa wiedza o ochronie środowiska i zrównoważonym rozwoju",
                "category": TechnologyCategory.ENVIRONMENT,
                "cost": 700,
                "research_time": 3,
                "prerequisites": [],
                "effects": {
                    "pollution_reduction": 0.1,  # -10% zanieczyszczeń
                    "green_bonus": 0.05          # +5% bonusu ekologicznego
                },
                "unlocks_buildings": ["recycling_center"]  # centra recyklingu
            },
            {
                "id": "renewable_energy",
                "name": "Energia Odnawialna",
                "description": "Czyste źródła energii: panele słoneczne, turbiny wiatrowe",
                "category": TechnologyCategory.ENVIRONMENT,
                "cost": 1500,
                "research_time": 6,
                "prerequisites": ["environmental_awareness", "basic_construction"],
                "effects": {
                    "energy_efficiency": 0.3,       # +30% efektywności energetycznej
                    "pollution_reduction": 0.2      # -20% zanieczyszczeń
                },
                "unlocks_buildings": ["solar_plant", "wind_farm"]  # elektrownie słoneczne, farmy wiatrowe
            },
            {
                "id": "green_technology",
                "name": "Zielone Technologie",
                "description": "Zaawansowane technologie ekologiczne i zrównoważone budownictwo",
                "category": TechnologyCategory.ENVIRONMENT,
                "cost": 2000,
                "research_time": 8,
                "prerequisites": ["renewable_energy"],
                "effects": {
                    "eco_efficiency": 0.25,         # +25% efektywności ekologicznej
                    "sustainability_bonus": 0.2     # +20% bonusu zrównoważoności
                },
                "unlocks_buildings": ["eco_district", "green_skyscraper"]  # dzielnice eko, zielone wieżowce
            },
            
            # === KATEGORIA: NAUKA ===
            {
                "id": "scientific_method",
                "name": "Metoda Naukowa",
                "description": "Systematyczne podejście do badań",
                "category": TechnologyCategory.SCIENCE,
                "cost": 1000,
                "research_time": 4,
                "prerequisites": ["public_education"],
                "effects": {"research_speed": 0.2, "technology_cost_reduction": 0.1},
                "unlocks_buildings": ["research_lab"]
            },
            {
                "id": "advanced_materials",
                "name": "Zaawansowane Materiały",
                "description": "Nowe materiały budowlane i przemysłowe",
                "category": TechnologyCategory.SCIENCE,
                "cost": 1800,
                "research_time": 7,
                "prerequisites": ["scientific_method", "industrialization"],
                "effects": {"construction_efficiency": 0.2, "durability_bonus": 0.15},
                "unlocks_buildings": ["high_tech_factory", "space_center"]
            },
            {
                "id": "information_technology",
                "name": "Technologie Informacyjne",
                "description": "Komputery i systemy informatyczne",
                "category": TechnologyCategory.SCIENCE,
                "cost": 2200,
                "research_time": 8,
                "prerequisites": ["advanced_materials"],
                "effects": {"efficiency_bonus": 0.15, "automation": 0.1},
                "unlocks_buildings": ["tech_park", "data_center"]
            },
            
            # === KATEGORIA: BEZPIECZEŃSTWO ===
            {
                "id": "law_enforcement",
                "name": "Egzekwowanie Prawa",
                "description": "Profesjonalne służby porządkowe",
                "category": TechnologyCategory.MILITARY,
                "cost": 900,
                "research_time": 4,
                "prerequisites": [],
                "effects": {"crime_reduction": 0.2, "safety_bonus": 0.15},
                "unlocks_buildings": ["police_station", "courthouse"]
            },
            {
                "id": "emergency_services",
                "name": "Służby Ratunkowe",
                "description": "Zorganizowane służby ratownicze",
                "category": TechnologyCategory.MILITARY,
                "cost": 1100,
                "research_time": 5,
                "prerequisites": ["law_enforcement"],
                "effects": {"disaster_resistance": 0.2, "emergency_response": 0.25},
                "unlocks_buildings": ["emergency_center", "disaster_shelter"]
            },
            {
                "id": "civil_defense",
                "name": "Obrona Cywilna",
                "description": "Kompleksowy system obrony miasta",
                "category": TechnologyCategory.MILITARY,
                "cost": 1600,
                "research_time": 6,
                "prerequisites": ["emergency_services"],
                "effects": {"city_defense": 0.3, "crisis_management": 0.2},
                "unlocks_buildings": ["command_center", "bunker"]
            },
            
            # === TIER 2 - Zaawansowane technologie ===
            {
                "id": "smart_city",
                "name": "Inteligentne Miasto",
                "description": "Zintegrowane systemy zarządzania miastem",
                "category": TechnologyCategory.SCIENCE,
                "cost": 3000,
                "research_time": 10,
                "prerequisites": ["information_technology", "urban_planning"],
                "effects": {"city_efficiency": 0.25, "automation": 0.2},
                "unlocks_buildings": ["smart_grid", "automated_transport"]
            },
            {
                "id": "biotechnology",
                "name": "Biotechnologia",
                "description": "Zaawansowane technologie biologiczne",
                "category": TechnologyCategory.SCIENCE,
                "cost": 2800,
                "research_time": 9,
                "prerequisites": ["advanced_materials", "healthcare_system"],
                "effects": {"health_efficiency": 0.3, "food_production": 0.2},
                "unlocks_buildings": ["biotech_lab", "vertical_farm"]
            },
            {
                "id": "fusion_power",
                "name": "Energia Fuzji",
                "description": "Czysta i nieograniczona energia",
                "category": TechnologyCategory.ENVIRONMENT,
                "cost": 4000,
                "research_time": 12,
                "prerequisites": ["green_technology", "advanced_materials"],
                "effects": {"energy_efficiency": 0.5, "pollution_reduction": 0.4},
                "unlocks_buildings": ["fusion_reactor"]
            },
            {
                "id": "space_technology",
                "name": "Technologie Kosmiczne",
                "description": "Eksploracja i wykorzystanie kosmosu",
                "category": TechnologyCategory.SCIENCE,
                "cost": 5000,
                "research_time": 15,
                "prerequisites": ["fusion_power", "smart_city"],
                "effects": {"prestige_bonus": 0.3, "research_speed": 0.3},
                "unlocks_buildings": ["space_elevator", "orbital_station"]
            }
        ]
        
        # Tworzenie obiektów technologii
        for tech_data in technologies_data:
            tech = Technology(**tech_data)
            self.technologies[tech.id] = tech
    
    def can_research(self, tech_id: str) -> tuple[bool, str]:
        """Sprawdza czy można rozpocząć badanie technologii"""
        if tech_id not in self.technologies:
            return False, "Nieznana technologia"
        
        tech = self.technologies[tech_id]
        
        if tech.is_researched:
            return False, "Technologia już zbadana"
        
        if self.current_research:
            return False, "Inne badania w toku"
        
        # Sprawdź prerequisity
        for prereq in tech.prerequisites:
            if not self.technologies[prereq].is_researched:
                return False, f"Wymagana technologia: {self.technologies[prereq].name}"
        
        return True, "OK"
    
    def start_research(self, tech_id: str, investment: int = 0) -> bool:
        """Rozpoczyna badanie technologii"""
        can_research, reason = self.can_research(tech_id)
        if not can_research:
            return False
        
        self.current_research = tech_id
        self.total_research_investment += investment
        
        # Inwestycja zwiększa szybkość badań
        if investment > 0:
            bonus_points = investment // 1000  # 1 punkt za każde 1000$
            self.research_points_per_turn = 1 + bonus_points
        
        return True
    
    def update_research(self) -> Optional[Technology]:
        """Aktualizuje postęp badań, zwraca ukończoną technologię"""
        if not self.current_research:
            return None
        
        tech = self.technologies[self.current_research]
        tech.research_progress += self.research_points_per_turn
        
        if tech.research_progress >= tech.research_time:
            # Technologia ukończona
            tech.is_researched = True
            completed_tech = tech
            self.current_research = None
            self.research_points_per_turn = 1
            
            return completed_tech
        
        return None
    
    def get_available_technologies(self) -> List[Technology]:
        """Zwraca technologie dostępne do badania"""
        available = []
        for tech in self.technologies.values():
            if not tech.is_researched:
                can_research, _ = self.can_research(tech.id)
                if can_research or not self.current_research:
                    available.append(tech)
        return available
    
    def get_researched_technologies(self) -> List[Technology]:
        """Zwraca zbadane technologie"""
        return [tech for tech in self.technologies.values() if tech.is_researched]
    
    def get_technology_effects(self) -> Dict[str, float]:
        """Zwraca skumulowane efekty wszystkich zbadanych technologii"""
        effects = {}
        for tech in self.get_researched_technologies():
            for effect, value in tech.effects.items():
                effects[effect] = effects.get(effect, 0) + value
        return effects
    
    def get_unlocked_buildings(self) -> List[str]:
        """Zwraca budynki odblokowane przez technologie"""
        buildings = []
        for tech in self.get_researched_technologies():
            buildings.extend(tech.unlocks_buildings)
        return buildings
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan do słownika"""
        return {
            'current_research': self.current_research,
            'research_points_per_turn': self.research_points_per_turn,
            'total_research_investment': self.total_research_investment,
            'technologies': {
                tech_id: {
                    'is_researched': tech.is_researched,
                    'research_progress': tech.research_progress
                }
                for tech_id, tech in self.technologies.items()
            }
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan ze słownika"""
        self.current_research = data.get('current_research')
        self.research_points_per_turn = data.get('research_points_per_turn', 1)
        self.total_research_investment = data.get('total_research_investment', 0)
        
        tech_data = data.get('technologies', {})
        for tech_id, tech_state in tech_data.items():
            if tech_id in self.technologies:
                self.technologies[tech_id].is_researched = tech_state.get('is_researched', False)
                self.technologies[tech_id].research_progress = tech_state.get('research_progress', 0) 