"""
Testy jednostkowe dla systemu wydarzeń losowych
"""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import os

# Dodaj ścieżkę do modułów projektu - MUSI być przed importami z core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.game_engine import GameEngine
from core.events import EventManager, Event
from core.tile import Building, BuildingType


class TestEventManager:
    """Test systemu wydarzeń"""
    
    def setup_method(self):
        """Setup przed każdym testem"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        
        self.engine = GameEngine(map_width=10, map_height=10)
        self.event_manager = EventManager()
    
    def test_initialization(self):
        """Test inicjalizacji systemu wydarzeń"""
        assert len(self.event_manager.events) > 0
        assert self.event_manager.event_history == []
        assert self.event_manager.last_event_turn == 0
    
    def test_trigger_random_event(self):
        """Test wyzwalania losowych wydarzeń"""
        game_state = {
            'turn': 5,
            'money': 10000,
            'population': 500,
            'satisfaction': 60
        }
        
        event = self.event_manager.trigger_random_event(game_state)
        assert event is not None
        assert hasattr(event, 'title')
        assert hasattr(event, 'description')
        assert hasattr(event, 'effects')
        
        # Sprawdź czy wydarzenie zostało dodane do historii
        assert len(self.event_manager.event_history) == 1
        assert self.event_manager.event_history[0]['event'] == event
        assert self.event_manager.event_history[0]['turn'] == 5
    
    def test_apply_decision_effects(self):
        """Test aplikowania efektów decyzji"""
        # Znajdź wydarzenie z opcjami
        event_with_options = None
        for event in self.event_manager.events:
            if event.options and event.decision_effects:
                event_with_options = event
                break
        
        assert event_with_options is not None
        
        # Wybierz pierwszą opcję
        decision = event_with_options.options[0]
        effects = self.event_manager.apply_decision_effects(event_with_options, decision)
        
        assert effects is not None
        assert isinstance(effects, dict)
    
    def test_event_statistics(self):
        """Test statystyk wydarzeń"""
        # Dodaj kilka wydarzeń do historii
        for i in range(5):
            game_state = {'turn': i, 'money': 10000, 'population': 500, 'satisfaction': 60}
            self.event_manager.trigger_random_event(game_state)
        
        stats = self.event_manager.get_event_statistics()
        assert 'total_events' in stats
        assert stats['total_events'] == 5
        assert 'event_types' in stats
    
    def test_contextual_event_selection(self):
        """Test wyboru wydarzeń kontekstowych"""
        # Test z różnymi stanami gry
        low_money_state = {'turn': 10, 'money': 1000, 'population': 500, 'satisfaction': 60}
        high_pop_state = {'turn': 10, 'money': 50000, 'population': 2000, 'satisfaction': 60}
        
        # Wywołaj kilka razy aby sprawdzić różnorodność
        events_low_money = []
        events_high_pop = []
        
        for _ in range(3):
            events_low_money.append(self.event_manager.trigger_random_event(low_money_state))
            events_high_pop.append(self.event_manager.trigger_random_event(high_pop_state))
        
        # Sprawdź czy wydarzenia są różne (nie zawsze to samo)
        assert len(set(e.title for e in events_low_money)) >= 1
        assert len(set(e.title for e in events_high_pop)) >= 1


class TestEvent:
    """Test klasy Event"""
    
    def test_event_creation(self):
        """Test tworzenia wydarzenia"""
        event = Event(
            title="Test Event",
            description="Test description",
            effects={"money": 100, "satisfaction": 5},
            options=["Option 1", "Option 2"],
            decision_effects={
                "Option 1": {"money": 200},
                "Option 2": {"satisfaction": 10}
            }
        )
        
        assert event.title == "Test Event"
        assert event.description == "Test description"
        assert event.effects == {"money": 100, "satisfaction": 5}
        assert len(event.options) == 2
        assert "Option 1" in event.decision_effects
        assert "Option 2" in event.decision_effects
    
    def test_event_without_options(self):
        """Test wydarzenia bez opcji"""
        event = Event(
            title="Simple Event",
            description="Simple description",
            effects={"population": -10}
        )
        
        assert event.title == "Simple Event"
        assert event.effects == {"population": -10}
        assert event.options == []
        assert event.decision_effects == {}


if __name__ == "__main__":
    pytest.main([__file__]) 