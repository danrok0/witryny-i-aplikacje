# 🏔️ System Rekomendacji Szlaków Turystycznych - ETAP 4

## 🎯 Opis Projektu
System rekomendacji szlaków turystycznych to zaawansowane narzędzie wykorzystujące **bazę danych SQLite**, które pomaga użytkownikom znaleźć idealne trasy na podstawie ich preferencji, warunków pogodowych i innych kryteriów.

## 🚀 **NOWOŚCI W ETAPIE 4 - INTEGRACJA BAZY DANYCH**
- **💾 Baza danych SQLite** z pełną infrastrukturą zarządzania danymi
- **🔄 Automatyczna integracja API** - nowe trasy zapisywane bezpośrednio do bazy
- **📊 Ponad 3900+ tras** w bazie danych (wzrost z 320 tras!)
- **🏗️ Wzorzec Repository** dla separacji logiki biznesowej od dostępu do danych
- **🔧 Narzędzia administracyjne** do zarządzania bazą danych
- **📈 Rozbudowane statystyki** i analityki systemowe

## 🛠️ Wymagania systemowe
- **Python 3.8 lub nowszy**
- **pip** (menedżer pakietów Pythona)
- **SQLite** (wbudowany w Python)
- **Dostęp do internetu** (do pobierania danych pogodowych i tras)

## ⚡ Szybka instalacja

### 1. Pobierz projekt
```powershell
git clone <adres-repozytorium>
cd projekt3xd
```

### 2. Zainstaluj zależności
```powershell
pip install -r requirements.txt
```

### 3. Uruchom system
```powershell
python main.py
```

## 📊 Struktura bazy danych

### Główne tabele:
- **🗺️ routes** - Trasy turystyczne (3900+ rekordów)
- **🌤️ weather_data** - Dane pogodowe
- **📝 reviews** - Recenzje tras
- **👤 user_preferences** - Preferencje użytkowników
- **🏔️ route_difficulty** - Oceny trudności tras

### Baza danych znajduje się w:
```
data/database/routes.db
```

## 🏗️ Architektura systemu

### Wzorzec Repository
```
database/
├── database_manager.py      # Główny menedżer bazy danych
├── database_admin.py        # Narzędzia administracyjne
├── migration_tool.py        # Migracje danych
└── repositories/
    ├── route_repository.py      # Operacje na trasach
    ├── weather_repository.py    # Operacje na danych pogodowych
    └── user_repository.py       # Operacje na użytkownikach
```

### Integracja API z bazą danych
```
api/
├── trails_api.py           # Pobieranie tras → automatyczny zapis do bazy
├── weather_api.py          # Pobieranie pogody → automatyczny zapis do bazy
└── update_data.py          # Kompleksowa aktualizacja danych
```

## 🎮 Jak używać systemu

### 1. Pierwsze uruchomienie
```powershell
python main.py
```
System automatycznie:
- Inicjalizuje bazę danych SQLite
- Sprawdza dostępność ponad 3900 tras
- Uruchamia menu główne

### 2. Dostępne opcje w menu:
1. **🎯 Standardowe rekomendacje tras** - główna funkcja systemu
2. **➕ Dodaj nową trasę** - rozszerzenie bazy danych
3. **📊 Statystyki bazy danych** - analiza danych systemowych
4. **💾 Utwórz kopię zapasową** - zabezpieczenie danych
5. **📥 Importuj dane z plików** - migracja danych
6. **📄 Rekomendacje z raportem PDF** - profesjonalne raporty
7. **🔍 Analiza konkretnej trasy** - szczegółowe informacje
8. **🗂️ Przeglądaj trasy w bazie danych** - eksploracja danych
9. **🌐 Zbieranie danych z internetu** - aktualizacja przez API
10. **📈 Generowanie wykresów** - wizualizacja danych
11. **🔧 Demonstracja przetwarzania tekstu** - funkcje NLP

### 3. Proces rekomendacji:
1. Wybierz region (Gdańsk, Warszawa, Kraków, Wrocław)
2. Wybierz kategorię trasy (rodzinna, widokowa, sportowa, ekstremalna)
3. Ustaw kryteria oceny (trudność, długość, warunki pogodowe)
4. Otrzymaj spersonalizowane rekomendacje

## 🔄 Aktualizacja danych

### Automatyczna aktualizacja API
```powershell
python api/update_data.py
```
**Nowe funkcje:**
- Automatyczny zapis do bazy danych SQLite
- Pobieranie tysięcy nowych tras z OpenStreetMap
- Aktualizacja prognoz pogody
- Backup do plików JSON

### Ręczna aktualizacja z menu
- Opcja **9. Zbieranie danych z internetu**
- Pobiera najnowsze trasy i automatycznie zapisuje do bazy

## 📈 Statystyki systemu

### Aktualne dane w bazie:
- **🏔️ Liczba tras**: 3900+ (wzrost z 320!)
- **🗺️ Regiony**: Gdańsk (3800+), Warszawa, Kraków, Wrocław
- **⚡ Rozkład trudności**: Łatwe (85%), Średnie (10%), Trudne (5%)
- **📁 Rozmiar bazy**: ~15 MB

