"""
Moduł narzędzi programowania funkcyjnego dla City Builder.
Zawiera funkcje wyższego rzędu, generatory i narzędzia funkcyjne.

Programowanie funkcyjne to paradygmat programowania gdzie:
- Funkcje są "obywatelami pierwszej klasy" (można je przekazywać jako argumenty)
- Unika się mutacji stanu (immutability)
- Używa się funkcji czystych (pure functions) bez efektów ubocznych
- Kompozycja funkcji zamiast dziedziczenia
- Deklaratywny styl zamiast imperatywnego

Ten moduł implementuje:
- Bezpieczne wersje map/filter/reduce z obsługą błędów
- Generatory do efektywnego przetwarzania dużych zbiorów danych
- Dekoratory do monitorowania wydajności i cache'owania
- Funkcje kompozycji i currying
- Narzędzia analizy danych miasta
"""

from functools import reduce, wraps
from typing import (
    Any, Callable, Dict, Generator, Iterable, List, Optional, 
    Tuple, TypeVar, Union
)
import time
import re
from itertools import islice, cycle, chain
from collections import defaultdict

# TypeVar pozwala na definiowanie generycznych typów
# T i U to "placeholder'y" dla dowolnych typów
T = TypeVar('T')  # typ wejściowy
U = TypeVar('U')  # typ wyjściowy

# ============================================================================
# FUNKCJE WYŻSZEGO RZĘDU (map, filter, reduce)
# Funkcje wyższego rzędu to funkcje, które przyjmują inne funkcje jako argumenty
# ============================================================================

def safe_map(func: Callable[[T], U], iterable: Iterable[T]) -> List[U]:
    """
    Bezpieczna wersja map() z obsługą błędów.
    
    Args:
        func: funkcja do zastosowania na każdym elemencie
        iterable: kolekcja elementów do przetworzenia (lista, tuple, generator)
        
    Returns:
        List[U]: lista wyników transformacji
        
    Różnica od standardowego map():
    - Standardowy map() przerywa działanie przy pierwszym błędzie
    - safe_map() kontynuuje przetwarzanie, pomijając błędne elementy
    - Loguje błędy dla debugowania
    
    Przykład:
        numbers = [1, 2, "błąd", 4, 5]
        squared = safe_map(lambda x: x**2, numbers)  # [1, 4, 16, 25]
    """
    results = []  # lista wyników
    for item in iterable:
        try:
            # Zastosuj funkcję do elementu i dodaj wynik
            results.append(func(item))
        except Exception as e:
            # W przypadku błędu, zaloguj i kontynuuj
            print(f"Błąd w safe_map dla {item}: {e}")
            continue  # przejdź do następnego elementu
    return results

def safe_filter(predicate: Callable[[T], bool], iterable: Iterable[T]) -> List[T]:
    """
    Bezpieczna wersja filter() z obsługą błędów.
    
    Args:
        predicate: funkcja zwracająca True/False (predykat) do filtrowania
        iterable: kolekcja elementów do przefiltrowania
        
    Returns:
        List[T]: lista elementów spełniających warunek
        
    Predykat to funkcja logiczna sprawdzająca warunek.
    
    Przykład:
        buildings = [dom, fabryka, None, park]
        valid_buildings = safe_filter(lambda b: b is not None, buildings)
    """
    results = []
    for item in iterable:
        try:
            # Sprawdź warunek i dodaj element jeśli spełnia
            if predicate(item):
                results.append(item)
        except Exception as e:
            print(f"Błąd w safe_filter dla {item}: {e}")
            continue
    return results

def safe_reduce(func: Callable[[T, T], T], iterable: Iterable[T], initial: Optional[T] = None) -> Optional[T]:
    """
    Bezpieczna wersja reduce() z obsługą błędów.
    
    Args:
        func: funkcja redukcji przyjmująca 2 argumenty i zwracająca 1
        iterable: kolekcja do zredukowania
        initial: wartość początkowa (opcjonalna)
        
    Returns:
        Optional[T]: zredukowana wartość lub None w przypadku błędu
        
    Reduce to funkcja "składająca" listę w jedną wartość:
    reduce(+, [1,2,3,4]) = ((1+2)+3)+4 = 10
    
    Przykład:
        total_population = safe_reduce(lambda a, b: a + b.population, buildings, 0)
    """
    try:
        if initial is not None:
            return reduce(func, iterable, initial)
        else:
            return reduce(func, iterable)
    except Exception as e:
        print(f"Błąd w safe_reduce: {e}")
        return None

