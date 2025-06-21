from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
import random

class SocialClass(Enum):
    """
    Wyliczenie klas społecznych w mieście.
    
    Każda klasa ma inne charakterystyki:
    - Dochody i wydatki
    - Poziom zatrudnienia
    - Zadowolenie z życia
    - Wpływ na rozwój miasta
    """
    WORKER = "worker"              # robotnicy - podstawowa klasa pracownicza
    MIDDLE_CLASS = "middle_class"  # klasa średnia - wykształceni mieszkańcy
    UPPER_CLASS = "upper_class"    # klasa wyższa - bogaci mieszkańcy
    STUDENT = "student"            # studenci - przyszła siła robocza
    UNEMPLOYED = "unemployed"      # bezrobotni - wymagają wsparcia

@dataclass
class PopulationGroup:
    """
    Reprezentuje grupę populacji o podobnych charakterystykach.
    
    @dataclass - dekorator automatycznie generujący konstruktor, __repr__ itp.
    Każda grupa ma swoje parametry ekonomiczne i społeczne.
    """
    social_class: SocialClass      # klasa społeczna tej grupy
    count: int                     # liczba osób w grupie
    employment_rate: float = 0.0   # wskaźnik zatrudnienia (0.0-1.0)
    satisfaction: float = 50.0     # poziom zadowolenia (0-100)
    income: float = 0.0           # średni dochód na osobę
    age_distribution: Dict[str, int] = None  # rozkład wiekowy (młodzi, dorośli, starsi)
    
    def __post_init__(self):
        """
        Metoda wywoływana automatycznie po inicjalizacji obiektu.
        
        __post_init__ to specjalna metoda @dataclass, która jest wywoływana
        po tym jak konstruktor ustawi wszystkie pola.
        """
        # Jeśli nie podano rozkładu wiekowego, ustaw domyślny
        if self.age_distribution is None:
            self.age_distribution = {
                "young": 30,    # 30% młodych (0-25 lat)
                "adult": 50,    # 50% dorosłych (26-65 lat)  
                "elderly": 20   # 20% starszych (65+ lat)
            }

