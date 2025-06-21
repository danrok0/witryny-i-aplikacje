"""
Testy dla modułu zarządzania konfiguracją.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager, get_config_manager

class TestConfigManager:
    """Testy dla klasy ConfigManager."""
    
    def setup_method(self):
        """Przygotowanie przed każdym testem."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        self.config_manager = ConfigManager(self.config_path)
    
    def teardown_method(self):
        """Czyszczenie po każdym teście."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_default_config(self):
        """Test tworzenia domyślnej konfiguracji."""
        assert self.config_manager.config is not None
        assert 'game_settings' in self.config_manager.config
        assert 'ui_settings' in self.config_manager.config
        assert 'performance_settings' in self.config_manager.config
    
    def test_get_existing_value(self):
        """Test pobierania istniejącej wartości."""
        value = self.config_manager.get('game_settings.difficulty')
        assert value == 'Normal'
    
    def test_get_nonexistent_value_returns_default(self):
        """Test pobierania nieistniejącej wartości zwraca default."""
        value = self.config_manager.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_set_valid_value(self):
        """Test ustawiania poprawnej wartości."""
        result = self.config_manager.set('game_settings.difficulty', 'Hard')
        assert result is True
        assert self.config_manager.get('game_settings.difficulty') == 'Hard'
    
    def test_set_invalid_value_fails(self):
        """Test ustawiania niepoprawnej wartości."""
        result = self.config_manager.set('game_settings.difficulty', 'Invalid')
        assert result is False
    
    def test_validate_difficulty(self):
        """Test walidacji poziomu trudności."""
        assert self.config_manager.validate_value('difficulty', 'Easy') is True
        assert self.config_manager.validate_value('difficulty', 'Normal') is True
        assert self.config_manager.validate_value('difficulty', 'Hard') is True
        assert self.config_manager.validate_value('difficulty', 'Invalid') is False
    
    def test_validate_language(self):
        """Test walidacji języka."""
        assert self.config_manager.validate_value('language', 'pl') is True
        assert self.config_manager.validate_value('language', 'en') is True
        assert self.config_manager.validate_value('language', 'invalid') is False
        assert self.config_manager.validate_value('language', 'toolong') is False
    
    def test_validate_positive_int(self):
        """Test walidacji liczb dodatnich."""
        assert self.config_manager.validate_value('window_width', 1600) is True
        assert self.config_manager.validate_value('window_width', '1600') is True
        assert self.config_manager.validate_value('window_width', 0) is False
        assert self.config_manager.validate_value('window_width', -100) is False
    
    def test_validate_file_path(self):
        """Test walidacji ścieżek plików."""
        assert self.config_manager.validate_value('db_path', 'city_builder.db') is True
        assert self.config_manager.validate_value('db_path', 'data/config.json') is True
        assert self.config_manager.validate_value('db_path', 'invalid_extension.txt') is False
    
    def test_save_and_load_config(self):
        """Test zapisywania i wczytywania konfiguracji."""
        # Zmień wartość
        self.config_manager.set('game_settings.difficulty', 'Hard')
        
        # Zapisz
        result = self.config_manager.save_config()
        assert result is True
        
        # Stwórz nowy manager i wczytaj
        new_manager = ConfigManager(self.config_path)
        assert new_manager.get('game_settings.difficulty') == 'Hard'
    
    def test_reset_to_defaults(self):
        """Test resetowania do wartości domyślnych."""
        # Zmień wartość
        self.config_manager.set('game_settings.difficulty', 'Hard')
        assert self.config_manager.get('game_settings.difficulty') == 'Hard'
        
        # Resetuj
        result = self.config_manager.reset_to_defaults()
        assert result is True
        assert self.config_manager.get('game_settings.difficulty') == 'Normal'
    
    def test_export_config(self):
        """Test eksportu konfiguracji."""
        export_path = os.path.join(self.temp_dir, 'exported_config.json')
        result = self.config_manager.export_config(export_path)
        assert result is True
        assert os.path.exists(export_path)
        
        # Sprawdź zawartość
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_config = json.load(f)
        assert 'game_settings' in exported_config
    
    def test_get_all_settings(self):
        """Test pobierania wszystkich ustawień."""
        settings = self.config_manager.get_all_settings()
        assert isinstance(settings, dict)
        assert 'game_settings' in settings
        assert 'ui_settings' in settings
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_config_file_not_found(self, mock_file):
        """Test obsługi braku pliku konfiguracji."""
        manager = ConfigManager('nonexistent.json')
        # Powinien utworzyć domyślną konfigurację
        assert manager.config is not None
        assert 'game_settings' in manager.config
    
    def test_load_invalid_json(self):
        """Test obsługi niepoprawnego JSON."""
        # Stwórz plik z niepoprawnym JSON
        with open(self.config_path, 'w') as f:
            f.write('invalid json content')
        
        manager = ConfigManager(self.config_path)
        # Powinien użyć domyślnej konfiguracji
        assert manager.config is not None
        assert manager.get('game_settings.difficulty') == 'Normal'
    
    def test_nested_key_creation(self):
        """Test tworzenia zagnieżdżonych kluczy."""
        result = self.config_manager.set('new_section.new_key', 'new_value')
        assert result is True
        assert self.config_manager.get('new_section.new_key') == 'new_value'
    
    def test_singleton_pattern(self):
        """Test wzorca singleton dla get_config_manager."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2


class TestConfigValidation:
    """Testy walidacji konfiguracji."""
    
    def setup_method(self):
        """Przygotowanie przed każdym testem."""
        self.config_manager = ConfigManager()
    
    def test_regex_patterns_compilation(self):
        """Test kompilacji wzorców regex."""
        # Sprawdź czy wszystkie wzorce się kompilują
        for pattern_name, pattern in self.config_manager.validators.items():
            assert pattern is not None
            # Test podstawowego dopasowania
            if pattern_name == 'difficulty':
                assert pattern.match('Normal') is not None
                assert pattern.match('Invalid') is None
    
    def test_boolean_validation(self):
        """Test walidacji wartości boolean."""
        assert self.config_manager.validate_value('enable_sound', True) is True
        assert self.config_manager.validate_value('enable_sound', False) is True
        # String boolean values nie są obsługiwane w tym teście
    
    def test_numeric_validation_edge_cases(self):
        """Test walidacji numerycznej - przypadki brzegowe."""
        # Zero nie jest dozwolone dla positive_int
        assert self.config_manager.validate_value('max_fps', 0) is False
        
        # Liczby ujemne nie są dozwolone
        assert self.config_manager.validate_value('max_fps', -60) is False
        
        # Bardzo duże liczby powinny być dozwolone
        assert self.config_manager.validate_value('max_fps', 999999) is True
    
    def test_path_validation_edge_cases(self):
        """Test walidacji ścieżek - przypadki brzegowe."""
        # Ścieżki z różnymi separatorami
        assert self.config_manager.validate_value('export_path', 'exports/') is True
        assert self.config_manager.validate_value('export_path', 'exports\\') is True
        
        # Ścieżki z podkatalogami
        assert self.config_manager.validate_value('custom_building_path', 'assets/custom_buildings/') is True


if __name__ == '__main__':
    pytest.main([__file__]) 