# ============================================================================
# GENERATORY
# Generator to funkcja która "yield'uje" wartości zamiast je zwracać
# Pozwala na przetwarzanie dużych zbiorów danych bez ładowania wszystkiego do pamięci
# ============================================================================

def building_generator(buildings: List[Any]) -> Generator[Any, None, None]:
    """
    Generator budynków z filtrowaniem pustych wartości.
    
    Args:
        buildings: lista budynków (może zawierać None)
        
    Yields:
        Any: budynki jeden po drugim (pomija None)
        
    Generator vs zwykła funkcja:
    - Zwykła funkcja: return [building for building in buildings if building]
    - Generator: yield building (jeden na raz, oszczędza pamięć)
    
    Użycie:
        for building in building_generator(all_buildings):
            process_building(building)
    """
    for building in buildings:
        if building is not None:  # filtruj puste wartości
            yield building  # "zwróć" budynek i wstrzymaj wykonanie

def resource_flow_generator(resources: Dict[str, float], 
                          time_steps: int) -> Generator[Dict[str, float], None, None]:
    """
    Generator symulujący przepływ zasobów w czasie.
    
    Args:
        resources: słownik zasobów {nazwa: ilość}
        time_steps: liczba kroków czasowych do symulacji
        
    Yields:
        Dict: stan zasobów w każdym kroku czasowym
        
    Symuluje zmiany zasobów w czasie (wzrost/spadek).
    Użyteczne do prognozowania rozwoju miasta.
    """
    current_resources = resources.copy()  # kopia aby nie modyfikować oryginału
    
    for step in range(time_steps):
        # Symuluj zmiany zasobów (przykładowa logika)
        for resource, amount in current_resources.items():
            # Wzrost zasobów w czasie (1% na krok + bonus za czas)
            change_rate = 0.01 * (step + 1)  # rate rośnie z czasem
            current_resources[resource] = amount * (1 + change_rate)
        
        # Yield słownik ze stanem w danym kroku
        yield {
            'step': step,
            'resources': current_resources.copy(),  # kopia aktualnego stanu
            'total_value': sum(current_resources.values())  # suma wszystkich zasobów
        }

def event_sequence_generator(events: List[Dict], 
                           repeat: bool = False) -> Generator[Dict, None, None]:
    """
    Generator sekwencji wydarzeń.
    
    Args:
        events: lista wydarzeń do wygenerowania
        repeat: czy powtarzać sekwencję w nieskończoność
        
    Yields:
        Dict: wydarzenia w sekwencji
        
    Użyteczne do skryptowanych sekwencji wydarzeń w grze.
    Z repeat=True można stworzyć cykliczne wydarzenia (np. pory roku).
    """
    if repeat:
        # cycle() z itertools tworzy nieskończony cykl
        event_cycle = cycle(events)  # [A,B,C] -> A,B,C,A,B,C,A,B,C...
        while True:
            yield next(event_cycle)  # następne wydarzenie z cyklu
    else:
        # Jednorazowe przejście przez wydarzenia
        for event in events:
            yield event

def population_growth_generator(initial_population: int, 
                              growth_rate: float,
                              max_steps: int = 100) -> Generator[Tuple[int, int], None, None]:
    """
    Generator wzrostu populacji z modelem eksponencjalnym.
    
    Args:
        initial_population: początkowa liczba mieszkańców
        growth_rate: współczynnik wzrostu na krok (np. 0.02 = 2% wzrostu)
        max_steps: maksymalna liczba kroków symulacji
        
    Yields:
        Tuple[int, int]: (numer_kroku, populacja)
        
    Model wzrostu eksponencjalnego: P(t) = P₀ * (1 + r)^t
    gdzie P₀=populacja początkowa, r=rate wzrostu, t=czas
    """
    population = initial_population
    
    for step in range(max_steps):
        yield (step, int(population))  # zwróć krokowo stan populacji
        population *= (1 + growth_rate)  # wzrost eksponencjalny
        
        # Ograniczenie wzrostu (model logistyczny)
        if population > 1000000:  # maksymalna populacja = 1M
            break  # przerwij symulację

