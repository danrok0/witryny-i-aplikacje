"""
System osiągnięć dla City Builder.

Implementuje osiągnięcia za realizację określonych celów rozwojowych:
- Różne kategorie osiągnięć (populacja, ekonomia, budownictwo, etc.)
- Rzadkość osiągnięć (common, uncommon, rare, epic, legendary)
- Punkty za osiągnięcia
- Ukryte osiągnięcia
- System powiadomień
- Statystyki gracza
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json

class AchievementCategory(Enum):
    """
    Kategorie osiągnięć w grze.
    
    Każda kategoria skupia się na innym aspekcie rozgrywki.
    """
    POPULATION = "population"      # osiągnięcia populacyjne
    ECONOMY = "economy"           # osiągnięcia ekonomiczne
    CONSTRUCTION = "construction" # osiągnięcia budowlane
    TECHNOLOGY = "technology"     # osiągnięcia technologiczne
    ENVIRONMENT = "environment"   # osiągnięcia ekologiczne
    TRADE = "trade"               # osiągnięcia handlowe
    SPECIAL = "special"           # osiągnięcia specjalne
    MILESTONE = "milestone"       # kamienie milowe

class AchievementRarity(Enum):
    """
    Rzadkość osiągnięć - określa jak trudne są do zdobycia.
    
    Im rzadsze osiągnięcie, tym więcej punktów i prestiżu daje.
    """
    COMMON = "common"           # częste (łatwe do zdobycia)
    UNCOMMON = "uncommon"       # niezbyt częste
    RARE = "rare"               # rzadkie
    EPIC = "epic"               # epickie (bardzo trudne)
    LEGENDARY = "legendary"     # legendarne (najrzadsze)

@dataclass
class Achievement:
    """
    Reprezentuje pojedyncze osiągnięcie.
    
    @dataclass automatycznie tworzy konstruktor i inne metody.
    """
    id: str                         # unikalne ID osiągnięcia
    name: str                       # nazwa wyświetlana graczowi
    description: str                # opis osiągnięcia
    category: AchievementCategory   # kategoria osiągnięcia
    rarity: AchievementRarity       # rzadkość
    points: int                     # punkty za osiągnięcie
    icon: str = "🏆"               # emoji lub ścieżka do ikony
    hidden: bool = False            # czy osiągnięcie jest ukryte przed odblokowaniem
    
    # Stan osiągnięcia
    is_unlocked: bool = False                 # czy zostało odblokowane
    unlock_date: Optional[datetime] = None    # data odblokowania
    progress: float = 0.0                     # postęp (0.0 - 1.0)
    
    # Warunki odblokowania
    condition_function: Optional[Callable] = None  # funkcja sprawdzająca warunek
    condition_data: Dict[str, Any] = None          # dodatkowe dane dla warunku
    
    def __post_init__(self):
        """
        Metoda wywoływana po inicjalizacji.
        
        Ustawia domyślne wartości jeśli nie zostały podane.
        """
        if self.condition_data is None:
            self.condition_data = {}

class AchievementManager:
    """
    Zarządza systemem osiągnięć.
    
    Funkcje:
    - Sprawdzanie warunków osiągnięć
    - Odblokowanie nowych osiągnięć
    - Śledzenie postępu
    - Powiadomienia o nowych osiągnięciach
    - Statystyki gracza
    """
    
    def __init__(self):
        """
        Konstruktor menedżera osiągnięć.
        
        Inicjalizuje puste kolekcje i tworzy wszystkie osiągnięcia.
        """
        self.achievements = {}              # słownik wszystkich osiągnięć {id: Achievement}
        self.unlocked_achievements = []     # lista odblokowanych osiągnięć
        self.total_points = 0              # łączna liczba zdobytych punktów
        self.notification_queue = []        # kolejka powiadomień o nowych osiągnięciach
        
        self._initialize_achievements()     # utwórz wszystkie osiągnięcia
    
    def _initialize_achievements(self):
        """
        Inicjalizuje wszystkie osiągnięcia w grze.
        
        Tworzy kompletną listę osiągnięć od najprostszych do najbardziej wymagających.
        """
        
        # Lista danych osiągnięć - każde osiągnięcie ma swoje warunki
        achievements_data = [
            # === KATEGORIA: POPULACJA ===
            {
                "id": "first_citizen",
                "name": "Pierwszy Mieszkaniec",
                "description": "Osiągnij populację 1 mieszkańca",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.COMMON,
                "points": 10,
                "icon": "👤",
                "condition": lambda stats: stats.get('population', 0) >= 1
            },
            {
                "id": "small_town",
                "name": "Małe Miasteczko",
                "description": "Osiągnij populację 100 mieszkańców",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.COMMON,
                "points": 25,
                "icon": "🏘️",
                "condition": lambda stats: stats.get('population', 0) >= 100
            },
            {
                "id": "growing_city",
                "name": "Rozwijające się Miasto",
                "description": "Osiągnij populację 500 mieszkańców",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 50,
                "icon": "🏙️",
                "condition": lambda stats: stats.get('population', 0) >= 500
            },
            {
                "id": "big_city",
                "name": "Duże Miasto",
                "description": "Osiągnij populację 1000 mieszkańców",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 75,
                "icon": "🌆",
                "condition": lambda stats: stats.get('population', 0) >= 1000
            },
            {
                "id": "metropolis",
                "name": "Metropolia",
                "description": "Osiągnij populację 5000 mieszkańców",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.RARE,
                "points": 150,
                "icon": "🌃",
                "condition": lambda stats: stats.get('population', 0) >= 5000
            },
            {
                "id": "megacity",
                "name": "Megamiasto",
                "description": "Osiągnij populację 10000 mieszkańców",
                "category": AchievementCategory.POPULATION,
                "rarity": AchievementRarity.EPIC,
                "points": 300,
                "icon": "🏙️",
                "condition": lambda stats: stats.get('population', 0) >= 10000
            },
            
            # === KATEGORIA: EKONOMIA ===
            {
                "id": "first_dollar",
                "name": "Pierwszy Dolar",
                "description": "Zarobić pierwsze pieniądze",
                "category": AchievementCategory.ECONOMY,
                "rarity": AchievementRarity.COMMON,
                "points": 10,
                "icon": "💰",
                "condition": lambda stats: stats.get('money', 0) > 0
            },
            {
                "id": "wealthy",
                "name": "Zamożny",
                "description": "Zgromadź 10,000$",
                "category": AchievementCategory.ECONOMY,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 50,
                "icon": "💵",
                "condition": lambda stats: stats.get('money', 0) >= 10000
            },
            {
                "id": "millionaire",
                "name": "Milioner",
                "description": "Zgromadź 1,000,000$",
                "category": AchievementCategory.ECONOMY,
                "rarity": AchievementRarity.RARE,
                "points": 200,
                "icon": "💎",
                "condition": lambda stats: stats.get('money', 0) >= 1000000
            },
            {
                "id": "tax_master",
                "name": "Mistrz Podatków",
                "description": "Zbierz 100,000$ z podatków",
                "category": AchievementCategory.ECONOMY,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 75,
                "icon": "🏛️",
                "condition": lambda stats: stats.get('total_tax_collected', 0) >= 100000
            },
            {
                "id": "zero_unemployment",
                "name": "Zero Bezrobocia",
                "description": "Osiągnij 0% bezrobocia przez 10 tur",
                "category": AchievementCategory.ECONOMY,
                "rarity": AchievementRarity.RARE,
                "points": 150,
                "icon": "💼",
                "condition": lambda stats: stats.get('unemployment_streak', 0) >= 10
            },
            
            # === KATEGORIA: BUDOWNICTWO ===
            {
                "id": "first_building",
                "name": "Pierwszy Budynek",
                "description": "Postaw pierwszy budynek",
                "category": AchievementCategory.CONSTRUCTION,
                "rarity": AchievementRarity.COMMON,
                "points": 10,
                "icon": "🏠",
                "condition": lambda stats: stats.get('buildings_built', 0) >= 1
            },
            {
                "id": "builder",
                "name": "Budowniczy",
                "description": "Postaw 50 budynków",
                "category": AchievementCategory.CONSTRUCTION,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 50,
                "icon": "🏗️",
                "condition": lambda stats: stats.get('buildings_built', 0) >= 50
            },
            {
                "id": "architect",
                "name": "Architekt",
                "description": "Postaw 200 budynków",
                "category": AchievementCategory.CONSTRUCTION,
                "rarity": AchievementRarity.RARE,
                "points": 100,
                "icon": "📐",
                "condition": lambda stats: stats.get('buildings_built', 0) >= 200
            },
            {
                "id": "master_builder",
                "name": "Mistrz Budowniczy",
                "description": "Postaw po jednym budynku każdego typu",
                "category": AchievementCategory.CONSTRUCTION,
                "rarity": AchievementRarity.EPIC,
                "points": 200,
                "icon": "👷",
                "condition": lambda stats: len(stats.get('building_types_built', [])) >= 20
            },
            {
                "id": "city_planner",
                "name": "Planista Miasta",
                "description": "Zbuduj miasto z idealnym układem dróg",
                "category": AchievementCategory.CONSTRUCTION,
                "rarity": AchievementRarity.RARE,
                "points": 150,
                "icon": "🗺️",
                "condition": lambda stats: stats.get('road_efficiency', 0) >= 0.9
            },
            
            # === KATEGORIA: TECHNOLOGIA ===
            {
                "id": "first_research",
                "name": "Pierwsze Badania",
                "description": "Ukończ pierwszą technologię",
                "category": AchievementCategory.TECHNOLOGY,
                "rarity": AchievementRarity.COMMON,
                "points": 25,
                "icon": "🔬",
                "condition": lambda stats: stats.get('technologies_researched', 0) >= 1
            },
            {
                "id": "tech_enthusiast",
                "name": "Entuzjasta Technologii",
                "description": "Ukończ 10 technologii",
                "category": AchievementCategory.TECHNOLOGY,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 75,
                "icon": "⚗️",
                "condition": lambda stats: stats.get('technologies_researched', 0) >= 10
            },
            {
                "id": "tech_master",
                "name": "Mistrz Technologii",
                "description": "Ukończ wszystkie dostępne technologie",
                "category": AchievementCategory.TECHNOLOGY,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 500,
                "icon": "🚀",
                "condition": lambda stats: stats.get('technologies_researched', 0) >= 25
            },
            
            # === KATEGORIA: ŚRODOWISKO ===
            {
                "id": "green_city",
                "name": "Zielone Miasto",
                "description": "Zbuduj 20 parków",
                "category": AchievementCategory.ENVIRONMENT,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 75,
                "icon": "🌳",
                "condition": lambda stats: stats.get('parks_built', 0) >= 20
            },
            {
                "id": "eco_warrior",
                "name": "Wojownik Ekologii",
                "description": "Osiągnij zerowe zanieczyszczenie",
                "category": AchievementCategory.ENVIRONMENT,
                "rarity": AchievementRarity.RARE,
                "points": 150,
                "icon": "♻️",
                "condition": lambda stats: stats.get('pollution_level', 100) <= 0
            },
            {
                "id": "renewable_energy",
                "name": "Energia Odnawialna",
                "description": "100% energii z odnawialnych źródeł",
                "category": AchievementCategory.ENVIRONMENT,
                "rarity": AchievementRarity.EPIC,
                "points": 250,
                "icon": "⚡",
                "condition": lambda stats: stats.get('renewable_energy_percent', 0) >= 100
            },
            
            # === KATEGORIA: HANDEL ===
            {
                "id": "first_trade",
                "name": "Pierwszy Handel",
                "description": "Zawrzyj pierwszą transakcję handlową",
                "category": AchievementCategory.TRADE,
                "rarity": AchievementRarity.COMMON,
                "points": 25,
                "icon": "🤝",
                "condition": lambda stats: stats.get('trades_completed', 0) >= 1
            },
            {
                "id": "trade_baron",
                "name": "Baron Handlowy",
                "description": "Zawrzyj 100 transakcji handlowych",
                "category": AchievementCategory.TRADE,
                "rarity": AchievementRarity.RARE,
                "points": 150,
                "icon": "💼",
                "condition": lambda stats: stats.get('trades_completed', 0) >= 100
            },
            {
                "id": "diplomatic_relations",
                "name": "Relacje Dyplomatyczne",
                "description": "Osiągnij sojusz ze wszystkimi miastami",
                "category": AchievementCategory.TRADE,
                "rarity": AchievementRarity.EPIC,
                "points": 300,
                "icon": "🤝",
                "condition": lambda stats: stats.get('allied_cities', 0) >= 6
            },
            
            # === KATEGORIA: SPECJALNE ===
            {
                "id": "survivor",
                "name": "Ocalały",
                "description": "Przetrwaj 10 katastrof naturalnych",
                "category": AchievementCategory.SPECIAL,
                "rarity": AchievementRarity.RARE,
                "points": 200,
                "icon": "🌪️",
                "condition": lambda stats: stats.get('disasters_survived', 0) >= 10
            },
            {
                "id": "crisis_manager",
                "name": "Menedżer Kryzysowy",
                "description": "Rozwiąż 50 wydarzeń kryzysowych",
                "category": AchievementCategory.SPECIAL,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 100,
                "icon": "🚨",
                "condition": lambda stats: stats.get('crisis_events_resolved', 0) >= 50
            },
            {
                "id": "perfectionist",
                "name": "Perfekcjonista",
                "description": "Utrzymaj 100% zadowolenia przez 50 tur",
                "category": AchievementCategory.SPECIAL,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 500,
                "icon": "⭐",
                "condition": lambda stats: stats.get('perfect_happiness_streak', 0) >= 50
            },
            
            # === KATEGORIA: KAMIENIE MILOWE ===
            {
                "id": "century_club",
                "name": "Klub Stulecia",
                "description": "Przetrwaj 100 tur",
                "category": AchievementCategory.MILESTONE,
                "rarity": AchievementRarity.UNCOMMON,
                "points": 100,
                "icon": "📅",
                "condition": lambda stats: stats.get('turns_played', 0) >= 100
            },
            {
                "id": "millennium",
                "name": "Milenium",
                "description": "Przetrwaj 1000 tur",
                "category": AchievementCategory.MILESTONE,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 1000,
                "icon": "🏆",
                "condition": lambda stats: stats.get('turns_played', 0) >= 1000
            },
            {
                "id": "achievement_hunter",
                "name": "Łowca Osiągnięć",
                "description": "Odblokuj 50% wszystkich osiągnięć",
                "category": AchievementCategory.MILESTONE,
                "rarity": AchievementRarity.EPIC,
                "points": 250,
                "icon": "🎯",
                "condition": lambda stats: stats.get('achievements_unlocked_percent', 0) >= 50
            },
            {
                "id": "completionist",
                "name": "Kompletista",
                "description": "Odblokuj wszystkie osiągnięcia",
                "category": AchievementCategory.MILESTONE,
                "rarity": AchievementRarity.LEGENDARY,
                "points": 1000,
                "icon": "👑",
                "hidden": True,
                "condition": lambda stats: stats.get('achievements_unlocked_percent', 0) >= 100
            }
        ]
        
        # Tworzenie obiektów osiągnięć
        for ach_data in achievements_data:
            achievement = Achievement(
                id=ach_data["id"],
                name=ach_data["name"],
                description=ach_data["description"],
                category=ach_data["category"],
                rarity=ach_data["rarity"],
                points=ach_data["points"],
                icon=ach_data.get("icon", "🏆"),
                hidden=ach_data.get("hidden", False),
                condition_function=ach_data.get("condition")
            )
            self.achievements[achievement.id] = achievement
    
    def check_achievements(self, game_stats: Dict[str, Any]) -> List[Achievement]:
        """Sprawdza i odblokowuje osiągnięcia na podstawie statystyk gry"""
        newly_unlocked = []
        
        # Dodaj procent odblokowanych osiągnięć do statystyk
        total_achievements = len(self.achievements)
        unlocked_count = len(self.unlocked_achievements)
        game_stats['achievements_unlocked_percent'] = (unlocked_count / total_achievements) * 100 if total_achievements > 0 else 0
        
        for achievement in self.achievements.values():
            if not achievement.is_unlocked and achievement.condition_function:
                try:
                    if achievement.condition_function(game_stats):
                        self._unlock_achievement(achievement)
                        newly_unlocked.append(achievement)
                except Exception as e:
                    print(f"Błąd sprawdzania osiągnięcia {achievement.id}: {e}")
        
        return newly_unlocked
    
    def _unlock_achievement(self, achievement: Achievement):
        """Odblokowuje osiągnięcie"""
        achievement.is_unlocked = True
        achievement.unlock_date = datetime.now()
        achievement.progress = 1.0
        
        self.unlocked_achievements.append(achievement.id)
        self.total_points += achievement.points
        
        # Dodaj do kolejki powiadomień
        self.notification_queue.append({
            'type': 'achievement_unlocked',
            'achievement': achievement,
            'timestamp': achievement.unlock_date
        })
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Zwraca osiągnięcia z danej kategorii"""
        return [ach for ach in self.achievements.values() if ach.category == category]
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Zwraca odblokowane osiągnięcia"""
        return [self.achievements[ach_id] for ach_id in self.unlocked_achievements]
    
    def get_locked_achievements(self, include_hidden: bool = False) -> List[Achievement]:
        """Zwraca zablokowane osiągnięcia"""
        locked = [ach for ach in self.achievements.values() if not ach.is_unlocked]
        if not include_hidden:
            locked = [ach for ach in locked if not ach.hidden]
        return locked
    
    def get_achievement_statistics(self) -> Dict:
        """Zwraca statystyki osiągnięć"""
        total = len(self.achievements)
        unlocked = len(self.unlocked_achievements)
        
        # Statystyki według kategorii
        category_stats = {}
        for category in AchievementCategory:
            category_achievements = self.get_achievements_by_category(category)
            category_unlocked = [ach for ach in category_achievements if ach.is_unlocked]
            category_stats[category.value] = {
                'total': len(category_achievements),
                'unlocked': len(category_unlocked),
                'percentage': (len(category_unlocked) / len(category_achievements)) * 100 if category_achievements else 0
            }
        
        # Statystyki według rzadkości
        rarity_stats = {}
        for rarity in AchievementRarity:
            rarity_achievements = [ach for ach in self.achievements.values() if ach.rarity == rarity]
            rarity_unlocked = [ach for ach in rarity_achievements if ach.is_unlocked]
            rarity_stats[rarity.value] = {
                'total': len(rarity_achievements),
                'unlocked': len(rarity_unlocked),
                'percentage': (len(rarity_unlocked) / len(rarity_achievements)) * 100 if rarity_achievements else 0
            }
        
        return {
            'total_achievements': total,
            'unlocked_achievements': unlocked,
            'completion_percentage': (unlocked / total) * 100 if total > 0 else 0,
            'total_points': self.total_points,
            'category_stats': category_stats,
            'rarity_stats': rarity_stats,
            'recent_unlocks': [
                {
                    'id': ach.id,
                    'name': ach.name,
                    'points': ach.points,
                    'unlock_date': ach.unlock_date.isoformat() if ach.unlock_date else None
                }
                for ach in sorted(self.get_unlocked_achievements(), 
                                key=lambda x: x.unlock_date or datetime.min, reverse=True)[:10]
            ]
        }
    
    def get_notifications(self) -> List[Dict]:
        """Zwraca i czyści kolejkę powiadomień"""
        notifications = self.notification_queue.copy()
        self.notification_queue.clear()
        return notifications
    
    def save_to_dict(self) -> Dict:
        """Zapisuje stan osiągnięć do słownika"""
        return {
            'unlocked_achievements': self.unlocked_achievements,
            'total_points': self.total_points,
            'achievements_data': {
                ach_id: {
                    'is_unlocked': ach.is_unlocked,
                    'unlock_date': ach.unlock_date.isoformat() if ach.unlock_date else None,
                    'progress': ach.progress
                }
                for ach_id, ach in self.achievements.items()
            }
        }
    
    def load_from_dict(self, data: Dict):
        """Wczytuje stan osiągnięć ze słownika"""
        self.unlocked_achievements = data.get('unlocked_achievements', [])
        self.total_points = data.get('total_points', 0)
        
        achievements_data = data.get('achievements_data', {})
        for ach_id, ach_data in achievements_data.items():
            if ach_id in self.achievements:
                achievement = self.achievements[ach_id]
                achievement.is_unlocked = ach_data.get('is_unlocked', False)
                achievement.progress = ach_data.get('progress', 0.0)
                
                unlock_date_str = ach_data.get('unlock_date')
                if unlock_date_str:
                    try:
                        achievement.unlock_date = datetime.fromisoformat(unlock_date_str)
                    except ValueError:
                        achievement.unlock_date = None 