"""
MODUŁ PRZETWARZANIA TEKSTU - EKSTRAKCJA INFORMACJI Z OPISÓW TRAS
===============================================================

Ten moduł zawiera klasę TextProcessor, która wykorzystuje wyrażenia regularne
do automatycznego wydobywania kluczowych informacji z opisów tras turystycznych.

FUNKCJONALNOŚCI:
- Ekstrakcja czasów przejścia (różne formaty: "2h 30min", "150 minut", "około 4h")
- Rozpoznawanie wysokości i przewyższeń ("1650 m n.p.m.", "przewyższenie 500m")
- Standaryzacja współrzędnych GPS (różne formaty zapisu)
- Identyfikacja punktów charakterystycznych (schroniska, szczyty, przełęcze)
- Rozpoznawanie ostrzeżeń i zagrożeń na trasach
- Określanie poziomu trudności i sezonowości

WYMAGANIA: Implementacja zgodna z specyfikacją z updatelist.txt
AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK
# ============================================================================
import re                                    # Wyrażenia regularne
from typing import Dict, List, Optional, Any, Tuple  # Podpowiedzi typów
from dataclasses import dataclass           # Struktura danych
import logging                              # Logowanie błędów i informacji
import datetime                            # Operacje na datach

# ============================================================================
# KONFIGURACJA LOGOWANIA
# ============================================================================
logging.basicConfig(level=logging.INFO)    # Ustawienia logowania
logger = logging.getLogger(__name__)       # Logger dla tego modułu

# ============================================================================
# STRUKTURY DANYCH
# ============================================================================

@dataclass
class ExtractedTrailInfo:
    """
    Struktura danych przechowująca wszystkie wyekstraktowane informacje o trasie.
    
    Attributes:
        duration_minutes: Czas przejścia w minutach (np. 120 dla 2h)
        elevation_gain: Przewyższenie w metrach (np. 500)
        landmarks: Lista punktów charakterystycznych na trasie
        warnings: Lista ostrzeżeń i zagrożeń
        coordinates: Współrzędne GPS jako tuple (szerokość, długość)
        difficulty_level: Poziom trudności ("łatwa", "średnia", "trudna")
        recommended_season: Zalecana pora roku lub warunki
    
    Wszystkie pola są opcjonalne - jeśli informacja nie została znaleziona,
    pole ma wartość None lub pustą listę.
    """
    duration_minutes: Optional[int] = None              # Czas w minutach
    elevation_gain: Optional[int] = None                # Przewyższenie w metrach
    landmarks: List[str] = None                         # Punkty charakterystyczne
    warnings: List[str] = None                          # Ostrzeżenia
    coordinates: Optional[Tuple[str, str]] = None       # Współrzędne GPS
    difficulty_level: Optional[str] = None              # Poziom trudności
    recommended_season: Optional[str] = None            # Zalecana pora
    
    def __post_init__(self):
        """
        Inicjalizacja pustych list dla pól, które nie mogą być None.
        Wywoływana automatycznie po utworzeniu obiektu.
        """
        if self.landmarks is None:
            self.landmarks = []  # Pusta lista zamiast None
        if self.warnings is None:
            self.warnings = []   # Pusta lista zamiast None

# ============================================================================
# GŁÓWNA KLASA PROCESORA TEKSTU
# ============================================================================

class TextProcessor:
    """
    Główna klasa do przetwarzania tekstów opisów tras i ekstrakcji informacji
    używając zaawansowanych wyrażeń regularnych.
    
    Klasa implementuje kompleksowy system rozpoznawania wzorców w tekstach
    polskojęzycznych opisów tras turystycznych. Wykorzystuje predefiniowane
    wzorce regex do identyfikacji różnych typów informacji.
    
    Przykład użycia:
        processor = TextProcessor()
        info = processor.process_trail_description("Trasa 5km, 2h 30min, 
                                                    przełęcz Zawrat 2159m n.p.m.")
        print(f"Czas: {info.duration_minutes} minut")
    """
    
    def __init__(self):
        """
        Inicjalizacja wszystkich wzorców wyrażeń regularnych.
        
        Tworzy słownik wzorców regex podzielonych na kategorie:
        - duration: różne formaty czasu przejścia
        - elevation: wysokości i przewyższenia  
        - coordinates: współrzędne GPS w różnych formatach
        - landmarks: punkty charakterystyczne
        - warnings: ostrzeżenia i zagrożenia
        - difficulty: poziomy trudności
        - season: informacje o sezonowości
        """
        # ====================================================================
        # WZORCE WYRAŻEŃ REGULARNYCH - zgodnie z wymaganiami updatelist.txt
        # ====================================================================
        self.patterns = {
            # Czas przejścia: r'(\d+(?:\.\d+)?)\s*(?:h|godz|hours?)|(\d+)\s*(?:min|minut)'
            'duration': [
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:h|godz|godzin|hours?)', re.IGNORECASE),
                re.compile(r'(\d+)\s*(?:min|minut)', re.IGNORECASE),
                re.compile(r'(\d+)\s*h\s*(\d+)\s*min', re.IGNORECASE),
                re.compile(r'około\s*(\d+(?:\.\d+)?)\s*(?:h|godz|godzin)', re.IGNORECASE),
                re.compile(r'(\d+)-(\d+)\s*(?:h|godz|godzin)', re.IGNORECASE)
            ],
            
            # Wysokości: r'(\d{3,4})\s*m\s*n\.p\.m\.'
            'elevation': [
                re.compile(r'(\d{3,4})\s*m\s*n\.?p\.?m\.?', re.IGNORECASE),
                re.compile(r'przewyższenie[:\s]*(\d{3,4})\s*m', re.IGNORECASE),
                re.compile(r'wysokość[:\s]*(\d{3,4})\s*m', re.IGNORECASE)
            ],
            
            # Współrzędne GPS: r'([NS]?\d{1,2}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)\s*,?\s*([EW]?\d{1,3}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)'
            'coordinates': [
                re.compile(r'([NS]?\d{1,2}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)\s*,?\s*([EW]?\d{1,3}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)', re.IGNORECASE),
                re.compile(r'(\d{2}\.\d{4,})[°\s]*N[,\s]*(\d{2}\.\d{4,})[°\s]*E', re.IGNORECASE),
                re.compile(r'N\s*(\d{2}[°º]\d{2}[\'′]\d{2}[\"″]?)\s*E\s*(\d{2}[°º]\d{2}[\'′]\d{2}[\"″]?)', re.IGNORECASE)
            ],
            
            # Punkty charakterystyczne
            'landmarks': [
                re.compile(r'(schronisko\s+\w+)', re.IGNORECASE),
                re.compile(r'(szczyt\s+\w+)', re.IGNORECASE),
                re.compile(r'(przełęcz\s+\w+)', re.IGNORECASE),
                re.compile(r'(dolina\s+\w+)', re.IGNORECASE),
                re.compile(r'(jezioro\s+\w+)', re.IGNORECASE),
                re.compile(r'(wodospad\s+\w+)', re.IGNORECASE),
                re.compile(r'(punkt\s+widokowy)', re.IGNORECASE)
            ],
            
            # Ostrzeżenia i zagrożenia
            'warnings': [
                re.compile(r'uwaga[:\s]*([\w\s,]+(?:po\s+deszczu|śliskie|niebezpieczne|trudne|strome)[\w\s]*)', re.IGNORECASE),
                re.compile(r'((?:śliskie|niebezpieczne|trudne|strome)[\w\s]*)', re.IGNORECASE),
                re.compile(r'ostrzeżenie[:\s]*([\w\s,]+)', re.IGNORECASE),
                re.compile(r'(zagrożenie[\w\s]*)', re.IGNORECASE)
            ],
            
            # Poziom trudności
            'difficulty': [
                re.compile(r'trasa\s+(łatwa|średnia|średnio\s+trudna|trudna|bardzo\s+trudna)', re.IGNORECASE),
                re.compile(r'poziom\s+trudności[:\s]*(łatwy|średni|trudny)', re.IGNORECASE),
                re.compile(r'(łatwa|średnia|trudna)\s+trasa', re.IGNORECASE)
            ],
            
            # Sezonowość i zalecane pory
            'season': [
                re.compile(r'najlepiej\s+(wiosną|latem|jesienią|zimą)', re.IGNORECASE),
                re.compile(r'zalecana\s+pora[:\s]*([\w\s]+)', re.IGNORECASE),
                re.compile(r'(wczesnym\s+rankiem|wieczorem|w\s+południe)', re.IGNORECASE),
                re.compile(r'sezon[:\s]*([\w\s-]+)', re.IGNORECASE)
            ]
        }
    
    def extract_duration(self, text: str) -> Optional[int]:
        """
        Wydobywa czas przejścia w różnych formatach i konwertuje na minuty.
        
        Metoda rozpoznaje następujące formaty czasu:
        - "2h 30min" lub "2 godz 30 minut" -> 150 minut
        - "3.5h" lub "3,5 godziny" -> 210 minut  
        - "90 minut" -> 90 minut
        - "około 4h" -> 240 minut
        - "2-3h" -> średnia 150 minut
        
        Args:
            text: Tekst do analizy zawierający informacje o czasie
            
        Returns:
            int: Czas w minutach (np. 120 dla 2 godzin)
            None: Jeśli nie znaleziono informacji o czasie lub wystąpił błąd konwersji
            
        Przykłady:
            extract_duration("Trasa zajmuje 2h 30min") -> 150
            extract_duration("Około 3.5 godziny marszu") -> 210
            extract_duration("90 minut spaceru") -> 90
        """
        # Iteracja przez wszystkie wzorce czasowe zdefiniowane w __init__
        for pattern in self.patterns['duration']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            if matches:  # Jeśli znaleziono jakieś dopasowania
                try:
                    match = matches[0]  # Weź pierwsze dopasowanie
                    
                    # Obsługa dopasowań w formie krotki (np. z grup w regex)
                    if isinstance(match, tuple):
                        # Format "X h Y min" - obie wartości obecne
                        if len(match) == 2 and match[0] and match[1]:
                            hours = float(match[0])    # Konwertuj godziny na float
                            minutes = float(match[1])  # Konwertuj minuty na float
                            return int(hours * 60 + minutes)  # Zwróć sumę w minutach
                            
                        # Format tylko z godzinami (np. "3h")
                        elif len(match) == 2 and match[0] and not match[1]:
                            return int(float(match[0]) * 60)  # Konwertuj godziny na minuty
                            
                        # Format tylko z minutami (np. "90min")
                        elif len(match) == 2 and not match[0] and match[1]:
                            return int(float(match[1]))  # Zwróć minuty bezpośrednio
                            
                    # Obsługa pojedynczej wartości (string)
                    else:
                        # Sprawdź kontekst - czy to minuty czy godziny
                        if 'min' in text.lower():
                            return int(float(match))  # Zwróć jako minuty
                        else:
                            return int(float(match) * 60)  # Konwertuj godziny na minuty
                            
                except (ValueError, TypeError):
                    # Jeśli konwersja się nie powiodła, spróbuj następny wzorzec
                    continue
                    
        # Jeśli żaden wzorzec nie pasował lub wszystkie konwersje się nie powiodły
        return None
    
    def extract_elevation(self, text: str) -> Optional[int]:
        """
        Wydobywa informacje o wysokości/przewyższeniu z tekstu opisu trasy.
        
        Metoda rozpoznaje następujące formaty wysokości:
        - "1650 m n.p.m." -> 1650 metrów
        - "przewyższenie 500m" -> 500 metrów
        - "wysokość: 2000 m" -> 2000 metrów
        - "1200m npm" -> 1200 metrów
        
        Args:
            text: Tekst do analizy zawierający informacje o wysokości
            
        Returns:
            int: Wysokość w metrach (np. 1650)
            None: Jeśli nie znaleziono informacji o wysokości lub wystąpił błąd
            
        Przykłady:
            extract_elevation("Szczyt na 1650 m n.p.m.") -> 1650
            extract_elevation("Przewyższenie wynosi 500m") -> 500
            extract_elevation("Brak informacji") -> None
        """
        # Iteracja przez wszystkie wzorce wysokości zdefiniowane w __init__
        for pattern in self.patterns['elevation']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            if matches:  # Jeśli znaleziono jakieś dopasowania
                try:
                    # Weź pierwsze dopasowanie i konwertuj na int
                    return int(matches[0])
                except (ValueError, TypeError):
                    # Jeśli konwersja się nie powiodła, spróbuj następny wzorzec
                    continue
                    
        # Jeśli żaden wzorzec nie pasował lub wszystkie konwersje się nie powiodły
        return None
    
    def extract_coordinates(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Standaryzuje różne formaty zapisu współrzędnych geograficznych.
        
        Metoda rozpoznaje następujące formaty współrzędnych:
        - "N49°15'30\" E20°05'45\"" -> ("N49°15'30\"", "E20°05'45\"")
        - "49.2583°N, 20.0958°E" -> ("49.2583°N", "20.0958°E")
        - "49.2583 N 20.0958 E" -> ("49.2583 N", "20.0958 E")
        
        Args:
            text: Tekst do analizy zawierający współrzędne GPS
            
        Returns:
            Tuple[str, str]: Krotka (szerokość_geograficzna, długość_geograficzna)
            None: Jeśli nie znaleziono współrzędnych lub wystąpił błąd
            
        Przykłady:
            extract_coordinates("Start: N49°15'30\" E20°05'45\"") -> ("N49°15'30\"", "E20°05'45\"")
            extract_coordinates("Brak współrzędnych") -> None
        """
        # Iteracja przez wszystkie wzorce współrzędnych zdefiniowane w __init__
        for pattern in self.patterns['coordinates']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            if matches:  # Jeśli znaleziono jakieś dopasowania
                try:
                    match = matches[0]  # Weź pierwsze dopasowanie
                    
                    # Sprawdź czy dopasowanie to krotka z dwoma elementami
                    if isinstance(match, tuple) and len(match) == 2:
                        # Zwróć oczyszczone współrzędne (usuń białe znaki)
                        return (match[0].strip(), match[1].strip())
                        
                except (ValueError, TypeError):
                    # Jeśli przetwarzanie się nie powiodło, spróbuj następny wzorzec
                    continue
                    
        # Jeśli żaden wzorzec nie pasował lub wszystkie konwersje się nie powiodły
        return None
    
    def extract_landmarks(self, text: str) -> List[str]:
        """
        Identyfikuje punkty charakterystyczne na trasie (schroniska, szczyty, przełęcze).
        
        Metoda rozpoznaje następujące typy punktów charakterystycznych:
        - Schroniska: "Schronisko PTTK", "Schronisko na Hali Gąsienicowej"
        - Szczyty: "Szczyt Giewont", "Szczyt Kasprowy Wierch"
        - Przełęcze: "Przełęcz Zawrat", "Przełęcz Krzyżne"
        - Doliny: "Dolina Pięciu Stawów", "Dolina Kościeliska"
        - Jeziora: "Jezioro Morskie Oko", "Jezioro Czarny Staw"
        - Wodospady: "Wodospad Siklawa", "Wodospad Wodogrzmoty"
        - Punkty widokowe: "Punkt widokowy na Gubałówce"
        
        Args:
            text: Tekst do analizy zawierający opis trasy
            
        Returns:
            List[str]: Lista unikalnych punktów charakterystycznych znalezionych w tekście
                      (bez duplikatów, z zachowaniem kolejności pierwszego wystąpienia)
            
        Przykłady:
            extract_landmarks("Trasa prowadzi przez Schronisko PTTK na Szczyt Giewont") 
            -> ["Schronisko PTTK", "Szczyt Giewont"]
        """
        landmarks = []  # Lista na znalezione punkty charakterystyczne
        
        # Iteracja przez wszystkie wzorce punktów charakterystycznych
        for pattern in self.patterns['landmarks']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            # Dodaj wszystkie znalezione punkty do listy (z oczyszczeniem białych znaków)
            landmarks.extend([match.strip() for match in matches])
        
        # Usuwanie duplikatów z zachowaniem kolejności pierwszego wystąpienia
        # dict.fromkeys() zachowuje kolejność i usuwa duplikaty
        return list(dict.fromkeys(landmarks))
    
    def extract_warnings(self, text: str) -> List[str]:
        """
        Rozpoznaje ostrzeżenia i zagrożenia w opisach tras turystycznych.
        
        Metoda identyfikuje różne typy ostrzeżeń:
        - Bezpośrednie ostrzeżenia: "Uwaga: ślisko po deszczu"
        - Zagrożenia: "Niebezpieczne przejście", "Strome zbocze"
        - Trudności: "Trudny odcinek", "Wymagana ostrożność"
        - Warunki: "Śliskie kamienie", "Zagrożenie lawinowe"
        
        Args:
            text: Tekst do analizy zawierający opis trasy
            
        Returns:
            List[str]: Lista unikalnych ostrzeżeń znalezionych w tekście
                      (bez duplikatów, z zachowaniem kolejności, puste stringi są filtrowane)
            
        Przykłady:
            extract_warnings("Uwaga: ślisko po deszczu. Niebezpieczne przejście przez skały.")
            -> ["ślisko po deszczu", "Niebezpieczne przejście przez skały"]
        """
        warnings = []  # Lista na znalezione ostrzeżenia
        
        # Iteracja przez wszystkie wzorce ostrzeżeń
        for pattern in self.patterns['warnings']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            # Dodaj wszystkie niepuste ostrzeżenia do listy (z oczyszczeniem białych znaków)
            warnings.extend([match.strip() for match in matches if match.strip()])
        
        # Usuwanie duplikatów z zachowaniem kolejności pierwszego wystąpienia
        return list(dict.fromkeys(warnings))
    
    def extract_difficulty(self, text: str) -> Optional[str]:
        """
        Ekstraktuje poziom trudności trasy z opisu tekstowego.
        
        Metoda rozpoznaje następujące poziomy trudności:
        - "łatwa" - trasy dostępne dla wszystkich
        - "średnia" lub "średnio trudna" - trasy wymagające podstawowej kondycji
        - "trudna" - trasy wymagające dobrej kondycji i doświadczenia
        - "bardzo trudna" - trasy dla zaawansowanych turystów
        
        Args:
            text: Tekst do analizy zawierający opis trudności trasy
            
        Returns:
            str: Poziom trudności w formie znormalizowanej (małe litery)
            None: Jeśli nie znaleziono informacji o trudności
            
        Przykłady:
            extract_difficulty("To jest trudna trasa górska") -> "trudna"
            extract_difficulty("Poziom trudności: średni") -> "średni"
            extract_difficulty("Łatwa trasa dla rodzin") -> "łatwa"
        """
        # Iteracja przez wszystkie wzorce trudności
        for pattern in self.patterns['difficulty']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            if matches:  # Jeśli znaleziono jakieś dopasowania
                # Zwróć pierwsze dopasowanie w formie znormalizowanej (małe litery, bez białych znaków)
                return matches[0].strip().lower()
                
        # Jeśli żaden wzorzec nie pasował
        return None
    
    def extract_season_info(self, text: str) -> Optional[str]:
        """
        Wydobywa informacje o sezonowości i zalecanych porach dla trasy.
        
        Metoda rozpoznaje następujące informacje sezonowe:
        - Zalecane pory roku: "najlepiej latem", "zalecana pora: wiosna"
        - Pory dnia: "wczesnym rankiem", "wieczorem", "w południe"
        - Sezony: "sezon letni", "sezon zimowy"
        - Warunki czasowe: "po roztopach", "przed śniegami"
        
        Args:
            text: Tekst do analizy zawierający informacje o sezonowości
            
        Returns:
            str: Informacje o sezonowości (z oczyszczonymi białymi znakami)
            None: Jeśli nie znaleziono informacji o sezonowości
            
        Przykłady:
            extract_season_info("Najlepiej latem, unikać zimy") -> "latem"
            extract_season_info("Zalecana pora: wczesne rano") -> "wczesne rano"
            extract_season_info("Brak informacji") -> None
        """
        # Iteracja przez wszystkie wzorce sezonowości
        for pattern in self.patterns['season']:
            matches = pattern.findall(text)  # Znajdź wszystkie dopasowania
            if matches:  # Jeśli znaleziono jakieś dopasowania
                # Zwróć pierwsze dopasowanie z oczyszczonymi białymi znakami
                return matches[0].strip()
                
        # Jeśli żaden wzorzec nie pasował
        return None
    
    def process_trail_description(self, description: str) -> ExtractedTrailInfo:
        """
        Główna metoda przetwarzająca opis trasy i ekstraktująca wszystkie informacje.
        
        Ta metoda stanowi centralny punkt przetwarzania - wywołuje wszystkie metody
        ekstraktujące i łączy wyniki w jeden obiekt ExtractedTrailInfo.
        
        Proces przetwarzania:
        1. Walidacja danych wejściowych
        2. Logowanie rozpoczęcia przetwarzania
        3. Wywołanie wszystkich metod ekstraktujących:
           - extract_duration() - czas przejścia
           - extract_elevation() - wysokość/przewyższenie
           - extract_landmarks() - punkty charakterystyczne
           - extract_warnings() - ostrzeżenia i zagrożenia
           - extract_coordinates() - współrzędne GPS
           - extract_difficulty() - poziom trudności
           - extract_season_info() - informacje sezonowe
        4. Utworzenie obiektu wynikowego
        5. Logowanie podsumowania wyników
        
        Args:
            description: Pełny opis trasy do analizy (string)
            
        Returns:
            ExtractedTrailInfo: Obiekt zawierający wszystkie wyekstraktowane informacje
                               Jeśli opis jest pusty/nieprawidłowy, zwraca pusty obiekt
            
        Przykłady:
            info = process_trail_description("Trasa 5km, 2h 30min, Szczyt Giewont 1895m n.p.m.")
            print(f"Czas: {info.duration_minutes} minut")  # 150
            print(f"Wysokość: {info.elevation_gain} m")     # 1895
            print(f"Punkty: {info.landmarks}")              # ["Szczyt Giewont"]
        """
        # Walidacja danych wejściowych
        if not description or not isinstance(description, str):
            # Zwróć pusty obiekt jeśli opis jest nieprawidłowy
            return ExtractedTrailInfo()
        
        # Logowanie rozpoczęcia przetwarzania (pierwsze 100 znaków opisu)
        logger.info(f"Przetwarzanie opisu trasy: {description[:100]}...")
        
        # Utworzenie obiektu wynikowego z wywołaniem wszystkich metod ekstraktujących
        extracted_info = ExtractedTrailInfo(
            duration_minutes=self.extract_duration(description),      # Czas w minutach
            elevation_gain=self.extract_elevation(description),       # Wysokość w metrach
            landmarks=self.extract_landmarks(description),            # Lista punktów charakterystycznych
            warnings=self.extract_warnings(description),              # Lista ostrzeżeń
            coordinates=self.extract_coordinates(description),        # Współrzędne GPS
            difficulty_level=self.extract_difficulty(description),    # Poziom trudności
            recommended_season=self.extract_season_info(description)  # Informacje sezonowe
        )
        
        # Logowanie podsumowania wyekstraktowanych informacji
        logger.info(f"Wyekstraktowano: czas={extracted_info.duration_minutes}min, "
                   f"przewyższenie={extracted_info.elevation_gain}m, "
                   f"punkty={len(extracted_info.landmarks)}, "
                   f"ostrzeżenia={len(extracted_info.warnings)}")
        
        return extracted_info
    
    def enhance_trail_data(self, trail_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rozszerza dane trasy o informacje wyekstraktowane z opisu tekstowego.
        
        Ta metoda służy jako interfejs do integracji z istniejącymi danymi tras.
        Pobiera słownik z danymi trasy, ekstraktuje dodatkowe informacje z opisu
        i zwraca rozszerzony słownik z nowymi polami.
        
        Proces rozszerzania:
        1. Utworzenie kopii oryginalnych danych (bez modyfikacji oryginału)
        2. Pobranie opisu trasy z pola 'description'
        3. Przetworzenie opisu przez process_trail_description()
        4. Dodanie wyekstraktowanych informacji jako nowe pola
        5. Dodanie znacznika czasu przetwarzania
        
        Nowe pola dodawane do danych trasy:
        - extracted_duration_minutes: Czas przejścia w minutach
        - extracted_elevation_gain: Przewyższenie w metrach
        - landmarks: Lista punktów charakterystycznych
        - warnings: Lista ostrzeżeń i zagrożeń
        - extracted_coordinates: Współrzędne GPS
        - extracted_difficulty: Poziom trudności
        - recommended_season: Zalecana pora roku
        - processing_timestamp: Znacznik czasu przetwarzania
        
        Args:
            trail_data: Słownik z danymi trasy (musi zawierać pole 'description')
            
        Returns:
            Dict[str, Any]: Rozszerzony słownik z dodatkowymi informacjami
                           Jeśli brak opisu, zwraca kopię oryginalnych danych
            
        Przykłady:
            original_data = {
                'name': 'Szlak na Giewont',
                'description': 'Trasa 5km, 2h 30min, trudna, Szczyt Giewont 1895m'
            }
            enhanced = enhance_trail_data(original_data)
            print(enhanced['extracted_duration_minutes'])  # 150
            print(enhanced['extracted_elevation_gain'])     # 1895
        """
        # Utworzenie kopii oryginalnych danych (bez modyfikacji oryginału)
        enhanced_trail = trail_data.copy()
        
        # Pobranie opisu trasy z danych (domyślnie pusty string jeśli brak)
        description = trail_data.get('description', '')
        if not description:
            # Jeśli brak opisu, zwróć niezmienione dane
            return enhanced_trail
        
        # Przetworzenie opisu przez główną metodę ekstraktującą
        extracted_info = self.process_trail_description(description)
        
        # Dodanie wyekstraktowanych informacji do danych trasy
        enhanced_trail.update({
            'extracted_duration_minutes': extracted_info.duration_minutes,    # Czas w minutach
            'extracted_elevation_gain': extracted_info.elevation_gain,        # Wysokość w metrach
            'landmarks': extracted_info.landmarks,                           # Punkty charakterystyczne
            'warnings': extracted_info.warnings,                             # Ostrzeżenia
            'extracted_coordinates': extracted_info.coordinates,              # Współrzędne GPS
            'extracted_difficulty': extracted_info.difficulty_level,          # Poziom trudności
            'recommended_season': extracted_info.recommended_season,          # Sezonowość
            'processing_timestamp': datetime.datetime.now().isoformat()      # Znacznik czasu
        })
        
        return enhanced_trail