def batch_generator(iterable: Iterable[T], batch_size: int) -> Generator[List[T], None, None]:
    """
    Generator dzielący dużą kolekcję na mniejsze partie (batches).
    
    Args:
        iterable: kolekcja do podziału
        batch_size: rozmiar każdej partii
        
    Yields:
        List[T]: partie elementów o zadanym rozmiarze
        
    Użyteczne przy przetwarzaniu dużych zbiorów danych:
    - Oszczędza pamięć
    - Pozwala na przetwarzanie równoległe
    - Lepsze dla baz danych (batch insert/update)
    
    Przykład:
        for batch in batch_generator(all_buildings, 50):
            process_building_batch(batch)  # przetwórz 50 budynków na raz
    """
    iterator = iter(iterable)  # stwórz iterator z kolekcji
    while True:
        # islice() pobiera określoną liczbę elementów z iteratora
        batch = list(islice(iterator, batch_size))
        if not batch:  # jeśli brak elementów, koniec
            break
        yield batch  # zwróć partię

# ============================================================================
# DEKORATORY I FUNKCJE WYŻSZEGO RZĘDU
# Dekorator to funkcja modyfikująca zachowanie innej funkcji
# ============================================================================

def performance_monitor(func: Callable) -> Callable:
    """
    Dekorator monitorujący wydajność funkcji.
    
    Args:
        func: funkcja do ozdobienia
        
    Returns:
        Callable: funkcja z dodanym monitorowaniem czasu wykonania
        
    Dekorator to "wrapper" - funkcja opakowująca inną funkcję.
    Pozwala dodać funkcjonalność bez modyfikowania oryginalnego kodu.
    
    Użycie:
        @performance_monitor
        def slow_function():
            time.sleep(1)
            
    Wypisze: "slow_function wykonana w 1.00s"
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            print(f"Funkcja {func.__name__} wykonana w {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Błąd w {func.__name__} po {execution_time:.4f}s: {e}")
            raise
    return wrapper

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    Dekorator ponawiający wykonanie funkcji w przypadku błędu.
    
    Args:
        max_attempts: Maksymalna liczba prób
        delay: Opóźnienie między próbami
        
    Returns:
        Dekorator
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Próba {attempt + 1} nieudana dla {func.__name__}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def memoize(func: Callable) -> Callable:
    """
    Dekorator memoizacji (cache wyników).
    
    Args:
        func: Funkcja do memoizacji
        
    Returns:
        Funkcja z cache
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Tworzenie klucza cache
        key = str(args) + str(sorted(kwargs.items()))
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cache[key]
    
    return wrapper

# ============================================================================
# FUNKCJE ANALITYCZNE Z PROGRAMOWANIEM FUNKCYJNYM
# ============================================================================

