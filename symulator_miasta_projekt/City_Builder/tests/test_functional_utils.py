"""
Testy dla modułu programowania funkcyjnego.
"""

import pytest
import time
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.functional_utils import (
    safe_map, safe_filter, safe_reduce,
    building_generator, resource_flow_generator, event_sequence_generator,
    population_growth_generator, batch_generator,
    performance_monitor, retry_on_failure, memoize,
    analyze_building_efficiency, calculate_resource_trends, optimize_city_layout,
    validate_game_data, compose, curry, pipe
)

class TestHigherOrderFunctions:
    """Testy funkcji wyższego rzędu."""
    
    def test_safe_map_success(self):
        """Test safe_map z poprawnymi danymi."""
        data = [1, 2, 3, 4, 5]
        result = safe_map(lambda x: x * 2, data)
        assert result == [2, 4, 6, 8, 10]
    
    def test_safe_map_with_errors(self):
        """Test safe_map z błędami."""
        data = [1, 'invalid', 3, None, 5]
        result = safe_map(lambda x: x * 2, data)
        # Powinien pominąć błędne elementy
        assert len(result) < len(data)
        assert 2 in result  # 1 * 2
        assert 6 in result  # 3 * 2
        assert 10 in result  # 5 * 2
    
    def test_safe_filter_success(self):
        """Test safe_filter z poprawnymi danymi."""
        data = [1, 2, 3, 4, 5]
        result = safe_filter(lambda x: x > 3, data)
        assert result == [4, 5]
    
    def test_safe_filter_with_errors(self):
        """Test safe_filter z błędami."""
        data = [1, 'invalid', 3, None, 5]
        result = safe_filter(lambda x: x > 3, data)
        # Powinien pominąć błędne elementy i zwrócić tylko 5
        assert result == [5]
    
    def test_safe_reduce_success(self):
        """Test safe_reduce z poprawnymi danymi."""
        data = [1, 2, 3, 4, 5]
        result = safe_reduce(lambda a, b: a + b, data)
        assert result == 15
    
    def test_safe_reduce_with_initial(self):
        """Test safe_reduce z wartością początkową."""
        data = [1, 2, 3]
        result = safe_reduce(lambda a, b: a + b, data, 10)
        assert result == 16
    
    def test_safe_reduce_with_error(self):
        """Test safe_reduce z błędem."""
        data = [1, 'invalid', 3]
        result = safe_reduce(lambda a, b: a + b, data)
        assert result is None


class TestGenerators:
    """Testy generatorów."""
    
    def test_building_generator(self):
        """Test generatora budynków."""
        # Mock buildings
        building1 = Mock()
        building2 = None
        building3 = Mock()
        buildings = [building1, building2, building3]
        
        result = list(building_generator(buildings))
        assert len(result) == 2  # Powinien pominąć None
        assert building1 in result
        assert building3 in result
        assert building2 not in result
    
    def test_resource_flow_generator(self):
        """Test generatora przepływu zasobów."""
        resources = {'money': 1000, 'energy': 500}
        time_steps = 3
        
        results = list(resource_flow_generator(resources, time_steps))
        
        assert len(results) == 3
        assert all('step' in result for result in results)
        assert all('resources' in result for result in results)
        assert all('total_value' in result for result in results)
        
        # Sprawdź czy zasoby rosną
        assert results[1]['total_value'] > results[0]['total_value']
        assert results[2]['total_value'] > results[1]['total_value']
    
    def test_event_sequence_generator_no_repeat(self):
        """Test generatora sekwencji wydarzeń bez powtarzania."""
        events = [{'id': 1}, {'id': 2}, {'id': 3}]
        
        results = list(event_sequence_generator(events, repeat=False))
        
        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3
    
    def test_event_sequence_generator_with_repeat(self):
        """Test generatora sekwencji wydarzeń z powtarzaniem."""
        events = [{'id': 1}, {'id': 2}]
        
        generator = event_sequence_generator(events, repeat=True)
        
        # Pobierz pierwsze 5 elementów
        results = []
        for i, event in enumerate(generator):
            if i >= 5:
                break
            results.append(event)
        
        assert len(results) == 5
        # Sprawdź cykliczność
        assert results[0]['id'] == results[2]['id'] == results[4]['id'] == 1
        assert results[1]['id'] == results[3]['id'] == 2
    
    def test_population_growth_generator(self):
        """Test generatora wzrostu populacji."""
        initial_pop = 100
        growth_rate = 0.1
        max_steps = 5
        
        results = list(population_growth_generator(initial_pop, growth_rate, max_steps))
        
        assert len(results) == 5
        assert results[0] == (0, 100)
        
        # Sprawdź wzrost populacji
        for i in range(1, len(results)):
            step, population = results[i]
            prev_step, prev_population = results[i-1]
            assert step == i
            assert population > prev_population
    
    def test_batch_generator(self):
        """Test generatora partii."""
        data = list(range(10))  # [0, 1, 2, ..., 9]
        batch_size = 3
        
        batches = list(batch_generator(data, batch_size))
        
        assert len(batches) == 4  # 3 pełne partie + 1 niepełna
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]