### Dostęp do statystyk:
```powershell
python main.py
# Wybierz opcję: 3. Statystyki bazy danych
```

## 🎯 Wyniki rekomendacji

System generuje rekomendacje w trzech formatach:
- **📄 Plik tekstowy** (.txt) - czytelny raport
- **📊 Plik JSON** (.json) - dane strukturalne
- **📋 Plik CSV** (.csv) - dane tabelaryczne

## 🔧 Rozwiązywanie problemów

### Problemy z bazą danych:
```powershell
# Sprawdź integralność bazy
python main.py
# Wybierz: 3 → 1 (Sprawdź integralność)

# Optymalizuj bazę danych
python main.py  
# Wybierz: 3 → 2 (Optymalizuj bazę)
```

### Problemy z modułami:
```powershell
pip install -r requirements.txt --upgrade
```

### Problemy z danymi:
```powershell
# Wyczyść cache i pobierz świeże dane
python manage_cache.py clear
python api/update_data.py
```

### Problemy z API:
```powershell
# Sprawdź połączenie z API
python -c "from api.trails_api import TrailsAPI; api = TrailsAPI(); print('API OK')"
```

## 🏆 Zaawansowane funkcje

### 1. Zarządzanie bazą danych
- **Backup automatyczny** - System tworzy kopie zapasowe
- **Migracje danych** - Bezpieczna aktualizacja struktury
- **Optymalizacja** - Indeksy i triggery dla wydajności

### 2. Analiza danych
- **Wizualizacje** - Wykresy rozkładu tras
- **Statystyki regionalne** - Porównanie regionów
- **Trendy pogodowe** - Analiza warunków optymalnych

### 3. Integracja zewnętrzna
- **OpenStreetMap API** - Ponad 50 typów tras
- **Open-Meteo API** - Prognozy pogody 7-dniowe
- **Automatyczne kategorie** - AI klasyfikacja tras

## 📖 Dokumentacja

### Pliki dokumentacji:
- **`README.md`** - Ten plik (podstawy)
- **`DOCUMENTATION.md`** - Szczegółowa dokumentacja techniczna
- **`sql/schema.sql`** - Struktura bazy danych
- **`POPRAWKI_ETAP4.md`** - Changelog najnowszych zmian

### Dokumentacja w kodzie:
- Wszystkie klasy i metody zawierają docstrings
- Komentarze wyjaśniające logikę biznesową
- Przykłady użycia w plikach testowych

## 🎨 Przykład użycia

```python
# Przykład pracy z bazą danych
from database import DatabaseManager
from database.repositories.route_repository import RouteRepository

# Inicjalizacja
db_manager = DatabaseManager()
db_manager.initialize_database()
route_repo = RouteRepository(db_manager)

# Pobieranie tras
trails = route_repo.find_routes_by_region("Gdańsk", limit=10)
print(f"Znaleziono {len(trails)} tras w Gdańsku")

# Dodawanie nowej trasy
new_trail = {
    'name': 'Moja Trasa',
    'region': 'Gdańsk',
    'length_km': 5.0,
    'difficulty': 2,
    'terrain_type': 'leśna'
}
trail_id = route_repo.add_route(new_trail)
print(f"Dodano trasę z ID: {trail_id}")
```

## 🎓 Wsparcie i pomoc

### W razie problemów:
1. **Sprawdź logi** - System wyświetla szczegółowe informacje o błędach
2. **Consulte dokumentację** - `DOCUMENTATION.md` zawiera wszystkie szczegóły
3. **Testuj połączenia** - Sprawdź dostęp do API i bazy danych
4. **Resetuj dane** - Użyj opcji czyszczenia cache

### Struktura projektu po aktualizacji:
```
projekt3xd/
├── main.py              # Punkt wejścia systemu
├── requirements.txt     # Zależności Python
├── config.py           # Konfiguracja API i bazy danych
├── database/           # 🆕 Infrastruktura bazy danych
│   ├── database_manager.py
│   ├── database_admin.py
│   └── repositories/
├── api/                # 🆕 Zintegrowane API z bazą danych
│   ├── trails_api.py
│   ├── weather_api.py
│   └── update_data.py
├── data/               # Dane aplikacji
│   └── database/
│       └── routes.db   # 🆕 Główna baza danych SQLite
├── sql/                # 🆕 Skrypty SQL
│   └── schema.sql
└── recommendation/     # Silnik rekomendacji
    └── trail_recommender.py
```

---

## 🏅 Podsumowanie ETAP 4

**✅ Zrealizowane cele:**
- Pełna integracja z bazą danych SQLite
- Automatyczne zapisywanie nowych tras z API
- Wzrost z 320 do 3900+ tras w systemie
- Narzędzia administracyjne i statystyki
- Wzorzec Repository dla czystej architektury

**📊 Osiągnięcia:**
- **12x więcej tras** niż w poprzednim etapie
- **100% automatyzacja** zapisywania z API
- **Pełna funkcjonalność** bazy danych
- **Bezpieczeństwo danych** z backupami
- **Skalowalna architektura** dla przyszłych rozszerzeń

System jest teraz **produkcyjnie gotowy** z profesjonalną infrastrukturą bazy danych! 🎉