def analyze_building_efficiency(buildings: List[Any]) -> Dict[str, Any]:
    """
    Analizuje efektywność budynków używając funkcji wyższego rzędu.
    
    Funkcja demonstruje programowanie funkcyjne w praktyce:
    - filter() do filtrowania aktywnych budynków
    - map() do ekstraktowania wartości efektywności
    - reduce() do agregacji statystyk
    - lambdy do zwięzłych transformacji
    
    Args:
        buildings: lista budynków miasta do analizy
        
    Returns:
        Dict[str, Any]: słownik z analizą efektywności zawierający:
        - Ogólne statystyki (liczby budynków)
        - Wskaźniki efektywności (średnia, min, max)  
        - Rozkład efektywności (wysokie/średnie/niskie)
    """
    if not buildings:  # jeśli brak budynków
        return {}
    
    # Filtruj tylko aktywne budynki używając lambda w filter()
    # Lambda sprawdza czy budynek ma atrybut 'is_active' i czy jest True
    active_buildings = list(filter(lambda b: hasattr(b, 'is_active') and b.is_active, buildings))
    
    if not active_buildings:  # jeśli brak aktywnych budynków
        return {'error': 'Brak aktywnych budynków'}
    
    # Mapuj budynki na ich efektywność używając lambda w map()
    # Lambda pobiera efficiency lub domyślną wartość 0.5
    efficiencies = list(map(
        lambda b: getattr(b, 'efficiency', 0.5) if hasattr(b, 'efficiency') else 0.5,
        active_buildings
    ))
    
    # Oblicz statystyki używając reduce() z lambdami
    # Reduce "składa" listę w jedną wartość używając funkcji agregującej
    total_efficiency = reduce(lambda a, b: a + b, efficiencies, 0)  # suma wszystkich wartości
    avg_efficiency = total_efficiency / len(efficiencies)  # średnia efektywność
    
    # Znajdź najlepsze i najgorsze budynki używając reduce() z lambdami
    max_efficiency = reduce(lambda a, b: max(a, b), efficiencies)  # maksymalna efektywność
    min_efficiency = reduce(lambda a, b: min(a, b), efficiencies)  # minimalna efektywność
    
    return {
        'total_buildings': len(buildings),  # wszystkie budynki
        'active_buildings': len(active_buildings),  # tylko aktywne
        'average_efficiency': avg_efficiency,  # średnia efektywność
        'max_efficiency': max_efficiency,  # najlepsza efektywność
        'min_efficiency': min_efficiency,  # najgorsza efektywność
        'efficiency_distribution': {  # rozkład efektywności
            # Wysokie efektywność (>80%) - używa filter() z lambdą
            'high': len(list(filter(lambda e: e > 0.8, efficiencies))),
            # Średnia efektywność (50-80%) - używa filter() z lambdą
            'medium': len(list(filter(lambda e: 0.5 <= e <= 0.8, efficiencies))),
            # Niska efektywność (<50%) - używa filter() z lambdą  
            'low': len(list(filter(lambda e: e < 0.5, efficiencies)))
        }
    }