class TestDecorators:
    """Testy dekoratorów."""
    
    def test_performance_monitor(self):
        """Test dekoratora monitorowania wydajności."""
        @performance_monitor
        def test_function():
            time.sleep(0.01)  # Krótkie opóźnienie
            return "result"
        
        with patch('builtins.print') as mock_print:
            result = test_function()
            assert result == "result"
            mock_print.assert_called()
            # Sprawdź czy wypisano informację o czasie wykonania
            call_args = mock_print.call_args[0][0]
            assert "test_function" in call_args
            assert "wykonana w" in call_args
    
    def test_retry_on_failure_success(self):
        """Test dekoratora retry - sukces za pierwszym razem."""
        @retry_on_failure(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_retry_on_failure_eventual_success(self):
        """Test dekoratora retry - sukces po kilku próbach."""
        call_count = 0
        
        @retry_on_failure(max_attempts=3, delay=0.001)
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = eventually_successful_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_failure_final_failure(self):
        """Test dekoratora retry - ostateczna porażka."""
        @retry_on_failure(max_attempts=2, delay=0.001)
        def always_failing_function():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_failing_function()
    
    def test_memoize(self):
        """Test dekoratora memoizacji."""
        call_count = 0
        
        @memoize
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Pierwsze wywołanie
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Drugie wywołanie z tymi samymi argumentami
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Nie powinno zwiększyć licznika
        
        # Wywołanie z innymi argumentami
        result3 = expensive_function(3)
        assert result3 == 6
        assert call_count == 2


class TestAnalyticalFunctions:
    """Testy funkcji analitycznych."""
    
    def test_analyze_building_efficiency_empty_list(self):
        """Test analizy efektywności - pusta lista."""
        result = analyze_building_efficiency([])
        assert result == {}
    
    def test_analyze_building_efficiency_no_active_buildings(self):
        """Test analizy efektywności - brak aktywnych budynków."""
        building1 = Mock()
        building1.is_active = False
        buildings = [building1]
        
        result = analyze_building_efficiency(buildings)
        assert 'error' in result
    
    def test_analyze_building_efficiency_with_active_buildings(self):
        """Test analizy efektywności - z aktywnymi budynkami."""
        building1 = Mock()
        building1.is_active = True
        building1.efficiency = 0.8
        
        building2 = Mock()
        building2.is_active = True
        building2.efficiency = 0.6
        
        buildings = [building1, building2]
        
        result = analyze_building_efficiency(buildings)
        
        assert 'total_buildings' in result
        assert 'active_buildings' in result
        assert 'average_efficiency' in result
        assert 'max_efficiency' in result
        assert 'min_efficiency' in result
        assert 'efficiency_distribution' in result
        
        assert result['total_buildings'] == 2
        assert result['active_buildings'] == 2
        assert result['average_efficiency'] == 0.7
        assert result['max_efficiency'] == 0.8
        assert result['min_efficiency'] == 0.6
    
    def test_calculate_resource_trends_insufficient_data(self):
        """Test obliczania trendów - niewystarczające dane."""
        history = [{'money': 1000}]  # Tylko jeden punkt
        result = calculate_resource_trends(history)
        assert result == {}
    
    def test_calculate_resource_trends_with_data(self):
        """Test obliczania trendów - z danymi."""
        history = [
            {'money': 1000, 'energy': 500},
            {'money': 1100, 'energy': 450},
            {'money': 1200, 'energy': 400}
        ]
        
        result = calculate_resource_trends(history)
        
        assert 'money' in result
        assert 'energy' in result
        
        money_trend = result['money']
        assert money_trend['trend_direction'] == 'growing'
        assert money_trend['total_change'] == 200
        assert money_trend['current_value'] == 1200
        
        energy_trend = result['energy']
        assert energy_trend['trend_direction'] == 'declining'
        assert energy_trend['total_change'] == -100
    
    def test_optimize_city_layout_empty_data(self):
        """Test optymalizacji układu - puste dane."""
        result = optimize_city_layout({})
        assert result == {}
    
    def test_optimize_city_layout_with_buildings(self):
        """Test optymalizacji układu - z budynkami."""
        building1 = Mock()
        building1.building_type = 'residential'
        building1.x = 10
        building1.y = 10
        
        building2 = Mock()
        building2.building_type = 'residential'
        building2.x = 15
        building2.y = 15
        
        city_data = {'buildings': [building1, building2]}
        
        result = optimize_city_layout(city_data)
        
        assert 'residential' in result
        residential_data = result['residential']
        assert 'count' in residential_data
        assert 'center_of_mass' in residential_data
        assert 'average_spread' in residential_data
        assert 'clustering_score' in residential_data
        assert 'recommendation' in residential_data


class TestValidationFunctions:
    """Testy funkcji walidacji."""
    
    def test_validate_game_data_valid_data(self):
        """Test walidacji - poprawne dane."""
        data = {
            'city_name': 'Warszawa',
            'resources': {
                'money': '1000',
                'energy': '500'
            },
            'buildings': [
                {
                    'name': 'Dom mieszkalny',
                    'x': '10',
                    'y': '15'
                }
            ]
        }
        
        errors = validate_game_data(data)
        
        # Nie powinno być błędów dla poprawnych danych
        assert len(errors) == 0 or all(len(error_list) == 0 for error_list in errors.values())
    
    def test_validate_game_data_invalid_city_name(self):
        """Test walidacji - niepoprawna nazwa miasta."""
        data = {
            'city_name': 'AB',  # Za krótka
        }
        
        errors = validate_game_data(data)
        assert 'city_name' in errors
        assert len(errors['city_name']) > 0
    
    def test_validate_game_data_invalid_resources(self):
        """Test walidacji - niepoprawne zasoby."""
        data = {
            'resources': {
                'invalid-resource-name': '1000',  # Niepoprawna nazwa
                'money': 'invalid_amount'  # Niepoprawna ilość
            }
        }
        
        errors = validate_game_data(data)
        assert 'resources' in errors
        assert len(errors['resources']) > 0
    
    def test_validate_game_data_invalid_buildings(self):
        """Test walidacji - niepoprawne budynki."""
        data = {
            'buildings': [
                {
                    'name': 'A',  # Za krótka nazwa
                    'x': '999',  # Niepoprawna współrzędna
                    'y': 'invalid'  # Niepoprawna współrzędna
                }
            ]
        }
        
        errors = validate_game_data(data)
        assert 'buildings' in errors
        assert len(errors['buildings']) > 0


class TestUtilityFunctions:
    """Testy funkcji pomocniczych."""
    
    def test_compose(self):
        """Test kompozycji funkcji."""
        add_one = lambda x: x + 1
        multiply_two = lambda x: x * 2
        
        composed = compose(multiply_two, add_one)
        result = composed(5)
        
        # (5 + 1) * 2 = 12
        assert result == 12
    
    def test_curry(self):
        """Test curry funkcji."""
        def add_three(a, b, c):
            return a + b + c
        
        curried_add = curry(add_three)
        
        # Częściowa aplikacja
        add_5_and_3 = curried_add(5)(3)
        result = add_5_and_3(2)
        
        assert result == 10
    
    def test_pipe(self):
        """Test pipe funkcji."""
        add_one = lambda x: x + 1
        multiply_two = lambda x: x * 2
        subtract_three = lambda x: x - 3
        
        result = pipe(5, add_one, multiply_two, subtract_three)
        
        # 5 -> 6 -> 12 -> 9
        assert result == 9


if __name__ == '__main__':
    pytest.main([__file__]) 