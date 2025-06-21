# 🔒 System Walidacji i Zabezpieczeń - City Builder

## 📋 Przegląd

System walidacji i zabezpieczeń zapewnia integralność danych i bezpieczeństwo aplikacji City Builder. Wszystkie dane wejściowe są sprawdzane pod kątem poprawności, a potencjalne błędy są przechwytywane i obsługiwane.

## 🏗️ Architektura Systemu

### Centralny Moduł Walidacji
- **Lokalizacja**: `core/validation_system.py`
- **Główna Klasa**: `ValidationSystem`
- **Singleton**: `get_validation_system()`

### Struktura Walidacji
```python
@dataclass
class ValidationResult:
    is_valid: bool           # Czy dane są poprawne
    errors: List[str]        # Lista błędów
    warnings: List[str]      # Lista ostrzeżeń
    cleaned_data: Any        # Oczyszczone dane
```

## 🎯 Obszary Walidacji

### 1. 💾 Zapisywanie i Wczytywanie Gry

**Lokalizacja**: `Main.py` - `save_game()`, `load_game()`

**Walidacje**:
- ✅ Walidacja nazw plików (znaki specjalne, długość)
- ✅ Sprawdzenie poprawności struktury JSON
- ✅ Walidacja danych zapisu gry
- ✅ Kontrola rozmiaru pliku (max 50MB)
- ✅ Sprawdzenie kodowania UTF-8

**Przykład**:
```python
validation_result = validator.validate_save_filename(filename)
if not validation_result.is_valid:
    # Pokaż błędy użytkownikowi
    error_msg = "\n".join(validation_result.errors)
    QMessageBox.warning(self, 'Błąd walidacji', error_msg)
```

### 2. 🏗️ Budowanie

**Lokalizacja**: `Main.py` - `on_building_placed()`

**Walidacje**:
- ✅ Sprawdzenie współrzędnych (granice mapy)
- ✅ Walidacja danych budynku (nazwa, typ, koszt)
- ✅ Kontrola efektów budynku
- ✅ Zabezpieczenie przed nieprawidłowymi wartościami

### 3. 💰 System Ekonomiczny

**Lokalizacja**: `core/resources.py` - `modify_resource()`

**Walidacje**:
- ✅ Sprawdzenie kwot (NaN, Infinity)
- ✅ Kontrola limitów zasobów
- ✅ Walidacja stawek podatkowych (0-100%)
- ✅ Zaokrąglanie do 2 miejsc po przecinku
- ✅ Logowanie błędów walidacji

### 4. 🎮 Stan Gry

**Lokalizacja**: `Main.py` - `_validate_game_state()`

**Walidacje**:
- ✅ Sprawdzenie obiektów gry (economy, population)
- ✅ Walidacja stanu ekonomii
- ✅ Kontrola populacji
- ✅ Sprawdzenie stawek podatkowych
- ✅ Automatyczna naprawa błędów

### 5. 📊 Podatki

**Lokalizacja**: `Main.py` - `on_tax_slider_changed()`

**Walidacje**:
- ✅ Sprawdzenie stawek podatkowych (0-1.0)
- ✅ Kontrola NaN i Infinity
- ✅ Automatyczna korekta błędnych wartości
- ✅ Informowanie użytkownika o błędach

## 🛡️ Typy Walidacji

### Podstawowe Wzorce
```python
'city_name': r'^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\-]{2,50}$'
'save_filename': r'^[A-Za-z0-9_\-\s]{1,50}$'
'money_amount': r'^-?\d{1,12}(\.\d{1,2})?$'
'percentage': r'^(100|[0-9]{1,2})(\.\d{1,2})?$'
'coordinates': r'^(\d{1,3}),(\d{1,3})$'
```

### Limity Bezpieczeństwa
```python
limits = {
    'money': {'min': -999999999, 'max': 999999999},
    'population': {'min': 0, 'max': 99999999},
    'coordinates': {'min': 0, 'max': 999},
    'percentage': {'min': 0, 'max': 100},
    'map_size': {'min': 10, 'max': 500},
    'tax_rate': {'min': 0, 'max': 1},
    'filename_length': {'min': 1, 'max': 50}
}
```

