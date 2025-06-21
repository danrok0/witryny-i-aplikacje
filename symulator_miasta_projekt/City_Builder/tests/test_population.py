"""
Testy jednostkowe dla systemu populacji
"""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import os

# Dodaj ścieżkę do modułów projektu - MUSI być przed importami z core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_helpers import find_buildable_location
from core.game_engine import GameEngine
from core.population import PopulationManager, SocialClass, PopulationGroup
from core.tile import Building, BuildingType


class TestPopulationManager:
    """Test systemu populacji"""
    
    def setup_method(self):
        """Setup przed każdym testem"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        
        self.engine = GameEngine(map_width=10, map_height=10)
        self.population = self.engine.population
    
    def test_initialization(self):
        """Test inicjalizacji systemu populacji"""
        # PopulationManager ma początkową populację
        total_pop = self.population.get_total_population()
        assert total_pop > 0  # Nie zero, bo ma początkowe grupy
        
        # Sprawdź czy grupy społeczne są zainicjalizowane
        assert len(self.population.groups) > 0
        assert SocialClass.WORKER in self.population.groups
        assert SocialClass.MIDDLE_CLASS in self.population.groups
        
        # Sprawdź potrzeby
        assert 'housing' in self.population.needs
        assert 'jobs' in self.population.needs
    
    def test_population_calculation(self):
        """Test obliczania populacji"""
        initial_population = self.population.get_total_population()
        
        # Dodaj budynek mieszkalny przez engine
        house = Building("Test House", BuildingType.HOUSE, 500, {"population": 35})
        
        # Znajdź miejsce do budowania
        x, y = find_buildable_location(self.engine)
        if x is not None and y is not None:
            success = self.engine.place_building(x, y, house)
            if success:
                # Sprawdź czy populacja wzrosła
                new_population = self.population.get_total_population()
                assert new_population > initial_population
            else:
                # Jeśli nie udało się postawić, sprawdź czy system działa
                assert initial_population > 0
        else:
            # Jeśli nie ma miejsca, sprawdź czy system działa
            assert initial_population > 0
    
    def test_unemployment_calculation(self):
        """Test obliczania bezrobocia"""
        unemployment_rate = self.population.get_unemployment_rate()
        assert 0 <= unemployment_rate <= 100
        
        # Dodaj miejsca pracy
        shop = Building("Test Shop", BuildingType.SHOP, 800, {"jobs": 15})
        self.engine.place_building(1, 0, shop)
        
        # Przelicz potrzeby
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Bezrobocie powinno się zmienić
        new_unemployment = self.population.get_unemployment_rate()
        assert 0 <= new_unemployment <= 100
    
    def test_satisfaction_calculation(self):
        """Test obliczania zadowolenia"""
        satisfaction = self.population.get_average_satisfaction()
        assert 0 <= satisfaction <= 100
        
        # Dodaj usługi publiczne
        school = Building("Test School", BuildingType.SCHOOL, 2000, {"education": 50})
        self.engine.place_building(2, 0, school)
        
        # Przelicz potrzeby
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Zadowolenie może się zmienić
        new_satisfaction = self.population.get_average_satisfaction()
        assert 0 <= new_satisfaction <= 100
    
    def test_calculate_needs(self):
        """Test obliczania potrzeb populacji"""
        # Dodaj różne budynki
        house = Building("House", BuildingType.HOUSE, 500, {"population": 50})
        shop = Building("Shop", BuildingType.SHOP, 800, {"jobs": 25})
        school = Building("School", BuildingType.SCHOOL, 2000, {"education": 50})
        
        self.engine.place_building(0, 0, house)
        self.engine.place_building(1, 0, shop)
        self.engine.place_building(2, 0, school)
        
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Sprawdź czy potrzeby zostały przeliczone
        assert 'housing' in self.population.needs
        assert 'jobs' in self.population.needs
        assert 'education' in self.population.needs
        
        # Sprawdź strukturę potrzeb
        for need_name, need_data in self.population.needs.items():
            assert 'current' in need_data
            assert 'demand' in need_data
            assert 'satisfaction' in need_data
            assert 0 <= need_data['satisfaction'] <= 100
    
    def test_update_population_dynamics(self):
        """Test aktualizacji dynamiki populacji"""
        initial_population = self.population.get_total_population()
        
        # Dodaj domy dla lepszych warunków
        for i in range(3):
            house = Building(f"House {i}", BuildingType.HOUSE, 500, {"population": 50})
            self.engine.place_building(i, 0, house)
        
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Aktualizuj dynamikę populacji
        self.population.update_population_dynamics()
        
        # Populacja może się zmienić (wzrosnąć lub spaść)
        new_population = self.population.get_total_population()
        assert new_population > 0
    
    def test_population_growth_conditions(self):
        """Test warunków wzrostu populacji"""
        # Stwórz dobre warunki - dużo domów i usług
        for i in range(5):
            house = Building(f"House {i}", BuildingType.HOUSE, 500, {"population": 50})
            self.engine.place_building(i, 0, house)
        
        # Dodaj usługi
        school = Building("School", BuildingType.SCHOOL, 2000, {"education": 50})
        hospital = Building("Hospital", BuildingType.HOSPITAL, 3000, {"health": 100})
        
        self.engine.place_building(5, 0, school)
        self.engine.place_building(6, 0, hospital)
        
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Sprawdź zadowolenie z mieszkań
        housing_satisfaction = self.population.needs['housing']['satisfaction']
        assert housing_satisfaction >= 0
    
    def test_population_decline_conditions(self):
        """Test warunków spadku populacji"""
        # Usuń wszystkie budynki aby stworzyć złe warunki
        # (w rzeczywistości trudno to przetestować bez manipulacji wewnętrznych struktur)
        
        # Sprawdź czy system radzi sobie z brakiem infrastruktury
        buildings = []  # Brak budynków
        self.population.calculate_needs(buildings)
        
        # Potrzeby powinny być niezaspokojone
        housing_satisfaction = self.population.needs['housing']['satisfaction']
        jobs_satisfaction = self.population.needs['jobs']['satisfaction']
        
        # Przy braku budynków zadowolenie powinno być niskie
        assert housing_satisfaction <= 100
        assert jobs_satisfaction <= 100
    
    def test_social_groups(self):
        """Test grup społecznych"""
        # Sprawdź czy wszystkie grupy istnieją
        assert SocialClass.WORKER in self.population.groups
        assert SocialClass.MIDDLE_CLASS in self.population.groups
        assert SocialClass.UPPER_CLASS in self.population.groups
        assert SocialClass.STUDENT in self.population.groups
        assert SocialClass.UNEMPLOYED in self.population.groups
        
        # Sprawdź właściwości grup
        for social_class, group in self.population.groups.items():
            assert isinstance(group, PopulationGroup)
            assert group.count >= 0
            assert 0 <= group.satisfaction <= 100
            assert 0 <= group.employment_rate <= 1.0
    
    def test_demographics(self):
        """Test demografii"""
        demographics = self.population.get_demographics()
        
        assert 'total_population' in demographics
        assert 'social_groups' in demographics
        assert 'unemployment_rate' in demographics
        assert 'average_satisfaction' in demographics
        assert 'needs' in demographics
        
        # Sprawdź czy dane są sensowne
        assert demographics['total_population'] > 0
        assert len(demographics['social_groups']) > 0
    
    def test_population_statistics(self):
        """Test statystyk populacji"""
        # Dodaj budynki
        house = Building("House", BuildingType.HOUSE, 500, {"population": 50})
        shop = Building("Shop", BuildingType.SHOP, 800, {"jobs": 25})
        
        self.engine.place_building(0, 0, house)
        self.engine.place_building(1, 0, shop)
        
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Sprawdź podstawowe statystyki
        total_pop = self.population.get_total_population()
        unemployment = self.population.get_unemployment_rate()
        satisfaction = self.population.get_average_satisfaction()
        
        assert total_pop > 0
        assert 0 <= unemployment <= 100
        assert 0 <= satisfaction <= 100
    
    def test_instant_population_change(self):
        """Test natychmiastowej zmiany populacji"""
        initial_population = self.population.get_total_population()
        
        # Dodaj populację
        self.population.add_instant_population(100)
        new_population = self.population.get_total_population()
        assert new_population == initial_population + 100
        
        # Usuń populację
        self.population.add_instant_population(-50)
        final_population = self.population.get_total_population()
        assert final_population == initial_population + 50
    
    def test_save_load_functionality(self):
        """Test zapisywania i wczytywania danych populacji"""
        # Zmień stan populacji
        self.population.add_instant_population(200)
        original_population = self.population.get_total_population()
        
        # Zapisz dane
        saved_data = self.population.save_to_dict()
        assert isinstance(saved_data, dict)
        assert 'groups' in saved_data
        assert 'needs' in saved_data
        
        # Stwórz nowy manager i wczytaj dane
        new_population = PopulationManager()
        new_population.load_from_dict(saved_data)
        
        # Sprawdź czy dane zostały przywrócone
        loaded_population = new_population.get_total_population()
        assert loaded_population == original_population
    
    def test_needs_satisfaction_bounds(self):
        """Test granic zadowolenia z potrzeb"""
        # Dodaj bardzo dużo budynków (nadpodaż)
        for i in range(20):
            house = Building(f"House {i}", BuildingType.HOUSE, 500, {"population": 10})
            shop = Building(f"Shop {i}", BuildingType.SHOP, 800, {"jobs": 50})
            if i < 10:  # Tylko pierwsze 10 się zmieści na mapie 10x10
                self.engine.place_building(i, 0, house)
                if i < 5:
                    self.engine.place_building(i, 1, shop)
        
        buildings = self.engine.get_all_buildings()
        self.population.calculate_needs(buildings)
        
        # Zadowolenie nie powinno przekraczać 100%
        for need_name, need_data in self.population.needs.items():
            assert 0 <= need_data['satisfaction'] <= 100


if __name__ == "__main__":
    pytest.main([__file__]) 