class PopulationManager:
    """
    Zarządza dynamiką populacji miasta.
    
    Odpowiada za:
    - Śledzenie różnych grup społecznych
    - Obliczanie potrzeb mieszkańców (mieszkania, praca, usługi)
    - Symulację wzrostu/spadku populacji
    - Monitorowanie zadowolenia i bezrobocia
    - Wpływ budynków na populację
    """
    
    def __init__(self):
        """
        Konstruktor menedżera populacji.
        
        Inicjalizuje wszystkie grupy społeczne z ich parametrami startowymi,
        ustawienia wzrostu populacji oraz system potrzeb mieszkańców.
        """
        # Grupy populacji z ich charakterystykami (starszy system - do usunięcia)
        self.population_groups = {
            'workers': {'size': 100, 'income': 1000, 'tax_rate': 0.2, 'satisfaction': 0.5},
            'middle_class': {'size': 50, 'income': 2000, 'tax_rate': 0.25, 'satisfaction': 0.5},
            'elite': {'size': 10, 'income': 5000, 'tax_rate': 0.3, 'satisfaction': 0.5}
        }
        
        # Parametry wzrostu populacji - dostosowane dla naturalniejszego wzrostu
        self.birth_rate = 0.025      # współczynnik urodzeń: 2.5% naturalne (zwiększone z 1.5%)
        self.death_rate = 0.002      # współczynnik śmiertelności: 0.2% (zmniejszone z 0.3%)
        self.migration_factor = 0.01 # wpływ migracji: 1% (zmniejszone z 2%)
        
        # Parametry mieszkaniowe i zadowolenia - bardziej przebaczające
        self.housing_satisfaction_threshold = 0.2  # próg zadowolenia mieszkaniowego (zmniejszone z 0.3)
        self.satisfaction_multiplier = 0.8         # mnożnik wpływu zadowolenia (zwiększone z 0.5)
        self.min_satisfaction = 0.1               # minimalne zadowolenie (zmniejszone z 0.2)
        self.max_population_decline = 0.01       # maksymalny spadek populacji: 1% (zmniejszone z 2%)
        
        # System potrzeb mieszkańców (starszy format)
        self.needs = {
            'housing': 0.0,      # potrzeby mieszkaniowe
            'jobs': 0.0,         # potrzeby pracy
            'services': 0.0,     # potrzeby usług
            'entertainment': 0.0 # potrzeby rozrywki
        }
        
        # Statystyki populacji
        self.statistics = {
            'total_population': 0,      # całkowita populacja
            'unemployment_rate': 0.0,   # stopa bezrobocia
            'average_satisfaction': 0.0, # średnie zadowolenie
            'population_growth': 0.0    # wzrost populacji
        }
        
        # Nowy system grup społecznych (aktualnie używany)
        self.groups = {
            SocialClass.WORKER: PopulationGroup(
                SocialClass.WORKER, 150,                    # 150 robotników
                employment_rate=0.8,                        # 80% zatrudnienia
                satisfaction=40.0,                          # zadowolenie 40/100
                income=2000                                 # $2000 dochodu
            ),
            SocialClass.MIDDLE_CLASS: PopulationGroup(
                SocialClass.MIDDLE_CLASS, 75,               # 75 klasy średniej
                employment_rate=0.85,                       # 85% zatrudnienia
                satisfaction=60.0,                          # zadowolenie 60/100
                income=4000                                 # $4000 dochodu
            ),
            SocialClass.UPPER_CLASS: PopulationGroup(
                SocialClass.UPPER_CLASS, 15,                # 15 klasy wyższej
                employment_rate=0.7,                        # 70% zatrudnienia (niektórzy żyją z rent)
                satisfaction=70.0,                          # zadowolenie 70/100
                income=8000                                 # $8000 dochodu
            ),
            SocialClass.STUDENT: PopulationGroup(
                SocialClass.STUDENT, 30,                    # 30 studentów
                employment_rate=0.3,                        # 30% zatrudnienia (praca dorywcza)
                satisfaction=55.0,                          # zadowolenie 55/100
                income=500                                  # $500 dochodu (stypendia, dorywcza praca)
            ),
            SocialClass.UNEMPLOYED: PopulationGroup(
                SocialClass.UNEMPLOYED, 20,                 # 20 bezrobotnych
                employment_rate=0.0,                        # 0% zatrudnienia
                satisfaction=20.0,                          # zadowolenie 20/100 (niezadowoleni)
                income=800                                  # $800 dochodu (zasiłki)
            )
        }
        
        # Nowy system potrzeb z bardziej szczegółowymi kategoriami
        self.needs = {
            'housing': {'current': 0, 'demand': 0, 'satisfaction': 50},        # mieszkania
            'jobs': {'current': 0, 'demand': 0, 'satisfaction': 50},           # miejsca pracy
            'healthcare': {'current': 0, 'demand': 0, 'satisfaction': 50},     # opieka zdrowotna
            'education': {'current': 0, 'demand': 0, 'satisfaction': 50},      # edukacja
            'safety': {'current': 0, 'demand': 0, 'satisfaction': 50},         # bezpieczeństwo
            'entertainment': {'current': 0, 'demand': 0, 'satisfaction': 50},  # rozrywka
            'transport': {'current': 0, 'demand': 0, 'satisfaction': 50}       # transport
        }
        
    def get_total_population(self) -> int:
        """
        Pobiera całkowitą liczbę mieszkańców miasta.
        
        Returns:
            int: suma wszystkich mieszkańców ze wszystkich grup społecznych
        """
        # sum() - funkcja sumująca elementy iterowalneg obiektu
        # group.count for group in self.groups.values() - generator expression
        return sum(group.count for group in self.groups.values())
    
    def get_unemployment_rate(self) -> float:
        """
        Oblicza stopę bezrobocia w mieście.
        
        Returns:
            float: stopa bezrobocia w procentach (0-100)
            
        Stopa bezrobocia = (liczba bezrobotnych / siła robocza) * 100
        Siła robocza = wszyscy dorośli oprócz studentów
        """
        # Oblicz całkowitą siłę roboczą (wszyscy oprócz studentów)
        total_workforce = sum(
            group.count for group in self.groups.values() 
            if group.social_class != SocialClass.STUDENT  # pomijaj studentów
        )
        
        # Pobierz liczbę bezrobotnych
        unemployed = self.groups[SocialClass.UNEMPLOYED].count
        
        # Oblicz stopę bezrobocia (zabezpiecz przed dzieleniem przez zero)
        return (unemployed / total_workforce) * 100 if total_workforce > 0 else 0
    
    def get_average_satisfaction(self) -> float:
        """
        Oblicza średnie ważone zadowolenie mieszkańców.
        
        Returns:
            float: średnie zadowolenie ważone liczebnością grup (0-100)
            
        Średnia ważona = suma(zadowolenie_grupy * liczebność_grupy) / całkowita_populacja
        """
        total_pop = self.get_total_population()
        if total_pop == 0:
            return 50.0  # domyślne zadowolenie jeśli brak mieszkańców
            
        # Oblicz średnią ważoną zadowolenia wszystkich grup
        weighted_satisfaction = sum(
            group.count * group.satisfaction for group in self.groups.values()
        )
        
        return weighted_satisfaction / total_pop
    
    def calculate_needs(self, buildings: List):
        """Calculate population needs based on current infrastructure"""
        total_pop = self.get_total_population()
        
        if total_pop == 0:
            return
        
        # Reset current supply
        for need in self.needs.values():
            need['current'] = 0
        
        # Calculate supply from buildings
        for building in buildings:
            if not building or not hasattr(building, 'effects'):
                continue
                
            effects = building.effects
            building_type = building.building_type.value
            
            # Housing supply
            if 'population' in effects:
                self.needs['housing']['current'] += effects['population']
            
            # Jobs supply  
            if 'jobs' in effects:
                self.needs['jobs']['current'] += effects['jobs']
            
            # Healthcare supply
            if 'health' in effects:
                self.needs['healthcare']['current'] += effects['health']
            
            # Education supply
            if 'education' in effects:
                self.needs['education']['current'] += effects['education']
            
            # Safety supply
            if 'safety' in effects:
                self.needs['safety']['current'] += effects['safety']
            
            # Entertainment supply
            if 'happiness' in effects and ('park' in building_type or 'stadium' in building_type):
                self.needs['entertainment']['current'] += effects['happiness']
            
            # Transport supply
            if 'traffic' in effects or 'walkability' in effects:
                self.needs['transport']['current'] += effects.get('traffic', 0) + effects.get('walkability', 0)
        
        # Calculate demand based on population
        self.needs['housing']['demand'] = total_pop
        self.needs['jobs']['demand'] = int(total_pop * 0.6)  # 60% need jobs
        self.needs['healthcare']['demand'] = int(total_pop * 0.3)  # 30% need healthcare
        self.needs['education']['demand'] = int(total_pop * 0.4)  # 40% need education
        self.needs['safety']['demand'] = int(total_pop * 0.5)  # 50% need safety
        self.needs['entertainment']['demand'] = int(total_pop * 0.2)  # 20% need entertainment
        self.needs['transport']['demand'] = int(total_pop * 0.7)  # 70% need transport
        
        # Calculate satisfaction for each need
        for need_name, need_data in self.needs.items():
            if need_data['demand'] > 0:
                ratio = need_data['current'] / need_data['demand']
                need_data['satisfaction'] = min(100, ratio * 100)
            else:
                need_data['satisfaction'] = 100
    
    def update_population_dynamics(self):
        """Update population through births, deaths, and migration"""
        total_pop = self.get_total_population()
        if total_pop == 0:
            return
            
        avg_satisfaction = self.get_average_satisfaction()
        
        # Housing satisfaction bonus - zwiększony wpływ na wzrost
        housing_satisfaction = self.needs['housing']['satisfaction']
        housing_bonus = max(0, (housing_satisfaction - 30) / 100)  # Obniżony próg z 50 na 30
        
        # Natural population change - adjusted by satisfaction
        satisfaction_multiplier = max(0.5, avg_satisfaction / 100)  # Zwiększony minimalny mnożnik z 0.2 na 0.5
        
        # Przyrost naturalny - zmniejszona losowość
        births = int(total_pop * self.birth_rate * satisfaction_multiplier * (1 + housing_bonus) * random.uniform(0.95, 1.05))
        deaths = int(total_pop * self.death_rate * (2 - satisfaction_multiplier) * random.uniform(0.95, 1.05))
        
        # Migracja - znacznie bardziej stabilna
        migration_rate = ((avg_satisfaction - 20) / 100 + housing_bonus) * self.migration_factor  # Obniżony próg z 30 na 20
        migration = int(total_pop * migration_rate * random.uniform(0.95, 1.05))
        
        net_change = births - deaths + migration
        
        # Zabezpieczenie przed drastycznym spadkiem
        if net_change < 0 and abs(net_change) > total_pop * 0.02:  # Zmniejszone z 5% na 2%
            net_change = -int(total_pop * 0.02)
        
        # Distribute changes across social classes
        self._distribute_population_change(net_change)
        
        # Update employment
        self._update_employment()
        
        # Update satisfaction based on needs
        self._update_satisfaction()
    
    def _distribute_population_change(self, net_change: int):
        """Distribute population change across social classes"""
        if net_change == 0:
            return
            
        total_pop = self.get_total_population()
        if total_pop == 0:
            return
            
        # Distribute proportionally z mniejszą losowością
        for social_class, group in self.groups.items():
            if social_class == SocialClass.UNEMPLOYED:
                continue  # Handle unemployment separately
                
            proportion = group.count / total_pop
            change = int(net_change * proportion * random.uniform(0.9, 1.1))  # Zmniejszona losowość z 0.7-1.3 na 0.9-1.1
            
            new_count = max(0, group.count + change)
            group.count = new_count
    
    def _update_employment(self):
        """Update employment rates based on available jobs"""
        total_jobs = self.needs['jobs']['current']
        total_workforce = sum(
            group.count for group in self.groups.values()
            if group.social_class != SocialClass.STUDENT
        )
        
        if total_workforce == 0:
            return
            
        employment_ratio = min(1.0, total_jobs / total_workforce)
        
        # Update employment rates
        for social_class, group in self.groups.items():
            if social_class == SocialClass.STUDENT:
                continue
            elif social_class == SocialClass.UNEMPLOYED:
                # Some unemployed might find jobs
                jobs_found = int(group.count * employment_ratio * 0.1)  # 10% chance
                group.count = max(0, group.count - jobs_found)
                # Add them to working class
                self.groups[SocialClass.WORKER].count += jobs_found
            else:
                # Update employment rate
                base_rate = {
                    SocialClass.WORKER: 0.8,
                    SocialClass.MIDDLE_CLASS: 0.85,
                    SocialClass.UPPER_CLASS: 0.7
                }.get(social_class, 0.5)
                
                group.employment_rate = min(base_rate, employment_ratio)
    
    def _update_satisfaction(self):
        """Update satisfaction based on needs fulfillment"""
        for social_class, group in self.groups.items():
            # Base satisfaction from needs
            needs_satisfaction = []
            for need_name, need_data in self.needs.items():
                needs_satisfaction.append(need_data['satisfaction'])
            
            # Calculate average needs satisfaction
            if needs_satisfaction:
                avg_needs = sum(needs_satisfaction) / len(needs_satisfaction)
            else:
                avg_needs = 50
            
            # Różne klasy społeczne mają różne priorytety
            if social_class == SocialClass.WORKER:
                # Robotnicy priorytetowo patrzą na pracę i mieszkania
                priority_satisfaction = (
                    self.needs['jobs']['satisfaction'] * 0.4 +  # Zwiększone z 0.3
                    self.needs['housing']['satisfaction'] * 0.4 +  # Zwiększone z 0.3
                    avg_needs * 0.2  # Zmniejszone z 0.4
                )
            elif social_class == SocialClass.MIDDLE_CLASS:
                # Klasa średnia patrzy na edukację i bezpieczeństwo
                priority_satisfaction = (
                    self.needs['education']['satisfaction'] * 0.3 +  # Zwiększone z 0.25
                    self.needs['safety']['satisfaction'] * 0.3 +  # Zwiększone z 0.25
                    self.needs['housing']['satisfaction'] * 0.2 +
                    avg_needs * 0.2  # Zmniejszone z 0.3
                )
            elif social_class == SocialClass.UPPER_CLASS:
                # Klasa wyższa patrzy na rozrywkę i transport
                priority_satisfaction = (
                    self.needs['entertainment']['satisfaction'] * 0.4 +  # Zwiększone z 0.3
                    self.needs['transport']['satisfaction'] * 0.3 +  # Zwiększone z 0.2
                    avg_needs * 0.3  # Zmniejszone z 0.5
                )
            else:
                priority_satisfaction = avg_needs
            
            # Gładkie przejście satysfakcji (nie skrajne zmiany)
            new_satisfaction = group.satisfaction * 0.8 + priority_satisfaction * 0.2  # Zmienione proporcje
            
            # Upewnij się, że satysfakcja nie spada poniżej 20% i nie rośnie powyżej 100%
            group.satisfaction = max(20, min(100, new_satisfaction))  # Zwiększony minimalny poziom z 10 na 20
    
    def get_demographics(self) -> Dict:
        """Get demographic statistics"""
        return {
            'total_population': self.get_total_population(),
            'unemployment_rate': self.get_unemployment_rate(),
            'average_satisfaction': self.get_average_satisfaction(),
            'social_groups': {
                class_name.value: {
                    'count': group.count,
                    'employment_rate': group.employment_rate,
                    'satisfaction': group.satisfaction,
                    'income': group.income
                }
                for class_name, group in self.groups.items()
            },
            'needs': self.needs
        }
    
    def save_to_dict(self) -> Dict:
        """Save population state to dictionary"""
        return {
            'groups': {
                class_name.value: {
                    'social_class': group.social_class.value,
                    'count': group.count,
                    'employment_rate': group.employment_rate,
                    'satisfaction': group.satisfaction,
                    'income': group.income,
                    'age_distribution': group.age_distribution
                }
                for class_name, group in self.groups.items()
            },
            'needs': self.needs,
            'birth_rate': self.birth_rate,
            'death_rate': self.death_rate,
            'migration_factor': self.migration_factor
        }
    
    def load_from_dict(self, data: Dict):
        """Load population state from dictionary"""
        if 'groups' in data:
            for class_name, group_data in data['groups'].items():
                social_class = SocialClass(class_name)
                self.groups[social_class] = PopulationGroup(
                    social_class=social_class,
                    count=group_data['count'],
                    employment_rate=group_data['employment_rate'],
                    satisfaction=group_data['satisfaction'],
                    income=group_data['income'],
                    age_distribution=group_data.get('age_distribution')
                )
        
        if 'needs' in data:
            self.needs.update(data['needs'])
            
        if 'birth_rate' in data:
            self.birth_rate = data['birth_rate']
            
        if 'death_rate' in data:
            self.death_rate = data['death_rate']
            
        if 'migration_factor' in data:
            self.migration_factor = data['migration_factor']

    def add_instant_population(self, value: int):
        """Instantly add population to the WORKER group (default for new housing)."""
        if SocialClass.WORKER in self.groups:
            self.groups[SocialClass.WORKER].count += value
        else:
            # Fallback: add to any group
            for group in self.groups.values():
                group.count += value
                break
    
    def reset_to_initial_state(self):
        """
        Resetuje populację do stanu początkowego.
        
        Przywraca domyślne wartości wszystkich grup społecznych
        i statystyk populacyjnych.
        """
        # Resetuj grupy społeczne do wartości początkowych
        self.groups = {
            SocialClass.WORKER: PopulationGroup(
                SocialClass.WORKER, 150,
                employment_rate=0.8,
                satisfaction=40.0,
                income=2000
            ),
            SocialClass.MIDDLE_CLASS: PopulationGroup(
                SocialClass.MIDDLE_CLASS, 75,
                employment_rate=0.85,
                satisfaction=60.0,
                income=4000
            ),
            SocialClass.UPPER_CLASS: PopulationGroup(
                SocialClass.UPPER_CLASS, 15,
                employment_rate=0.7,
                satisfaction=70.0,
                income=8000
            ),
            SocialClass.STUDENT: PopulationGroup(
                SocialClass.STUDENT, 30,
                employment_rate=0.3,
                satisfaction=55.0,
                income=500
            ),
            SocialClass.UNEMPLOYED: PopulationGroup(
                SocialClass.UNEMPLOYED, 20,
                employment_rate=0.0,
                satisfaction=20.0,
                income=800
            )
        }
        
        # Resetuj potrzeby
        self.needs = {
            'housing': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'jobs': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'healthcare': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'education': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'safety': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'entertainment': {'current': 0, 'demand': 0, 'satisfaction': 50},
            'transport': {'current': 0, 'demand': 0, 'satisfaction': 50}
        }
        
        # Resetuj statystyki
        self.statistics = {
            'total_population': 0,
            'unemployment_rate': 0.0,
            'average_satisfaction': 0.0,
            'population_growth': 0.0
        }