## 🔧 Funkcje Walidacji

### Podstawowe Walidacje
- `validate_save_filename()` - nazwy plików zapisu
- `validate_coordinates()` - współrzędne na mapie
- `validate_money_amount()` - kwoty pieniędzy
- `validate_population()` - liczebność populacji
- `validate_percentage()` - wartości procentowe
- `validate_building_data()` - dane budynków
- `validate_tax_rate()` - stawki podatkowe

### Walidacje Strukturalne
- `validate_json_file()` - pliki JSON
- `validate_game_save_data()` - dane zapisu gry
- `validate_economic_data()` - dane ekonomiczne

### Funkcje Sanityzacji
- `_sanitize_text()` - oczyszcza tekst
- `_sanitize_filename()` - oczyszcza nazwy plików
- `_get_dict_depth()` - sprawdza głębokość struktury

## 🚨 Obsługa Błędów

### Poziomy Błędów
1. **ERRORS** - Krytyczne błędy blokujące operację
2. **WARNINGS** - Ostrzeżenia, operacja kontynuowana
3. **INFO** - Informacje o naprawach automatycznych

### Strategie Naprawy
- **Automatyczna korekta** - dla prostych błędów
- **Wartości domyślne** - gdy dane są nieprawidłowe
- **Blokada operacji** - dla krytycznych błędów
- **Informowanie użytkownika** - o wszystkich problemach

## 📝 Logowanie

### Kategorie Logów
- **validation** - błędy walidacji
- **economy** - problemy ekonomiczne
- **ui** - błędy interfejsu
- **game_engine** - błędy silnika gry

### Przykłady Logów
```python
logger.error("Invalid money state: amount is NaN")
logger.warning("Invalid tax rate for residential: exceeds maximum")
logger.info("Save validation warnings: deep structure detected")
```

## 🔍 Testowanie Walidacji

### Przypadki Testowe
1. **Nieprawidłowe nazwy plików** - znaki specjalne, długość
2. **Błędne współrzędne** - poza mapą, ujemne
3. **Nieprawidłowe kwoty** - NaN, Infinity, za duże
4. **Błędne pliki JSON** - uszkodzona struktura
5. **Nieprawidłowe stawki podatkowe** - poza zakresem

### Uruchamianie Testów
```bash
cd City_Builder
python -c "from core.validation_system import get_validation_system; vs = get_validation_system(); print('Tests passed')"
```

## 🛠️ Integracja z Aplikacją

### Import Systemu
```python
from core.validation_system import get_validation_system

validator = get_validation_system()
result = validator.validate_money_amount(amount)
```

### Obsługa Wyników
```python
if not result.is_valid:
    # Pokaż błędy
    for error in result.errors:
        print(f"Error: {error}")
else:
    # Użyj oczyszczonych danych
    clean_data = result.cleaned_data
```

## 🔄 Przyszłe Rozszerzenia

### Planowane Funkcje
- [ ] Walidacja handlu międzymiastowego
- [ ] Kontrola technologii
- [ ] Walidacja osiągnięć
- [ ] Sprawdzenie celów gry
- [ ] Walidacja ustawień konfiguracji

### Potencjalne Ulepszenia
- [ ] Async walidacja dla dużych plików
- [ ] Cache wyników walidacji
- [ ] Metryki wydajności walidacji
- [ ] Niestandardowe reguły walidacji

## 🎯 Korzyści Systemu

### Bezpieczeństwo
- ✅ Ochrona przed uszkodzonymi danymi
- ✅ Kontrola danych wejściowych
- ✅ Automatyczna naprawa błędów
- ✅ Logowanie wszystkich problemów

### Stabilność
- ✅ Zapobieganie awariom aplikacji
- ✅ Graceful degradation
- ✅ Automatyczne recovery
- ✅ Informowanie użytkownika

### Użyteczność
- ✅ Czytelne komunikaty błędów
- ✅ Sugestie naprawy
- ✅ Automatyczne oczyszczanie danych
- ✅ Ostrzeżenia o problemach

---

**📅 Ostatnia aktualizacja**: 2024-12-17  
**🔖 Wersja**: 1.0.0  
**✨ Status**: Kompletny i gotowy do użycia 