def calculate_resource_trends(resource_history: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Oblicza trendy zasobów używając programowania funkcyjnego.
    
    Args:
        resource_history: Historia zasobów
        
    Returns:
        Analiza trendów
    """
    if len(resource_history) < 2:
        return {}
    
    # Pobierz wszystkie typy zasobów
    all_resources = set()
    for entry in resource_history:
        all_resources.update(entry.keys())
    
    trends = {}
    
    for resource in all_resources:
        # Wyciągnij wartości dla danego zasobu
        values = list(map(
            lambda entry: entry.get(resource, 0),
            resource_history
        ))
        
        if len(values) < 2:
            continue
        
        # Oblicz zmiany między kolejnymi wartościami
        changes = list(map(
            lambda i: values[i] - values[i-1],
            range(1, len(values))
        ))
        
        # Oblicz statystyki zmian
        total_change = reduce(lambda a, b: a + b, changes, 0)
        avg_change = total_change / len(changes)
        
        # Określ trend
        positive_changes = list(filter(lambda c: c > 0, changes))
        negative_changes = list(filter(lambda c: c < 0, changes))
        
        trend_direction = 'stable'
        if len(positive_changes) > len(negative_changes):
            trend_direction = 'growing'
        elif len(negative_changes) > len(positive_changes):
            trend_direction = 'declining'
        
        trends[resource] = {
            'total_change': total_change,
            'average_change': avg_change,
            'trend_direction': trend_direction,
            'volatility': len(changes) - len(list(filter(lambda c: abs(c) < 0.1, changes))),
            'current_value': values[-1],
            'peak_value': reduce(lambda a, b: max(a, b), values),
            'lowest_value': reduce(lambda a, b: min(a, b), values)
        }
    
    return trends

def optimize_city_layout(city_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optymalizuje układ miasta używając funkcji funkcyjnych.
    
    Args:
        city_data: Dane miasta
        
    Returns:
        Rekomendacje optymalizacji
    """
    buildings = city_data.get('buildings', [])
    if not buildings:
        return {}
    
    # Grupuj budynki według typu
    building_groups = defaultdict(list)
    for building in buildings:
        building_type = getattr(building, 'building_type', 'unknown')
        building_groups[building_type].append(building)
    
    recommendations = {}
    
    for building_type, type_buildings in building_groups.items():
        # Analizuj rozmieszczenie budynków tego typu
        positions = list(map(
            lambda b: (getattr(b, 'x', 0), getattr(b, 'y', 0)),
            type_buildings
        ))
        
        if len(positions) < 2:
            continue
        
        # Oblicz średnią pozycję (centrum masy)
        avg_x = reduce(lambda a, b: a + b, map(lambda p: p[0], positions)) / len(positions)
        avg_y = reduce(lambda a, b: a + b, map(lambda p: p[1], positions)) / len(positions)
        
        # Oblicz rozproszenie
        distances = list(map(
            lambda p: ((p[0] - avg_x) ** 2 + (p[1] - avg_y) ** 2) ** 0.5,
            positions
        ))
        
        avg_distance = reduce(lambda a, b: a + b, distances) / len(distances)
        
        recommendations[building_type] = {
            'count': len(type_buildings),
            'center_of_mass': (avg_x, avg_y),
            'average_spread': avg_distance,
            'clustering_score': 1.0 / (1.0 + avg_distance),  # Wyższy = bardziej skupione
            'recommendation': 'cluster_more' if avg_distance > 10 else 'well_clustered'
        }
    
    return recommendations

# ============================================================================
# NARZĘDZIA WALIDACJI Z REGEX
# ============================================================================

def validate_game_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Waliduje dane gry używając wyrażeń regularnych.
    
    Args:
        data: Dane do walidacji
        
    Returns:
        Słownik błędów walidacji
    """
    errors = defaultdict(list)
    
    # Wzorce regex dla walidacji
    patterns = {
        'city_name': re.compile(r'^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s]{3,30}$'),
        'resource_name': re.compile(r'^[a-z_]{3,20}$'),
        'building_name': re.compile(r'^[a-zA-Z\s]{3,50}$'),
        'positive_number': re.compile(r'^[1-9]\d*$'),
        'decimal_number': re.compile(r'^\d+\.?\d*$'),
        'coordinate': re.compile(r'^[0-9]{1,3}$'),
        'percentage': re.compile(r'^(100|[1-9]?\d)$')
    }
    
    # Walidacja nazwy miasta
    if 'city_name' in data:
        if not patterns['city_name'].match(str(data['city_name'])):
            errors['city_name'].append('Nazwa miasta musi mieć 3-30 znaków i zawierać tylko litery')
    
    # Walidacja zasobów
    if 'resources' in data and isinstance(data['resources'], dict):
        for resource_name, amount in data['resources'].items():
            if not patterns['resource_name'].match(resource_name):
                errors['resources'].append(f'Niepoprawna nazwa zasobu: {resource_name}')
            
            if not patterns['decimal_number'].match(str(amount)):
                errors['resources'].append(f'Niepoprawna ilość zasobu {resource_name}: {amount}')
    
    # Walidacja budynków
    if 'buildings' in data and isinstance(data['buildings'], list):
        for i, building in enumerate(data['buildings']):
            if isinstance(building, dict):
                # Walidacja pozycji
                for coord in ['x', 'y']:
                    if coord in building:
                        if not patterns['coordinate'].match(str(building[coord])):
                            errors['buildings'].append(f'Niepoprawna współrzędna {coord} budynku {i}')
                
                # Walidacja nazwy
                if 'name' in building:
                    if not patterns['building_name'].match(str(building['name'])):
                        errors['buildings'].append(f'Niepoprawna nazwa budynku {i}')
    
    return dict(errors)

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def compose(*functions):
    """
    Komponuje funkcje (kompozycja funkcyjna).
    
    Args:
        *functions: Funkcje do skomponowania
        
    Returns:
        Skomponowana funkcja
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)

def curry(func: Callable) -> Callable:
    """
    Currying funkcji (częściowa aplikacja).
    
    Args:
        func: Funkcja do curry
        
    Returns:
        Funkcja curry
    """
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= func.__code__.co_argcount:
            return func(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(*(args + more_args), **{**kwargs, **more_kwargs})
    return curried

def pipe(value: Any, *functions) -> Any:
    """
    Przepuszcza wartość przez sekwencję funkcji.
    
    Args:
        value: Wartość początkowa
        *functions: Funkcje do zastosowania
        
    Returns:
        Przetworzona wartość
    """
    return reduce(lambda v, f: f(v), functions, value) 