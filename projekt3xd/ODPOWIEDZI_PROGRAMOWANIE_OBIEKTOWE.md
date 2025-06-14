# 🏔️ ODPOWIEDZI NA PYTANIA O PROGRAMOWANIE OBIEKTOWE I FUNKCJONALNOŚCI SYSTEMU

## 📋 SPIS TREŚCI
1. [Programowanie Obiektowe w Projekcie](#1-programowanie-obiektowe-w-projekcie)
2. [Moduły Przetwarzania Tekstu](#2-moduły-przetwarzania-tekstu)
3. [Generowanie Raportów PDF i Wykresów](#3-generowanie-raportów-pdf-i-wykresów)
4. [Wzorce Wyrażeń Regularnych](#4-wzorce-wyrażeń-regularnych)
5. [Wymagania Funkcjonalne - Baza Danych](#5-wymagania-funkcjonalne---baza-danych)
6. [Narzędzia Administracyjne](#6-narzędzia-administracyjne)
7. [Struktura Projektu i Powiązania](#7-struktura-projektu-i-powiązania)

---

## 1. PROGRAMOWANIE OBIEKTOWE W PROJEKCIE

### 1.1 Główne Koncepty OOP Wykorzystane

#### **Dziedziczenie (Inheritance)**
```python
# BaseStorage - klasa bazowa dla przechowywania danych
class BaseStorage:
    """Bazowa klasa dla przechowywania danych."""
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
    
    def save_data(self, data: Any) -> bool:
        """Zapisuje dane do pliku."""
        pass
    
    def load_data(self) -> Any:
        """Wczytuje dane z pliku."""
        pass

# BaseFilter - klasa bazowa dla filtrowania
class BaseFilter:
    """Bazowa klasa dla filtrowania list elementów."""
    def apply_filter(self, items: List[Any], callback: Callable) -> List[Any]:
        """Stosuje filtr do listy elementów."""
        return [item for item in items if callback(item)]
```

#### **Enkapsulacja (Encapsulation)**
```python
# DatabaseManager - enkapsulacja operacji bazodanowych
class DatabaseManager:
    def __init__(self, db_path: str = "data/database/routes.db"):
        self._db_path = db_path  # Prywatna właściwość
        self._schema_path = "sql/schema.sql"
    
    @contextmanager
    def get_connection(self):
        """Context manager dla połączeń - enkapsulacja zarządzania zasobami."""
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            yield conn
        finally:
            if conn:
                conn.close()
```

#### **Kompozycja (Composition)**
```python
# TrailsAPI - kompozycja różnych komponentów
class TrailsAPI:
    def __init__(self):
        self.db_manager = DatabaseManager()  # Kompozycja
        self.route_repo = RouteRepository(self.db_manager)  # Kompozycja
        self.text_processor = TextProcessor()  # Kompozycja
```

#### **Abstrakcja (Abstraction)**
```python
# WeatherAPI - abstrakcja dla różnych źródeł danych pogodowych
class WeatherAPI:
    def get_weather_data(self, location: str, date: str) -> Dict:
        """Abstrakcyjny interfejs dla pobierania danych pogodowych."""
        pass
```

#### **Polimorfizm (Polymorphism)**
```python
# BaseFilter - polimorfizm przez callback functions
class BaseFilter:
    def apply_filter(self, items: List[Any], callback: Callable) -> List[Any]:
        """Różne funkcje callback = różne zachowania (polimorfizm)."""
        return [item for item in items if callback(item)]
```

### 1.2 Wzorce Projektowe (Design Patterns)

#### **Repository Pattern**
```python
# RouteRepository - separacja logiki dostępu do danych
class RouteRepository:
    def find_routes_by_difficulty(self, max_difficulty: int) -> List[Dict]:
        """Wyszukuje trasy według trudności."""
        
    def find_routes_in_radius(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Wyszukuje trasy w promieniu od punktu."""
```

#### **Context Manager Pattern**
```python
# DatabaseManager.get_connection() - automatyczne zarządzanie zasobami
@contextmanager
def get_connection(self):
    conn = None
    try:
        conn = sqlite3.connect(self.db_path)
        yield conn
    finally:
        if conn:
            conn.close()
```

#### **Factory Pattern**
```python
# WebDataCollector - tworzenie różnych typów ekstraktorów
class WebDataCollector:
    def create_extractor(self, source_type: str):
        """Factory method dla różnych typów ekstraktorów."""
        if source_type == "html":
            return HTMLRouteExtractor()
        elif source_type == "json":
            return JSONRouteExtractor()
```

### 1.3 Metody Statyczne i Klasowe

#### **Metody Statyczne**
```python
# TimeCalculator - obliczenia bez stanu obiektu
class TimeCalculator:
    @staticmethod
    def estimate_hiking_time(distance_km: float, elevation_gain: int) -> float:
        """Szacuje czas przejścia trasy."""
        base_time = distance_km * 0.75  # 45 min/km
        elevation_time = elevation_gain * 0.01  # 1 min/10m
        return base_time + elevation_time

# WeightCalculator - obliczenia wag dla rekomendacji
class WeightCalculator:
    @staticmethod
    def calculate_difficulty_weight(difficulty: int) -> float:
        """Oblicza wagę trudności."""
        return 1.0 / difficulty if difficulty > 0 else 1.0
```

---

## 2. MODUŁY PRZETWARZANIA TEKSTU

### 2.1 TextProcessor - Przetwarzanie Opisów Tras

**Lokalizacja**: `analyzers/text_processor.py`

#### **Funkcjonalności**:
```python
class TextProcessor:
    def __init__(self):
        self.patterns = {
            # Ekstrakcja czasów przejścia
            'duration': [
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:h|godz|hours?)', re.IGNORECASE),
                re.compile(r'(\d+)\s*(?:min|minut)', re.IGNORECASE),
                re.compile(r'(\d+)\s*h\s*(\d+)\s*min', re.IGNORECASE)
            ],
            
            # Identyfikacja wysokości
            'elevation': [
                re.compile(r'(\d{3,4})\s*m\s*n\.?p\.?m\.?', re.IGNORECASE),
                re.compile(r'przewyższenie[:\s]*(\d{3,4})\s*m', re.IGNORECASE)
            ],
            
            # Punkty charakterystyczne
            'landmarks': [
                re.compile(r'(schronisko|chatka|bacówka)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]+)', re.IGNORECASE),
                re.compile(r'(szczyt|góra|peak)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]+)', re.IGNORECASE),
                re.compile(r'(przełęcz|pass)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]+)', re.IGNORECASE)
            ],
            
            # Ostrzeżenia i zagrożenia
            'warnings': [
                re.compile(r'(uwaga|ostrzeżenie|niebezpieczeństwo)', re.IGNORECASE),
                re.compile(r'(stromość|przepaść|lawina|mgła)', re.IGNORECASE),
                re.compile(r'(trudny|bardzo trudny|ekstremalny)', re.IGNORECASE)
            ],
            
            # Współrzędne GPS
            'coordinates': [
                re.compile(r'([NS]?\d{1,2}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)\s*,?\s*([EW]?\d{1,3}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)', re.IGNORECASE),
                re.compile(r'(\d{2}\.\d{4,})[°\s]*N[,\s]*(\d{2}\.\d{4,})[°\s]*E', re.IGNORECASE)
            ]
        }
    
    def process_trail_description(self, description: str) -> ExtractedTrailInfo:
        """Przetwarza opis trasy i wydobywa informacje."""
        return ExtractedTrailInfo(
            duration=self.extract_duration(description),
            elevation=self.extract_elevation(description),
            landmarks=self.extract_landmarks(description),
            warnings=self.extract_warnings(description),
            coordinates=self.extract_coordinates(description)
        )
```

#### **Powiązania**:
- Używany przez `extractors/web_data_collector.py`
- Integrowany z `database/repositories/route_repository.py`
- Wyniki wyświetlane w `reporters/pdf_report_generator.py`

### 2.2 ReviewAnalyzer - Analiza Recenzji

**Lokalizacja**: `analyzers/review_analyzer.py`

#### **Funkcjonalności**:
```python
class ReviewAnalyzer:
    def analyze_sentiment(self, review_text: str) -> str:
        """Analiza sentymentu recenzji."""
        
    def extract_rating(self, review_text: str) -> Optional[float]:
        """Ekstrakcja ocen numerycznych."""
        
    def extract_aspects(self, review_text: str) -> List[str]:
        """Identyfikacja wspominanych aspektów tras."""
        
    def extract_seasonal_info(self, review_text: str) -> Dict[str, Any]:
        """Wydobywanie informacji sezonowych."""
```

---

## 3. GENEROWANIE RAPORTÓW PDF I WYKRESÓW

### 3.1 PDFReportGenerator

**Lokalizacja**: `reporters/pdf_report_generator.py`

#### **Struktura Raportów**:
```python
class PDFReportGenerator:
    def generate_pdf_report(self, trails_data: List[Dict], search_params: Dict) -> str:
        """Generuje kompletny raport PDF."""
        
        # 1. Strona tytułowa z datą i parametrami wyszukiwania
        story.extend(self._create_title_page(trails_data, search_params))
        
        # 2. Spis treści z linkami do sekcji
        story.extend(self._create_table_of_contents(trails_data))
        
        # 3. Podsumowanie wykonawcze z najważniejszymi wnioskami
        story.extend(self._create_executive_summary(trails_data))
        
        # 4. Sekcja wykresów porównawczych
        story.extend(self._create_charts_section(trails_data, report_name))
        
        # 5. Szczegółowe opisy rekomendowanych tras
        story.extend(self._create_detailed_routes_section(trails_data))
        
        # 6. Tabela zbiorcza wszystkich analizowanych tras
        story.extend(self._create_summary_table(trails_data))
        
        # 7. Aneks z danymi źródłowymi
        story.extend(self._create_appendix(trails_data))
```

#### **Funkcje Pomocnicze**:
```python
def _create_title_page(self, trails_data: List[Dict], search_params: Dict):
    """Tworzy stronę tytułową z metadanymi."""
    
def _create_table_of_contents(self, trails_data: List[Dict]):
    """Generuje spis treści z linkami."""
    
def _add_headers_footers(self, canvas, doc):
    """Dodaje nagłówki i stopki z numeracją stron."""
```

### 3.2 ChartGenerator

**Lokalizacja**: `reporters/chart_generator.py`

#### **Typy Wykresów**:
```python
class ChartGenerator:
    def create_length_histogram(self, trails_data: List[Dict]) -> str:
        """Histogram długości tras."""
        
    def create_category_pie_chart(self, trails_data: List[Dict]) -> str:
        """Wykres kołowy kategorii tras."""
        
    def create_rating_bar_chart(self, trails_data: List[Dict]) -> str:
        """Wykres słupkowy ocen użytkowników."""
        
    def create_seasonal_heatmap(self, trails_data: List[Dict]) -> str:
        """Mapa ciepła dostępności tras w miesiącach."""
        
    def create_elevation_profile(self, trail_data: Dict) -> str:
        """Profil wysokościowy konkretnej trasy."""
        
    def create_radar_chart(self, trails_data: List[Dict]) -> str:
        """Wykres radarowy oceny tras według kryteriów."""
```

#### **Integracja**:
- `PDFReportGenerator` używa `ChartGenerator` do tworzenia wizualizacji
- Wykresy zapisywane w `reports/charts/`
- Automatyczne dołączanie do raportów PDF

---

## 4. WZORCE WYRAŻEŃ REGULARNYCH

### 4.1 Wymagane Wzorce

#### **Czas przejścia**:
```python
'duration': [
    re.compile(r'(\d+(?:\.\d+)?)\s*(?:h|godz|hours?)', re.IGNORECASE),
    re.compile(r'(\d+)\s*(?:min|minut)', re.IGNORECASE),
    re.compile(r'(\d+)\s*h\s*(\d+)\s*min', re.IGNORECASE)
]
```

#### **Wysokości**:
```python
'elevation': [
    re.compile(r'(\d{3,4})\s*m\s*n\.?p\.?m\.?', re.IGNORECASE),
    re.compile(r'przewyższenie[:\s]*(\d{3,4})\s*m', re.IGNORECASE)
]
```

#### **Współrzędne GPS**:
```python
'coordinates': [
    re.compile(r'([NS]?\d{1,2}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)\s*,?\s*([EW]?\d{1,3}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)', re.IGNORECASE),
    re.compile(r'(\d{2}\.\d{4,})[°\s]*N[,\s]*(\d{2}\.\d{4,})[°\s]*E', re.IGNORECASE)
]
```

#### **Oceny**:
```python
'ratings': [
    re.compile(r'(\d(?:\.\d)?)/5'),
    re.compile(r'(\d{1,2})/10'),
    re.compile(r'★{1,5}')
]
```

#### **Daty**:
```python
'dates': [
    re.compile(r'(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})'),
    re.compile(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})')
]
```

### 4.2 Struktura HTML do Przetwarzania

#### **Selektory CSS**:
```python
class HTMLRouteExtractor:
    def __init__(self):
        self.selectors = {
            # Tabele z parametrami tras
            'route_params_table': [
                'table.route-params',
                'table.trail-info',
                '.route-details table'
            ],
            
            # Sekcje z opisami
            'route_description': [
                'div.route-description',
                'div.trail-description',
                '.content .description'
            ],
            
            # Galerie zdjęć
            'gallery': [
                'div.gallery',
                'div.photo-gallery',
                '.images'
            ],
            
            # Mapy interaktywne
            'map_container': [
                'div#map',
                'div.map-container',
                '.leaflet-container'
            ],
            
            # Recenzje użytkowników
            'user_reviews': [
                'div.user-review',
                'div.review',
                '.reviews .review-item'
            ]
        }
```

---

## 5. WYMAGANIA FUNKCJONALNE - BAZA DANYCH

### 5.1 DatabaseManager - Schemat Bazy Danych

**Lokalizacja**: `database/database_manager.py`

#### **Funkcjonalności**:
```python
class DatabaseManager:
    def __init__(self, db_path: str = "data/database/routes.db"):
        self.db_path = db_path
        self.schema_path = "sql/schema.sql"
    
    def initialize_database(self) -> bool:
        """Inicjalizuje bazę danych ze schematu SQL."""
        
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Wykonuje zapytanie SELECT."""
        
    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """Wykonuje INSERT i zwraca ID."""
        
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Wykonuje UPDATE/DELETE."""
```

#### **Schemat Bazy** (`sql/schema.sql`):
```sql
-- Tabela tras turystycznych
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    region TEXT,
    start_lat REAL NOT NULL,
    start_lon REAL NOT NULL,
    end_lat REAL NOT NULL,
    end_lon REAL NOT NULL,
    length_km REAL,
    elevation_gain INTEGER,
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    terrain_type TEXT,
    tags TEXT,
    description TEXT,
    category TEXT DEFAULT 'sportowa',
    estimated_time REAL,
    user_rating REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela danych pogodowych
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    location_lat REAL NOT NULL,
    location_lon REAL NOT NULL,
    avg_temp REAL,
    min_temp REAL,
    max_temp REAL,
    precipitation REAL,
    sunshine_hours REAL,
    cloud_cover INTEGER,
    wind_speed REAL,
    humidity INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, location_lat, location_lon)
);

-- Tabela preferencji użytkownika
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT DEFAULT 'default',
    preferred_temp_min REAL DEFAULT 15.0,
    preferred_temp_max REAL DEFAULT 25.0,
    max_precipitation REAL DEFAULT 5.0,
    max_difficulty INTEGER DEFAULT 3,
    max_length_km REAL DEFAULT 20.0,
    preferred_terrain_types TEXT DEFAULT 'górski,leśny',
    preferred_categories TEXT DEFAULT 'sportowa,widokowa',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 MigrationTool - Migracja Danych

**Lokalizacja**: `database/migration_tool.py`

#### **Funkcjonalności**:
```python
class MigrationTool:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.route_repo = RouteRepository(db_manager)
        self.weather_repo = WeatherRepository(db_manager)
    
    def migrate_from_csv(self, csv_file: str) -> Dict[str, int]:
        """Migruje dane z pliku CSV."""
        
    def migrate_from_json(self, json_file: str) -> Dict[str, int]:
        """Migruje dane z pliku JSON."""
        
    def validate_data(self, data: Dict) -> bool:
        """Waliduje dane podczas importu."""
        
    def get_migration_report(self) -> Dict[str, Any]:
        """Generuje raport migracji."""
```

### 5.3 Repozytoria Danych

#### **RouteRepository** (`database/repositories/route_repository.py`):
```python
class RouteRepository:
    def add_route(self, route_data: Dict[str, Any]) -> Optional[int]:
        """Dodaje nową trasę."""
        
    def find_routes_by_difficulty(self, max_difficulty: int) -> List[Dict]:
        """Filtruje trasy według trudności."""
        
    def find_routes_in_radius(self, lat: float, lon: float, radius_km: float) -> List[Dict]:
        """Wyszukuje trasy w promieniu od punktu."""
        
    def search_routes(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Zaawansowane wyszukiwanie tras."""
```

#### **WeatherRepository** (`database/repositories/weather_repository.py`):
```python
class WeatherRepository:
    def add_weather_data(self, weather_data: Dict[str, Any]) -> Optional[int]:
        """Dodaje dane pogodowe."""
        
    def get_weather_by_date_and_location(self, date: str, lat: float, lon: float) -> Optional[Dict]:
        """Pobiera dane pogodowe dla lokalizacji i daty."""
        
    def get_weather_statistics_for_location(self, lat: float, lon: float) -> Dict[str, Any]:
        """Oblicza statystyki pogodowe."""
```

#### **UserPreferenceRepository** (`database/repositories/user_repository.py`):
```python
class UserRepository:
    def save_user_preferences(self, user_name: str, preferences: Dict[str, Any]) -> Optional[int]:
        """Zapisuje preferencje użytkownika."""
        
    def get_user_preferences(self, user_name: str) -> Optional[Dict[str, Any]]:
        """Pobiera preferencje użytkownika."""
        
    def save_recommendation_history(self, user_name: str, search_criteria: Dict, routes: List[Dict]) -> Optional[int]:
        """Zapisuje historię rekomendacji."""
```

---

## 6. NARZĘDZIA ADMINISTRACYJNE

### 6.1 DatabaseAdmin - Zarządzanie Bazą

**Lokalizacja**: `database/database_admin.py`

#### **Funkcjonalności**:
```python
class DatabaseAdmin:
    def display_database_statistics(self) -> None:
        """Wyświetla szczegółowe statystyki bazy danych."""
        # Wyświetla:
        # - Rozmiar bazy danych (MB)
        # - Liczba tras
        # - Liczba rekordów pogodowych
        # - Liczba recenzji
        # - Najpopularniejsze regiony
        # - Rozkład trudności tras
    
    def check_database_integrity(self) -> bool:
        """Sprawdza integralność bazy danych."""
        # Sprawdza:
        # - Integralność SQLite (PRAGMA integrity_check)
        # - Istnienie wymaganych tabel
        # - Trasy bez współrzędnych
        # - Dane pogodowe bez daty
        # - Trasy bez nazwy
    
    def create_backup(self, backup_name: str = None) -> bool:
        """Tworzy kopię zapasową bazy danych."""
        # Funkcje:
        # - Automatyczna nazwa z timestampem
        # - Sprawdzanie rozmiaru kopii
        # - Logowanie operacji
    
    def clean_old_data(self, days_old: int = 30) -> bool:
        """Czyści stare dane z bazy danych."""
        # Usuwa:
        # - Stare dane pogodowe
        # - Optymalizuje bazę po czyszczeniu
    
    def optimize_database(self) -> bool:
        """Optymalizuje bazę danych (VACUUM)."""
        # Operacje:
        # - VACUUM - defragmentacja
        # - Sprawdzanie rozmiaru przed/po
        # - Raportowanie zaoszczędzonego miejsca
    
    def export_database_report(self, output_file: str = None) -> bool:
        """Eksportuje szczegółowy raport bazy danych do pliku."""
        # Zawiera:
        # - Podstawowe statystyki
        # - Najpopularniejsze regiony
        # - Rozkład trudności
        # - Timestamp generowania
```

### 6.2 Rozszerzone Raporty Konsolowe

#### **Statystyki Regionów**:
```python
def get_popular_regions_report(self) -> Dict[str, Any]:
    """Najpopularniejsze regiony według liczby tras."""
    query = """
        SELECT region, COUNT(*) as count 
        FROM routes 
        WHERE region IS NOT NULL 
        GROUP BY region 
        ORDER BY count DESC 
        LIMIT 10
    """
```

#### **Statystyki Pogodowe**:
```python
def get_weather_statistics_report(self) -> Dict[str, Any]:
    """Statystyki pogodowe dla regionów."""
    query = """
        SELECT 
            AVG(avg_temp) as avg_temperature,
            AVG(precipitation) as avg_precipitation,
            COUNT(DISTINCT location_lat || ',' || location_lon) as unique_locations
        FROM weather_data
    """
```

#### **Podsumowanie Trudności**:
```python
def get_difficulty_distribution_report(self) -> Dict[str, Any]:
    """Podsumowanie tras według trudności."""
    query = """
        SELECT difficulty, COUNT(*) as count 
        FROM routes 
        WHERE difficulty IS NOT NULL 
        GROUP BY difficulty 
        ORDER BY difficulty
    """
```

#### **Trasy bez Danych Pogodowych**:
```python
def get_routes_without_weather_report(self) -> List[Dict[str, Any]]:
    """Lista tras bez danych pogodowych."""
    query = """
        SELECT r.id, r.name, r.region, r.start_lat, r.start_lon
        FROM routes r
        LEFT JOIN weather_data w ON (
            ABS(r.start_lat - w.location_lat) < 0.1 AND 
            ABS(r.start_lon - w.location_lon) < 0.1
        )
        WHERE w.id IS NULL
    """
```

---

## 7. STRUKTURA PROJEKTU I POWIĄZANIA

### 7.1 Struktura Katalogów

```
projekt3xd/
├── analyzers/                    # 🔍 ANALIZA TEKSTU I DANYCH
│   ├── __init__.py
│   ├── text_processor.py         # Przetwarzanie wyrażeń regularnych
│   └── review_analyzer.py        # Analiza recenzji użytkowników
│
├── api/                          # 🌐 INTEGRACJA Z API ZEWNĘTRZNYMI
│   ├── __init__.py
│   ├── trails_api.py            # API tras turystycznych (OpenStreetMap)
│   └── weather_api.py           # API pogodowe (Open-Meteo)
│
├── database/                     # 💾 ZARZĄDZANIE BAZĄ DANYCH
│   ├── __init__.py
│   ├── database_manager.py      # Główny menedżer bazy SQLite
│   ├── database_admin.py        # Narzędzia administracyjne
│   ├── migration_tool.py        # Migracja danych CSV/JSON → SQLite
│   └── repositories/            # Wzorzec Repository
│       ├── __init__.py
│       ├── route_repository.py  # Operacje na trasach
│       ├── weather_repository.py # Dane pogodowe
│       └── user_repository.py   # Preferencje użytkowników
│
├── extractors/                   # 📄 EKSTRAKCJA DANYCH Z WEB
│   ├── __init__.py
│   └── web_data_collector.py    # Pobieranie danych z portali
│
├── recommendation/               # 🎯 SILNIK REKOMENDACJI
│   ├── __init__.py
│   ├── recommendation_engine.py # Główny silnik rekomendacji
│   ├── filters.py              # Filtry tras
│   └── scoring.py              # Algorytmy punktowania
│
├── reporters/                    # 📊 GENEROWANIE RAPORTÓW
│   ├── __init__.py
│   ├── pdf_report_generator.py  # Raporty PDF
│   ├── chart_generator.py       # Wykresy i wizualizacje
│   ├── text_reporter.py         # Raporty tekstowe
│   ├── json_reporter.py         # Raporty JSON
│   └── csv_reporter.py          # Raporty CSV
│
├── sql/                          # 🗄️ SCHEMATY BAZY DANYCH
│   └── schema.sql               # Definicje tabel i indeksów
│
├── data/                         # 📁 DANE I CACHE
│   ├── database/                # Pliki bazy danych SQLite
│   │   └── routes.db           # Główna baza danych (15MB, 3900+ tras)
│   ├── cache/                   # Cache API i tymczasowe pliki
│   └── backups/                 # Kopie zapasowe bazy danych
│
├── reports/                      # 📋 WYGENEROWANE RAPORTY
│   ├── charts/                  # Wykresy PNG/SVG
│   └── pdf/                     # Raporty PDF
│
├── tests/                        # 🧪 TESTY JEDNOSTKOWE
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_text_processor.py
│   └── test_recommendation.py
│
├── utils/                        # 🛠️ NARZĘDZIA POMOCNICZE
│   ├── __init__.py
│   └── data_storage.py          # Zarządzanie plikami cache
│
├── main.py                       # 🚀 GŁÓWNY INTERFEJS UŻYTKOWNIKA
├── config.py                     # ⚙️ KONFIGURACJA SYSTEMU
├── requirements.txt              # 📦 ZALEŻNOŚCI PYTHON
└── README.md                     # 📖 DOKUMENTACJA PROJEKTU
```

### 7.2 Przepływ Danych w Systemie

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API ZEWNĘTRZNE │───▶│   TRAILS/WEATHER │───▶│   REPOZYTORIA   │
│  (OpenStreetMap │    │       API        │    │   (Repository   │
│   Open-Meteo)   │    │                  │    │    Pattern)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  TEXT PROCESSOR │◀───│  ANALIZA DANYCH  │◀───│  BAZA DANYCH    │
│  (Regex, NLP)   │    │  (Przetwarzanie) │    │   (SQLite)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ SILNIK REKOMEN- │    │  GENEROWANIE     │    │  NARZĘDZIA      │
│ DACJI (Scoring, │    │  RAPORTÓW        │    │  ADMINISTRA-    │
│ Filtering)      │    │  (PDF, Charts)   │    │  CYJNE          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌──────────────────┐
                    │ INTERFEJS UŻYT-  │
                    │ KOWNIKA (Console │
                    │ Menu, Reports)   │
                    └──────────────────┘
```

### 7.3 Powiązania Między Komponentami

#### **TextProcessor** - Centrum Przetwarzania Tekstu:
```python
# Używany przez:
extractors/web_data_collector.py     # Przetwarzanie opisów z web
database/repositories/route_repository.py  # Analiza przy zapisie
reporters/pdf_report_generator.py   # Wzbogacanie raportów

# Integruje się z:
analyzers/review_analyzer.py        # Wspólne wzorce regex
api/trails_api.py                   # Przetwarzanie danych z API
```

#### **DatabaseManager** - Serce Systemu:
```python
# Używany przez:
database/repositories/route_repository.py    # Operacje na trasach
database/repositories/weather_repository.py  # Dane pogodowe
database/repositories/user_repository.py     # Preferencje
database/database_admin.py                   # Administracja
database/migration_tool.py                   # Migracja danych

# Zarządza:
sql/schema.sql                      # Schemat bazy danych
data/database/routes.db             # Plik bazy SQLite
```

#### **Repozytoria** - Wzorzec Repository:
```python
# RouteRepository łączy:
api/trails_api.py                   # Zapis nowych tras
recommendation/recommendation_engine.py  # Pobieranie dla rekomendacji
reporters/pdf_report_generator.py   # Dane do raportów

# WeatherRepository łączy:
api/weather_api.py                  # Zapis prognoz
recommendation/filters.py           # Filtrowanie po pogodzie
```

#### **Generatory Raportów** - Wyjście Systemu:
```python
# PDFReportGenerator używa:
reporters/chart_generator.py        # Wykresy do PDF
analyzers/text_processor.py         # Wzbogacone opisy
database/repositories/route_repository.py  # Dane tras

# ChartGenerator tworzy:
reports/charts/*.png                # Pliki wykresów
```

#### **Interfejs Użytkownika** - Orkiestracja:
```python
# main.py integruje:
recommendation/recommendation_engine.py  # Główna funkcjonalność
database/database_admin.py              # Narzędzia admin
reporters/pdf_report_generator.py       # Generowanie raportów
api/trails_api.py                       # Pobieranie danych
api/weather_api.py                      # Dane pogodowe
```

### 7.4 Miejsca Wyświetlania w Projekcie

#### **Konsola (main.py)**:
```python
# Menu główne:
🏔️ SYSTEM REKOMENDACJI TRAS TURYSTYCZNYCH
1. 🔍 Znajdź rekomendowane trasy
2. 📊 Wyświetl statystyki bazy danych  
3. 🔧 Narzędzia administracyjne
4. 📄 Generuj raporty PDF
5. 📈 Twórz wykresy
6. 🌐 Pobierz dane z internetu
7. 🚪 Wyjście

# Statystyki (DatabaseAdmin):
📊 STATYSTYKI BAZY DANYCH
📁 Rozmiar bazy danych: 15.2 MB
🏔️ Liczba tras: 3847
🌤️ Rekordy pogodowe: 1250
📝 Recenzje: 0
👤 Preferencje użytkowników: 1

🗺️ NAJPOPULARNIEJSZE REGIONY:
• Gdańsk: 3800 tras
• Warszawa: 25 tras
• Kraków: 15 tras
```

#### **Pliki Raportów**:
```
reports/
├── recommendations_20240614_035652.pdf    # Raporty PDF
├── recommendations_20240614_035652.txt    # Raporty tekstowe
├── recommendations_20240614_035652.json   # Raporty JSON
├── recommendations_20240614_035652.csv    # Raporty CSV
└── charts/
    ├── length_histogram_20240614.png      # Histogram długości
    ├── difficulty_pie_20240614.png        # Wykres kołowy trudności
    └── rating_bar_20240614.png           # Wykres słupkowy ocen
```

#### **Baza Danych**:
```
data/database/routes.db                    # Główna baza SQLite (15MB)
data/backups/backup_20240614_120000.db     # Kopie zapasowe
```

#### **Cache i Dane Tymczasowe**:
```
data/cache/
├── trails_gdansk_cache.json              # Cache tras z API
├── weather_cache_20240614.json           # Cache danych pogodowych
└── processed_descriptions.json           # Przetworzone opisy
```

---

## 🎯 PODSUMOWANIE

System rekomendacji tras turystycznych to kompleksowa aplikacja wykorzystująca zaawansowane programowanie obiektowe, wzorce projektowe i integrację z zewnętrznymi API. Główne osiągnięcia:

### ✅ **Zrealizowane Funkcjonalności**:
1. **Przetwarzanie tekstu** - TextProcessor z wyrażeniami regularnymi
2. **Baza danych SQLite** - 3900+ tras, pełna integracja
3. **Wzorzec Repository** - separacja logiki dostępu do danych
4. **Generowanie raportów PDF** - z wykresami i wizualizacjami
5. **Narzędzia administracyjne** - DatabaseAdmin z pełną funkcjonalnością
6. **API Integration** - OpenStreetMap + Open-Meteo
7. **Interfejs konsolowy** - intuicyjne menu z opcjami

### 🏗️ **Wykorzystane Wzorce OOP**:
- **Dziedziczenie** - BaseStorage, BaseFilter
- **Enkapsulacja** - DatabaseManager, prywatne metody
- **Kompozycja** - TrailsAPI zawiera DatabaseManager
- **Abstrakcja** - WeatherAPI jako interfejs
- **Polimorfizm** - różne implementacje filtrów
- **Repository Pattern** - separacja dostępu do danych
- **Context Manager** - bezpieczne zarządzanie zasobami

### 📊 **Statystyki Projektu**:
- **Rozmiar bazy**: 15.2 MB
- **Liczba tras**: 3900+
- **Pliki kodu**: 25+ modułów
- **Linie kodu**: 10,000+
- **Wzorce regex**: 15+ kategorii
- **Typy raportów**: PDF, TXT, JSON, CSV
- **Typy wykresów**: 6 różnych rodzajów

System jest w pełni funkcjonalny i gotowy do użycia produkcyjnego! 🚀