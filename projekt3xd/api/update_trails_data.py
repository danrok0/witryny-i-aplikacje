"""
SKRYPT AKTUALIZACJI DANYCH O SZLAKACH TURYSTYCZNYCH
==================================================

Ten skrypt służy do pobierania i aktualizacji danych o szlakach turystycznych
dla wszystkich regionów zdefiniowanych w konfiguracji systemu.

FUNKCJONALNOŚĆ:
- Pobiera dane o szlakach dla wszystkich miast z CITY_COORDINATES
- Agreguje dane z różnych regionów w jedną listę
- Zapisuje wszystkie dane do pliku trails_data.json
- Obsługuje błędy pobierania dla poszczególnych regionów

UŻYCIE:
python api/update_trails_data.py

WYMAGANIA:
- Działające połączenie internetowe
- Dostęp do Overpass API
- Uprawnienia do zapisu w katalogu głównym projektu

AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# KONFIGURACJA ŚCIEŻEK I IMPORTÓW
# ============================================================================

# Dodanie katalogu głównego projektu do ścieżki Python
# Umożliwia import modułów z katalogu nadrzędnego
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# IMPORTY MODUŁÓW PROJEKTU
# ============================================================================

from api.trails_api import TrailsAPI         # Klasa do pobierania danych o szlakach
from config import CITY_COORDINATES         # Słownik miast i ich współrzędnych
import json                                 # Obsługa formatu JSON

# ============================================================================
# GŁÓWNA FUNKCJA AKTUALIZACJI DANYCH
# ============================================================================

def update_trails_data():
    """
    Pobiera i aktualizuje dane o szlakach turystycznych dla wszystkich regionów.
    
    Funkcja iteruje przez wszystkie miasta zdefiniowane w CITY_COORDINATES,
    pobiera dla każdego z nich dane o szlakach używając TrailsAPI,
    a następnie zapisuje zagregowane dane do pliku JSON.
    
    Proces:
    1. Inicjalizacja API i pustej listy na wszystkie szlaki
    2. Iteracja przez wszystkie regiony z CITY_COORDINATES
    3. Pobieranie szlaków dla każdego regionu (z obsługą błędów)
    4. Agregacja wszystkich szlaków w jedną listę
    5. Zapis do pliku trails_data.json
    
    Obsługa błędów:
    - Błędy pobierania dla poszczególnych regionów nie przerywają procesu
    - Wszystkie błędy są logowane z informacją o regionie
    - Proces kontynuuje dla pozostałych regionów
    
    Returns:
        None: Funkcja zapisuje dane do pliku, nie zwraca wartości
    """
    # Inicjalizacja API do pobierania danych o szlakach
    api = TrailsAPI()
    
    # Lista na wszystkie szlaki ze wszystkich regionów
    all_trails = []

    print("Pobieranie danych o szlakach dla wszystkich regionów...")
    
    # ========================================================================
    # ITERACJA PRZEZ WSZYSTKIE REGIONY
    # ========================================================================
    
    # Pobieranie szlaków dla każdego miasta z konfiguracji
    for region in CITY_COORDINATES.keys():
        print(f"\nPobieranie szlaków dla regionu: {region}")
        
        try:
            # Próba pobrania szlaków dla danego regionu
            trails = api.get_hiking_trails(region)
            
            # Dodanie pobranych szlaków do głównej listy
            all_trails.extend(trails)
            
            # Informacja o liczbie znalezionych szlaków
            print(f"Znaleziono {len(trails)} szlaków dla {region}")
            
        except Exception as e:
            # Obsługa błędów - logowanie i kontynuacja
            print(f"Błąd podczas pobierania szlaków dla {region}: {e}")
            # Proces kontynuuje dla pozostałych regionów

    # ========================================================================
    # PODSUMOWANIE I ZAPIS DANYCH
    # ========================================================================
    
    print(f"\nŁącznie znaleziono {len(all_trails)} szlaków")

    # Zapis wszystkich danych do pliku JSON
    try:
        with open('trails_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_trails, f, ensure_ascii=False, indent=2)
        print("Dane zostały zapisane do pliku trails_data.json")
        
    except Exception as e:
        print(f"Błąd podczas zapisywania danych: {e}")

# ============================================================================
# PUNKT WEJŚCIA SKRYPTU
# ============================================================================

if __name__ == "__main__":
    """
    Punkt wejścia skryptu - wykonuje aktualizację danych gdy skrypt jest uruchamiany bezpośrednio.
    
    Sprawdza czy skrypt jest uruchamiany jako główny program (nie importowany)
    i jeśli tak, wywołuje funkcję update_trails_data().
    """
    update_trails_data() 