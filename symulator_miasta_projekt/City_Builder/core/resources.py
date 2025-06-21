from typing import Dict, List
from dataclasses import dataclass, field
import json

@dataclass
class ResourceData:
    """Represents a single resource type"""
    name: str
    amount: float
    max_capacity: float = float('inf')
    production_rate: float = 0.0
    consumption_rate: float = 0.0
    price: float = 1.0  # For trading

class Economy:
    """Manages city's economy and resources"""
    
    def __init__(self, initial_money: float = 50000):
        self.resources = {
            # Basic resources
            'money': ResourceData('Money', initial_money, max_capacity=float('inf')),
            'energy': ResourceData('Energy', 100, max_capacity=1000, price=2.0),
            'water': ResourceData('Water', 100, max_capacity=1000, price=1.5),
            'materials': ResourceData('Materials', 50, max_capacity=500, price=3.0),
            'food': ResourceData('Food', 80, max_capacity=800, price=2.5),
            'luxury_goods': ResourceData('Luxury Goods', 20, max_capacity=200, price=5.0),
            
            # Derived metrics
            'population': ResourceData('Population', 0, price=0),
            'happiness': ResourceData('Happiness', 50, max_capacity=100, price=0),
            'education': ResourceData('Education', 0, max_capacity=100, price=0),
            'health': ResourceData('Health', 50, max_capacity=100, price=0),
            'safety': ResourceData('Safety', 50, max_capacity=100, price=0),
            'environment': ResourceData('Environment', 50, max_capacity=100, price=0),
        }
        
        self.tax_rates = {
            'residential': 0.05,  # 5% tax on residential income
            'commercial': 0.08,   # 8% tax on commercial income
            'industrial': 0.10,   # 10% tax on industrial income
        }
        
        self.expenses = {
            'maintenance': 0,     # Building maintenance costs
            'salaries': 0,        # Public service salaries
            'utilities': 0,       # City utilities
        }
        
        self.history: List[Dict] = []  # Resource history for reports
        
        # Śledzenie zmian dochodów
        self.previous_income = 0
        self.previous_expenses = 0
        self.income_change_alerts = []
        
    def get_resource(self, resource_name: str) -> ResourceData:
        """Get resource by name"""
        return self.resources.get(resource_name, ResourceData(resource_name, 0))
    
    def get_resource_amount(self, resource_name: str) -> float:
        """Get current amount of a resource"""
        return self.resources.get(resource_name, ResourceData(resource_name, 0)).amount
    
    def modify_resource(self, resource_name: str, amount: float) -> bool:
        """Modify resource amount with validation, returns True if successful"""
        from .validation_system import get_validation_system
        
        # Walidacja nazwy zasobu
        if not isinstance(resource_name, str) or not resource_name:
            return False
            
        if resource_name not in self.resources:
            return False
        
        # Walidacja kwoty
        validator = get_validation_system()
        amount_validation = validator.validate_money_amount(amount)
        
        if not amount_validation.is_valid:
            # Loguj błąd walidacji
            import logging
            logger = logging.getLogger('economy')
            logger.warning(f"Invalid amount for resource {resource_name}: {amount_validation.errors}")
            return False
        
        validated_amount = amount_validation.cleaned_data
        resource = self.resources[resource_name]
        new_amount = resource.amount + validated_amount
        
        # Sprawdzenie matematyczne (NaN, Infinity)
        import math
        if math.isnan(new_amount) or math.isinf(new_amount):
            import logging
            logger = logging.getLogger('economy')
            logger.error(f"Resource {resource_name} would become NaN or Infinity")
            return False
        
        # Check constraints - allow negative money (debt) but not other resources
        if resource_name != 'money' and new_amount < 0:
            return False
        if new_amount > resource.max_capacity:
            new_amount = resource.max_capacity
            
        resource.amount = round(new_amount, 2)  # Zaokrąglij do 2 miejsc po przecinku
        return True
    
    def can_afford(self, cost: float) -> bool:
        """Check if city can afford the cost"""
        return self.get_resource_amount('money') >= cost
    
    def spend_money(self, amount: float, game_engine=None) -> bool:
        """Spend money - now allows going into debt, with special handling for sandbox mode"""
        # W trybie Sandbox z nieograniczonymi środkami nie odbieraj pieniędzy
        if game_engine and hasattr(game_engine, 'special_sandbox_mode') and game_engine.special_sandbox_mode:
            # W trybie Sandbox utrzymuj zawsze wysoką kwotę
            if self.get_resource_amount('money') < 900000:  # Jeśli spadnie poniżej 900k
                self.modify_resource('money', 1000000 - self.get_resource_amount('money'))  # Uzupełnij do 1M
            return True
        
        self.modify_resource('money', -amount)
        return True
    
    def earn_money(self, amount: float):
        """Add money to treasury"""
        self.modify_resource('money', amount)
    
    def is_bankrupt(self, debt_limit: float = -4000, game_engine=None) -> bool:
        """
        Sprawdza czy miasto jest bankrutem (dług przekracza limit).
        
        Args:
            debt_limit (float): limit zadłużenia (domyślnie -4000)
            game_engine: silnik gry (dla sprawdzenia trybu Sandbox)
            
        Returns:
            bool: True jeśli miasto jest bankrutem
        """
        # W trybie Sandbox z wyłączonym bankructwem nigdy nie bankrutuj
        if game_engine and hasattr(game_engine, 'bankruptcy_disabled') and game_engine.bankruptcy_disabled:
            return False
        
        return self.get_resource_amount('money') <= debt_limit
    
    def calculate_taxes(self, buildings: List, population_manager=None) -> float:
        """
        Oblicza dochody podatkowe z budynków i pracującej populacji (znacznie zwiększone).
        
        Args:
            buildings (List): lista budynków w mieście
            population_manager: menedżer populacji (opcjonalnie)
            
        Returns:
            float: całkowite dochody podatkowe na turę
            
        Ta metoda została specjalnie dostrojona aby zwiększyć dochody z podatków,
        czyniąc grę bardziej przystępną finansowo.
        """
        total_tax = 0                    # całkowity podatek do zebrania
        employed_population = 0           # liczba zatrudnionych mieszkańców
        
        if population_manager:
            # Oblicz liczbę zatrudnionych mieszkańców
            # Sumuje wszystkich pracujących z różnych grup społecznych
            employed_population = sum(
                int(group.count * group.employment_rate)  # liczba * wskaźnik zatrudnienia
                for social, group in population_manager.groups.items()  # dla każdej grupy społecznej
                if social.value not in ['student', 'unemployed']        # pomijaj studentów i bezrobotnych
            )
        # Przejdź przez wszystkie budynki i oblicz podatki
        for building in buildings:
            # Sprawdź czy budynek istnieje i ma typ
            if not building or not hasattr(building, 'building_type'):
                continue  # pomiń ten budynek
                
            building_type = building.building_type.value  # pobierz typ budynku jako string
            
            # ZNACZNIE zwiększone dochody z budynków dla lepszej rozgrywki
            if 'commercial' in building_type or 'shop' in building_type or 'mall' in building_type:
                # Budynki komercyjne - generują 12% swojej wartości jako dochód bazowy
                base_income = building.cost * 0.12  # Zwiększone z 0.08 na 0.12 (12%!)
                total_tax += base_income * self.tax_rates['commercial']  # zastosuj stawkę podatkową
            elif 'industrial' in building_type or 'factory' in building_type:
                # Budynki przemysłowe - generują 10% swojej wartości jako dochód bazowy
                base_income = building.cost * 0.10  # Zwiększone z 0.07 na 0.10 (10%!)
                total_tax += base_income * self.tax_rates['industrial']
            elif 'residential' in building_type or 'house' in building_type or 'apartment' in building_type:
                # Budynki mieszkalne - generują 8% swojej wartości jako dochód bazowy
                base_income = building.cost * 0.08  # Zwiększone z 0.05 na 0.08 (8%!)
                total_tax += base_income * self.tax_rates['residential']
            else:
                # Wszystkie inne budynki - traktowane jak mieszkalne
                base_income = building.cost * 0.08  # Zwiększone z 0.05 na 0.08 (8%!)
                total_tax += base_income * self.tax_rates['residential']
                
        # Dodaj podatek dochodowy od zatrudnionych mieszkańców
        # Każdy zatrudniony mieszkaniec płaci 75$ podatku na turę
        total_tax += employed_population * 75 * self.tax_rates['residential']  # Zwiększone z 50 na 75!
        
        return total_tax  # zwróć całkowity podatek
    
    def calculate_expenses(self, buildings: List, population_manager=None) -> float:
        """
        Oblicza koszty utrzymania miasta (drastycznie zmniejszone dla lepszej rozgrywki).
        
        Args:
            buildings (List): lista budynków w mieście
            population_manager: menedżer populacji (opcjonalnie)
            
        Returns:
            float: całkowite koszty utrzymania na turę
            
        Koszty zostały specjalnie zmniejszone aby gra była bardziej przystępna
        i gracz nie musiał walczyć z nieustannymi problemami finansowymi.
        """
        total_expenses = 0
        for building in buildings:
            if not building:
                continue
            building_type = building.building_type.value
            # BARDZO niskie koszty utrzymania
            if any(service in building_type for service in ['park', 'school', 'hospital', 'university', 'police', 'fire']):
                maintenance_cost = building.cost * 0.0005  # Zmniejszone z 0.002 na 0.0005 (0.05%!)
            else:
                maintenance_cost = building.cost * 0.0003  # Zmniejszone z 0.0015 na 0.0003 (0.03%!)
            total_expenses += maintenance_cost
        # BARDZO niski koszt mieszkańca
        if population_manager:
            total_pop = population_manager.get_total_population()
            total_expenses += total_pop * 0.05  # Zmniejszone z 0.2 na 0.05 (25% poprzedniej wartości!)
        return total_expenses
    
    def update_turn(self, buildings: List, population_manager=None):
        """Update resources at the end of each turn"""
        # Calculate income and expenses
        tax_income = self.calculate_taxes(buildings, population_manager)
        total_expenses = self.calculate_expenses(buildings, population_manager)
        
        # Sprawdź czy są znaczące zmiany dochodów
        self._check_income_changes(tax_income, total_expenses)
        
        # Update money
        net_income = tax_income - total_expenses
        self.earn_money(net_income)
        # Update resource production/consumption
        self._update_resource_flows(buildings)
        # Store history for reports
        self._record_history()
    
    def _update_resource_flows(self, buildings: List):
        """Update resource production and consumption"""
        # Reset production/consumption rates
        for resource in self.resources.values():
            resource.production_rate = 0
            resource.consumption_rate = 0
        
        # Calculate from buildings
        for building in buildings:
            if not building or not hasattr(building, 'effects'):
                continue
                
            for effect, value in building.effects.items():
                if effect in self.resources:
                    if value > 0:
                        self.resources[effect].production_rate += value
                    else:
                        self.resources[effect].consumption_rate += abs(value)
        
        # Apply production/consumption
        for resource_name, resource in self.resources.items():
            if resource_name == 'money':  # Money handled separately
                continue
                
            net_change = resource.production_rate - resource.consumption_rate
            self.modify_resource(resource_name, net_change)
    
    def _record_history(self):
        """Record current state for historical analysis"""
        snapshot = {
            'turn': len(self.history) + 1,
            'resources': {name: res.amount for name, res in self.resources.items()},
            'tax_income': self.calculate_taxes([]),  # Would need actual buildings
            'expenses': sum(self.expenses.values())
        }
        self.history.append(snapshot)
        
        # Keep only last 100 turns
        if len(self.history) > 100:
            self.history.pop(0)
    
    def _check_income_changes(self, current_income: float, current_expenses: float):
        """Sprawdza znaczące zmiany dochodów i generuje alerty"""
        # Clear old alerts (keep only last 5)
        if len(self.income_change_alerts) > 5:
            self.income_change_alerts = self.income_change_alerts[-5:]
        
        # Sprawdź zmiany dochodów
        if self.previous_income > 0:
            income_change = current_income - self.previous_income
            income_change_percent = (income_change / self.previous_income) * 100
            
            # Znaczące zwiększenie dochodów (>50% lub >$1000)
            if income_change > 1000 or income_change_percent > 50:
                alert = f"📈 Dochody wzrosły z ${self.previous_income:,.0f} na ${current_income:,.0f} (+${income_change:,.0f}, +{income_change_percent:.1f}%)"
                self.income_change_alerts.append(alert)
            
            # Znaczące zmniejszenie dochodów (>50% lub >$1000)
            elif income_change < -1000 or income_change_percent < -50:
                alert = f"📉 Dochody spadły z ${self.previous_income:,.0f} na ${current_income:,.0f} (${income_change:,.0f}, {income_change_percent:.1f}%)"
                self.income_change_alerts.append(alert)
        
        # Sprawdź zmiany wydatków
        if self.previous_expenses > 0:
            expense_change = current_expenses - self.previous_expenses
            expense_change_percent = (expense_change / self.previous_expenses) * 100
            
            # Znaczące zwiększenie wydatków (>30% lub >$500)
            if expense_change > 500 or expense_change_percent > 30:
                alert = f"💸 Wydatki wzrosły z ${self.previous_expenses:,.0f} na ${current_expenses:,.0f} (+${expense_change:,.0f}, +{expense_change_percent:.1f}%)"
                self.income_change_alerts.append(alert)
        
        # Zapisz obecne wartości na następną turę
        self.previous_income = current_income
        self.previous_expenses = current_expenses
    
    def get_income_change_alerts(self) -> List[str]:
        """Zwraca listę alertów o zmianach dochodów"""
        return self.income_change_alerts.copy()
    
    def get_resource_summary(self) -> Dict:
        """Get summary of all resources"""
        return {
            name: {
                'amount': res.amount,
                'max_capacity': res.max_capacity,
                'production': res.production_rate,
                'consumption': res.consumption_rate,
                'price': res.price
            }
            for name, res in self.resources.items()
        }
    
    def save_to_dict(self) -> Dict:
        """Save economy state to dictionary"""
        return {
            'resources': {
                name: {
                    'name': res.name,
                    'amount': res.amount,
                    'max_capacity': res.max_capacity,
                    'production_rate': res.production_rate,
                    'consumption_rate': res.consumption_rate,
                    'price': res.price
                }
                for name, res in self.resources.items()
            },
            'tax_rates': self.tax_rates,
            'expenses': self.expenses,
            'history': self.history
        }
    
    def load_from_dict(self, data: Dict):
        """Load economy state from dictionary"""
        if 'resources' in data:
            for name, res_data in data['resources'].items():
                self.resources[name] = ResourceData(**res_data)
        
        if 'tax_rates' in data:
            self.tax_rates.update(data['tax_rates'])
            
        if 'expenses' in data:
            self.expenses.update(data['expenses'])
            
        if 'history' in data:
            self.history = data['history']

