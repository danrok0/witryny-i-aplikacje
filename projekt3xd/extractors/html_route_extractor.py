"""
EKSTRAKTOR DANYCH Z STRON INTERNETOWYCH - MODUŁ POBIERANIA INFORMACJI O TRASACH
============================================================================

Ten moduł zawiera klasę HTMLRouteExtractor do automatycznego parsowania
stron internetowych z opisami tras turystycznych i wydobywania kluczowych informacji.

FUNKCJONALNOŚCI:
- Pobieranie stron internetowych z obsługą różnych kodowań
- Parsowanie HTML przy użyciu BeautifulSoup4
- Ekstrakcja parametrów tras z tabel strukturalnych
- Wydobywanie opisów tekstowych i galerii zdjęć
- Rozpoznawanie współrzędnych GPS z różnych źródeł
- Zbieranie recenzji użytkowników i ocen
- Obsługa różnych selektorów CSS dla popularnych portali

OBSŁUGIWANE ELEMENTY:
- Tabele parametrów tras (długość, czas, trudność)
- Sekcje opisowe z informacjami szczegółowymi
- Galerie zdjęć i materiały multimedialne
- Kontenery map z współrzędnymi GPS
- Sekcje recenzji i ocen użytkowników
- Metadane strukturalne (mikroformaty)

ZGODNOŚĆ: Implementacja zgodna z wymaganiami updatelist.txt
WYMAGANIA: requests, beautifulsoup4, lxml
AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK
# ============================================================================
import re                                       # Wyrażenia regularne
import requests                                 # HTTP requests
from bs4 import BeautifulSoup                   # Parser HTML
from typing import Dict, List, Optional, Any, Tuple  # Podpowiedzi typów
from dataclasses import dataclass               # Struktury danych
import logging                                  # System logowania
import time                                     # Opóźnienia między requestami
from urllib.parse import urljoin, urlparse      # Parsowanie URL

# ============================================================================
# KONFIGURACJA LOGOWANIA
# ============================================================================
logging.basicConfig(level=logging.INFO)        # Poziom logowania
logger = logging.getLogger(__name__)           # Logger dla tego modułu

# ============================================================================
# STRUKTURY DANYCH
# ============================================================================

@dataclass
class ExtractedRouteData:
    """
    Struktura danych przechowująca wszystkie informacje wyekstraktowane z HTML.
    
    Attributes:
        name: Nazwa trasy (np. "Szlak na Rysy")
        length: Długość trasy w kilometrach (np. 12.5)
        duration: Czas przejścia jako string (np. "4h 30min") 
        elevation_gain: Przewyższenie w metrach (np. 800)
        difficulty: Poziom trudności (np. "trudna", "średnia")
        description: Pełny opis trasy z informacjami szczegółowymi
        images: Lista URL-i do zdjęć trasy
        coordinates: Współrzędne GPS jako tuple (lat, lon)
        reviews: Lista tekstów recenzji użytkowników
        rating: Średnia ocena jako liczba (np. 4.5)
        
    Wszystkie pola są opcjonalne - jeśli dana informacja nie została
    znaleziona na stronie, pole ma wartość None lub pustą listę.
    """
    name: Optional[str] = None                          # Nazwa trasy
    length: Optional[float] = None                      # Długość w km
    duration: Optional[str] = None                      # Czas przejścia
    elevation_gain: Optional[int] = None                # Przewyższenie w m
    difficulty: Optional[str] = None                    # Poziom trudności
    description: Optional[str] = None                   # Opis trasy
    images: List[str] = None                           # Lista URL zdjęć
    coordinates: Optional[Tuple[float, float]] = None   # Współrzędne GPS
    reviews: List[str] = None                          # Recenzje użytkowników
    rating: Optional[float] = None                     # Średnia ocena
    
    def __post_init__(self):
        """
        Inicjalizacja pustych list dla pól, które nie mogą być None.
        Wywoływana automatycznie po utworzeniu obiektu.
        """
        if self.images is None:
            self.images = []        # Pusta lista URL-i zdjęć
        if self.reviews is None:
            self.reviews = []       # Pusta lista recenzji

class HTMLRouteExtractor:
    """
    Klasa do parsowania stron internetowych z opisami tras turystycznych.
    """
    
    def __init__(self):
        """Inicjalizacja extractora z konfiguracją selektorów CSS."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Selektory CSS dla różnych typów stron zgodnie z wymaganiami
        self.selectors = {
            'route_params_table': [
                'table.route-params',
                'table.trail-info',
                'table.szlak-parametry',
                '.route-details table',
                '.trail-details table'
            ],
            'route_description': [
                'div.route-description',
                'div.trail-description',
                'div.opis-trasy',
                '.content .description',
                '.route-content'
            ],
            'gallery': [
                'div.gallery',
                'div.photo-gallery',
                'div.galeria',
                '.images',
                '.photos'
            ],
            'map_container': [
                'div#map',
                'div.map-container',
                'div.mapa',
                '.leaflet-container',
                '.google-map'
            ],
            'user_reviews': [
                'div.user-review',
                'div.review',
                'div.opinia',
                '.reviews .review-item',
                '.comments .comment'
            ],
            'rating': [
                '.rating',
                '.ocena',
                '.stars',
                '.gwiazdki'
            ],
            'route_name': [
                'h1',
                'h2.route-name',
                '.trail-title',
                '.route-title'
            ]
        }
        
        # Wzorce do ekstrakcji parametrów z tabel
        self.parameter_patterns = {
            'length': re.compile(r'długość[:\s]*(\d+(?:\.\d+)?)\s*km', re.IGNORECASE),
            'duration': re.compile(r'czas[:\s]*([^<\n]+)', re.IGNORECASE),
            'elevation': re.compile(r'przewyższenie[:\s]*(\d+)\s*m', re.IGNORECASE),
            'difficulty': re.compile(r'trudność[:\s]*([^<\n]+)', re.IGNORECASE)
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Pobiera stronę internetową i zwraca obiekt BeautifulSoup.
        
        Args:
            url: URL strony do pobrania
            
        Returns:
            BeautifulSoup object lub None w przypadku błędu
        """
        try:
            logger.info(f"Pobieranie strony: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Sprawdź encoding
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"Pomyślnie pobrano stronę: {len(response.content)} bajtów")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Błąd podczas pobierania strony {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas przetwarzania {url}: {e}")
            return None
    
    def extract_from_table(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Ekstraktuje strukturalne informacje o trasach z tabel parametrów.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Słownik z wyekstraktowanymi parametrami
        """
        extracted_data = {}
        
        # Znajdź tabele z parametrami tras
        for selector in self.selectors['route_params_table']:
            tables = soup.select(selector)
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Mapowanie kluczy na standardowe nazwy
                        if 'długość' in key or 'distance' in key:
                            match = re.search(r'(\d+(?:\.\d+)?)', value)
                            if match:
                                extracted_data['length'] = float(match.group(1))
                        
                        elif 'czas' in key or 'time' in key or 'duration' in key:
                            extracted_data['duration'] = value
                        
                        elif 'przewyższenie' in key or 'elevation' in key:
                            match = re.search(r'(\d+)', value)
                            if match:
                                extracted_data['elevation_gain'] = int(match.group(1))
                        
                        elif 'trudność' in key or 'difficulty' in key:
                            extracted_data['difficulty'] = value
        
        return extracted_data
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Ekstraktuje opis trasy z sekcji opisowych.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Tekst opisu lub None jeśli nie znaleziono
        """
        for selector in self.selectors['route_description']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 50:  # Filtruj zbyt krótkie opisy
                    return text
        return None
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Ekstraktuje URLe zdjęć z galerii.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            base_url: Bazowy URL strony dla względnych linków
            
        Returns:
            Lista URLi zdjęć
        """
        images = []
        
        # Znajdź galerie zdjęć
        for selector in self.selectors['gallery']:
            galleries = soup.select(selector)
            for gallery in galleries:
                img_tags = gallery.find_all('img')
                for img in img_tags:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        # Konwertuj względne URLe na bezwzględne
                        full_url = urljoin(base_url, src)
                        images.append(full_url)
        
        # Dodatkowe wyszukiwanie wszystkich obrazów na stronie
        if not images:
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '').lower()
                if src and any(keyword in alt for keyword in ['trail', 'szlak', 'góry', 'mountain']):
                    full_url = urljoin(base_url, src)
                    images.append(full_url)
        
        return images[:10]  # Ograniczenie do 10 zdjęć
    
    def extract_coordinates(self, soup: BeautifulSoup) -> Optional[Tuple[float, float]]:
        """
        Ekstraktuje współrzędne z map interaktywnych.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Tuple (latitude, longitude) lub None
        """
        # Szukaj w meta tagach
        meta_geo = soup.find('meta', {'name': 'geo.position'})
        if meta_geo:
            content = meta_geo.get('content')
            if content:
                try:
                    lat, lon = content.split(';')
                    return (float(lat), float(lon))
                except (ValueError, AttributeError):
                    pass
        
        # Szukaj w skryptach JavaScript
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Wzorce dla popularnych map
                lat_lon_patterns = [
                    r'lat[:\s]*([0-9.-]+)[,\s]*lng[:\s]*([0-9.-]+)',
                    r'latitude[:\s]*([0-9.-]+)[,\s]*longitude[:\s]*([0-9.-]+)',
                    r'center[:\s]*\[([0-9.-]+)[,\s]*([0-9.-]+)\]'
                ]
                
                for pattern in lat_lon_patterns:
                    match = re.search(pattern, script.string, re.IGNORECASE)
                    if match:
                        try:
                            return (float(match.group(1)), float(match.group(2)))
                        except ValueError:
                            continue
        
        return None
    
    def extract_reviews(self, soup: BeautifulSoup) -> List[str]:
        """
        Ekstraktuje recenzje użytkowników.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Lista tekstów recenzji
        """
        reviews = []
        
        for selector in self.selectors['user_reviews']:
            reviews_elements = soup.select(selector)
            for element in reviews_elements:
                # Pomiń elementy rating-only
                rating_element = element.find(class_=re.compile(r'rating|stars|gwiazdki'))
                if rating_element:
                    rating_element.decompose()
                
                text = element.get_text(strip=True)
                if len(text) > 20:  # Filtruj zbyt krótkie recenzje
                    reviews.append(text)
        
        return reviews[:20]  # Ograniczenie do 20 recenzji
    
    def extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """
        Ekstraktuje ocenę z elementów rating.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Ocena jako float lub None
        """
        for selector in self.selectors['rating']:
            rating_elements = soup.select(selector)
            for element in rating_elements:
                # Szukaj gwiazdek
                stars = element.find_all(class_=re.compile(r'star|filled'))
                if stars:
                    return float(len(stars))
                
                # Szukaj tekstu z oceną
                text = element.get_text(strip=True)
                rating_match = re.search(r'(\d(?:\.\d)?)[/\s]*(?:5|10)', text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    # Normalizuj do skali 1-5
                    if rating > 5:
                        rating = rating / 2
                    return rating
        
        return None
    
    def extract_route_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Ekstraktuje nazwę trasy.
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Nazwa trasy lub None
        """
        for selector in self.selectors['route_name']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) < 200:  # Filtruj zbyt długie tytuły
                    return text
        
        # Fallback - sprawdź title strony
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return None
    
    def extract_route_data(self, url: str) -> Optional[ExtractedRouteData]:
        """
        Główna metoda ekstraktująca wszystkie dane o trasie ze strony.
        
        Args:
            url: URL strony z opisem trasy
            
        Returns:
            ExtractedRouteData z wyekstraktowanymi informacjami
        """
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        logger.info(f"Ekstraktowanie danych z: {url}")
        
        # Wyekstraktuj wszystkie elementy
        table_data = self.extract_from_table(soup)
        
        extracted_data = ExtractedRouteData(
            name=self.extract_route_name(soup),
            length=table_data.get('length'),
            duration=table_data.get('duration'),
            elevation_gain=table_data.get('elevation_gain'),
            difficulty=table_data.get('difficulty'),
            description=self.extract_description(soup),
            images=self.extract_images(soup, url),
            coordinates=self.extract_coordinates(soup),
            reviews=self.extract_reviews(soup),
            rating=self.extract_rating(soup)
        )
        
        logger.info(f"Wyekstraktowano dane: nazwa='{extracted_data.name}', "
                   f"długość={extracted_data.length}km, "
                   f"zdjęcia={len(extracted_data.images)}, "
                   f"recenzje={len(extracted_data.reviews)}")
        
        return extracted_data
    
    def extract_multiple_routes(self, urls: List[str], delay: float = 1.0) -> List[ExtractedRouteData]:
        """
        Ekstraktuje dane z wielu stron z opóźnieniem między requestami.
        
        Args:
            urls: Lista URLi do przetworzenia
            delay: Opóźnienie między requestami w sekundach
            
        Returns:
            Lista ExtractedRouteData
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Przetwarzanie {i+1}/{len(urls)}: {url}")
            
            extracted_data = self.extract_route_data(url)
            if extracted_data:
                results.append(extracted_data)
            
            # Opóźnienie między requestami
            if i < len(urls) - 1:
                time.sleep(delay)
        
        logger.info(f"Zakończono ekstraktowanie. Przetworzono {len(results)} z {len(urls)} stron.")
        return results 