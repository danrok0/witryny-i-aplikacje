"""
WebDataCollector module for automatic data collection from hiking portals.
"""

import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import time
import pickle
from urllib.parse import urljoin, urlparse
import sys
import inspect

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dynamiczny import dla obsługi względnych importów
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir)

try:
    from html_route_extractor import HTMLRouteExtractor, ExtractedRouteData
except ImportError:
    logger.warning("Nie można zaimportować HTMLRouteExtractor, utworzę minimalną implementację")
    
    class ExtractedRouteData:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class HTMLRouteExtractor:
        def extract_route_data(self, url):
            return None

class WebDataCollector:
    """
    Klasa do automatycznego pobierania danych o trasach z popularnych portali turystycznych
    z obsługą różnych struktur HTML i formatów danych oraz mechanizmem cache'owania.
    """
    
    def __init__(self, cache_dir: str = "data/html_cache"):
        """
        Inicjalizacja collectora z konfiguracją portali i cache.
        
        Args:
            cache_dir: Katalog do przechowywania cache'owanych danych
        """
        self.cache_dir = cache_dir
        self.html_extractor = HTMLRouteExtractor()
        
        # Zapewnienie istnienia katalogu cache
        os.makedirs(cache_dir, exist_ok=True)
        
        # Konfiguracja popularnych portali turystycznych
        self.portals = {
            'e-turysta': {
                'base_url': 'https://e-turysta.pl',
                'search_paths': ['/szlaki', '/trasy'],
                'route_patterns': [r'/szlak/(\d+)', r'/trasa/(\d+)'],
                'custom_selectors': {
                    'route_list': '.trail-list .trail-item',
                    'route_link': 'a.trail-link',
                    'route_params': '.trail-params table'
                }
            },
            'traseo': {
                'base_url': 'https://traseo.pl',
                'search_paths': ['/trasy', '/szlaki-piesze'],
                'route_patterns': [r'/trasa/([^/]+)', r'/szlak/([^/]+)'],
                'custom_selectors': {
                    'route_list': '.route-item',
                    'route_link': 'a.route-title',
                    'route_params': '.route-details'
                }
            },
            'szlaki-gorskie': {
                'base_url': 'https://szlaki-gorskie.pl',
                'search_paths': ['/szlaki', '/trasy-gorskie'],
                'route_patterns': [r'/szlak-([^/]+)', r'/trasa-([^/]+)'],
                'custom_selectors': {
                    'route_list': '.szlak-lista .szlak',
                    'route_link': '.szlak-link',
                    'route_params': '.parametry-szlaku'
                }
            }
        }
        
        # Konfiguracja cache (domyślnie 24 godziny)
        self.cache_expiry_hours = 24
        
        # Headers dla zapytań HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def _get_cache_key(self, url: str, params: Dict = None) -> str:
        """
        Generuje klucz cache dla URL i parametrów.
        
        Args:
            url: URL zapytania
            params: Dodatkowe parametry
            
        Returns:
            Hash string jako klucz cache
        """
        cache_string = url
        if params:
            cache_string += json.dumps(params, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """
        Zwraca ścieżkę do pliku cache.
        
        Args:
            cache_key: Klucz cache
            
        Returns:
            Pełna ścieżka do pliku cache
        """
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """
        Sprawdza czy cache jest ważny (nie wygasł).
        
        Args:
            cache_path: Ścieżka do pliku cache
            
        Returns:
            True jeśli cache jest ważny
        """
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expiry_time = datetime.now() - timedelta(hours=self.cache_expiry_hours)
        
        return file_time > expiry_time
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """
        Zapisuje dane do cache.
        
        Args:
            cache_key: Klucz cache
            data: Dane do zapisania
        """
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, f)
            logger.debug(f"Zapisano do cache: {cache_key}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania do cache {cache_key}: {e}")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Ładuje dane z cache.
        
        Args:
            cache_key: Klucz cache
            
        Returns:
            Załadowane dane lub None jeśli nie znaleziono
        """
        cache_path = self._get_cache_path(cache_key)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
                logger.debug(f"Załadowano z cache: {cache_key}")
                return cached_data['data']
        except Exception as e:
            logger.error(f"Błąd podczas ładowania z cache {cache_key}: {e}")
            return None
    
    def _fetch_with_cache(self, url: str, params: Dict = None) -> Optional[BeautifulSoup]:
        """
        Pobiera stronę z obsługą cache.
        
        Args:
            url: URL do pobrania
            params: Parametry zapytania
            
        Returns:
            BeautifulSoup object lub None
        """
        cache_key = self._get_cache_key(url, params)
        
        # Sprawdź cache
        cached_content = self._load_from_cache(cache_key)
        if cached_content:
            logger.info(f"Używam cache dla: {url}")
            return BeautifulSoup(cached_content, 'html.parser')
        
        # Pobierz ze źródła
        try:
            logger.info(f"Pobieranie: {url}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Sprawdź encoding
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            # Zapisz do cache
            self._save_to_cache(cache_key, response.text)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"Błąd podczas pobierania {url}: {e}")
            return None
    
    def discover_route_urls(self, portal_name: str, region: str = None, max_routes: int = 50) -> List[str]:
        """
        Automatycznie odkrywa URLe tras z portalu turystycznego.
        
        Args:
            portal_name: Nazwa portalu ('e-turysta', 'traseo', 'szlaki-gorskie')
            region: Opcjonalny filtr regionu
            max_routes: Maksymalna liczba tras do znalezienia
            
        Returns:
            Lista URLi tras
        """
        if portal_name not in self.portals:
            logger.error(f"Nieznany portal: {portal_name}")
            return []
        
        portal_config = self.portals[portal_name]
        route_urls = []
        
        # Przeszukuj ścieżki wyszukiwania
        for search_path in portal_config['search_paths']:
            if len(route_urls) >= max_routes:
                break
                
            search_url = urljoin(portal_config['base_url'], search_path)
            
            # Dodaj parametry regionu jeśli podano
            params = {}
            if region:
                params['region'] = region
                params['wojewodztwo'] = region
                params['miejsce'] = region
            
            soup = self._fetch_with_cache(search_url, params)
            if not soup:
                continue
            
            # Znajdź linki do tras używając selektorów portalu
            selectors = portal_config['custom_selectors']
            
            # Użyj specyficznych selektorów dla portalu
            route_elements = soup.select(selectors.get('route_list', '.route-item'))
            
            for element in route_elements:
                if len(route_urls) >= max_routes:
                    break
                
                # Znajdź link do trasy
                link_selector = selectors.get('route_link', 'a')
                link_element = element.select_one(link_selector)
                
                if link_element and link_element.get('href'):
                    route_url = urljoin(portal_config['base_url'], link_element['href'])
                    if route_url not in route_urls:
                        route_urls.append(route_url)
            
            # Dodatkowe opóźnienie między requestami
            time.sleep(1)
        
        logger.info(f"Znaleziono {len(route_urls)} tras z portalu {portal_name}")
        return route_urls
    
    def collect_routes_from_portal(self, portal_name: str, region: str = None, max_routes: int = 20) -> List[ExtractedRouteData]:
        """
        Zbiera dane tras z konkretnego portalu turystycznego.
        
        Args:
            portal_name: Nazwa portalu
            region: Opcjonalny filtr regionu
            max_routes: Maksymalna liczba tras
            
        Returns:
            Lista ExtractedRouteData
        """
        logger.info(f"Zbieranie tras z portalu: {portal_name}")
        
        # Odkryj URLe tras
        route_urls = self.discover_route_urls(portal_name, region, max_routes)
        
        if not route_urls:
            logger.warning(f"Nie znaleziono tras w portalu {portal_name}")
            return []
        
        # Ekstraktuj dane z każdej trasy
        routes_data = []
        for i, url in enumerate(route_urls):
            logger.info(f"Przetwarzanie trasy {i+1}/{len(route_urls)} z {portal_name}")
            
            route_data = self.html_extractor.extract_route_data(url)
            if route_data:
                # Dodaj informacje o źródle
                route_data.source_portal = portal_name
                route_data.source_url = url
                routes_data.append(route_data)
            
            # Opóźnienie między requestami
            time.sleep(2)
        
        logger.info(f"Zebrano {len(routes_data)} tras z portalu {portal_name}")
        return routes_data
    
    def collect_routes_from_all_portals(self, region: str = None, max_routes_per_portal: int = 10) -> Dict[str, List[ExtractedRouteData]]:
        """
        Zbiera dane tras ze wszystkich skonfigurowanych portali.
        
        Args:
            region: Opcjonalny filtr regionu
            max_routes_per_portal: Maksymalna liczba tras na portal
            
        Returns:
            Słownik z danymi tras pogrupowanymi po portalach
        """
        all_routes = {}
        
        for portal_name in self.portals.keys():
            logger.info(f"Rozpoczynam zbieranie z portalu: {portal_name}")
            
            try:
                routes = self.collect_routes_from_portal(portal_name, region, max_routes_per_portal)
                all_routes[portal_name] = routes
                
                # Pauza między portalami
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Błąd podczas zbierania z portalu {portal_name}: {e}")
                all_routes[portal_name] = []
        
        total_routes = sum(len(routes) for routes in all_routes.values())
        logger.info(f"Łącznie zebrano {total_routes} tras ze wszystkich portali")
        
        return all_routes
    
    def integrate_with_weather_api(self, routes_data: List[ExtractedRouteData], weather_api) -> List[Dict[str, Any]]:
        """
        Integruje zebrane dane tras z API serwisów pogodowych.
        
        Args:
            routes_data: Lista danych tras
            weather_api: Instancja API pogodowego
            
        Returns:
            Lista zintegrowanych danych tras
        """
        integrated_routes = []
        
        for route_data in routes_data:
            route_dict = {
                'name': route_data.name,
                'length_km': route_data.length,
                'duration': route_data.duration,
                'elevation_gain': route_data.elevation_gain,
                'difficulty': route_data.difficulty,
                'description': route_data.description,
                'images': route_data.images,
                'coordinates': route_data.coordinates,
                'reviews': route_data.reviews,
                'rating': route_data.rating,
                'source_portal': getattr(route_data, 'source_portal', 'unknown'),
                'source_url': getattr(route_data, 'source_url', ''),
                'extraction_date': datetime.now().isoformat()
            }
            
            # Spróbuj dodać dane pogodowe jeśli są współrzędne
            if route_data.coordinates and weather_api:
                try:
                    # Szacowana lokalizacja na podstawie współrzędnych
                    # (w rzeczywistej implementacji można użyć reverse geocoding)
                    weather_data = weather_api.get_weather_forecast('Kraków', datetime.now().strftime('%Y-%m-%d'))
                    if weather_data:
                        route_dict['weather_forecast'] = weather_data
                except Exception as e:
                    logger.warning(f"Nie udało się pobrać danych pogodowych dla trasy {route_data.name}: {e}")
            
            integrated_routes.append(route_dict)
        
        return integrated_routes
    
    def save_collected_data(self, collected_data: Dict[str, List[ExtractedRouteData]], output_file: str) -> None:
        """
        Zapisuje zebrane dane do pliku.
        
        Args:
            collected_data: Zebrane dane tras
            output_file: Ścieżka do pliku wyjściowego
        """
        # Konwertuj na format serializowalny
        serializable_data = {}
        
        for portal_name, routes in collected_data.items():
            serializable_data[portal_name] = []
            for route in routes:
                route_dict = {
                    'name': route.name,
                    'length': route.length,
                    'duration': route.duration,
                    'elevation_gain': route.elevation_gain,
                    'difficulty': route.difficulty,
                    'description': route.description,
                    'images': route.images,
                    'coordinates': route.coordinates,
                    'reviews': route.reviews,
                    'rating': route.rating,
                    'source_portal': getattr(route, 'source_portal', portal_name),
                    'source_url': getattr(route, 'source_url', ''),
                    'extraction_date': datetime.now().isoformat()
                }
                serializable_data[portal_name].append(route_dict)
        
        # Zapisz do pliku
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Zapisano zebrane dane do: {output_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania danych do {output_file}: {e}")
    
    def clear_cache(self, older_than_hours: int = None) -> None:
        """
        Czyści cache starsze niż podany czas.
        
        Args:
            older_than_hours: Usuń pliki starsze niż X godzin (domyślnie wszystkie)
        """
        if not os.path.exists(self.cache_dir):
            return
        
        removed_count = 0
        cutoff_time = None
        
        if older_than_hours:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                file_path = os.path.join(self.cache_dir, filename)
                
                if cutoff_time:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time > cutoff_time:
                        continue
                
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas usuwania {file_path}: {e}")
        
        logger.info(f"Usunięto {removed_count} plików cache")
    
    def collect_sample_data(self) -> List[Dict[str, Any]]:
        """
        Pobiera przykładowe dane tras z różnych portali.
        
        Returns:
            Lista słowników z danymi tras
        """
        sample_trails = [
            {
                'name': 'Szlak Orlich Gniazd',
                'length_km': 164.0,
                'difficulty': 3,
                'terrain_type': 'górski',
                'region': 'Jura Krakowsko-Częstochowska',
                'description': 'Najsłynniejszy szlak turystyczny w Polsce, prowadzący przez malownicze zamki i skały.',
                'elevation_m': 515,
                'estimated_time': 8.5,
                'category': 'widokowa',
                'tags': ['zamki', 'skały', 'historia'],
                'reviews': [
                    'Fantastyczne widoki na zamki! Polecam szczególnie odcinek do Ogrodzieńca.',
                    'Długi ale bardzo ciekawy szlak. Warto zaplanować kilka dni.',
                    'Piękne krajobrazy, ale trzeba być przygotowanym na trudne odcinki.'
                ]
            },
            {
                'name': 'Szlak Pienińska Ścieżka',
                'length_km': 12.5,
                'difficulty': 2,
                'terrain_type': 'górski',
                'region': 'Pieniny',
                'description': 'Malowniczy szlak wzdłuż Dunajca z widokami na Trzy Korony.',
                'elevation_m': 982,
                'estimated_time': 4.0,
                'category': 'widokowa',
                'tags': ['dunajec', 'widoki', 'przełom'],
                'reviews': [
                    'Niesamowite widoki na przełom Dunajca!',
                    'Łatwy szlak, idealny dla rodzin z dziećmi.',
                    'Polecam połączyć z spływem pontonowym.'
                ]
            },
            {
                'name': 'Szlak Mazurski',
                'length_km': 8.3,
                'difficulty': 1,
                'terrain_type': 'nizinny',
                'region': 'Mazury',
                'description': 'Spokojny szlak wokół jezior mazurskich, idealny dla rodzin.',
                'elevation_m': 145,
                'estimated_time': 2.5,
                'category': 'rodzinna',
                'tags': ['jeziora', 'rodzinny', 'łatwy'],
                'reviews': [
                    'Idealny na spacer z dziećmi. Piękne jeziora.',
                    'Bardzo spokojny szlak, można spotkać dużo ptaków.',
                    'Polecam wczesnym rankiem - mniej ludzi.'
                ]
            },
            {
                'name': 'Szlak Karkonoski',
                'length_km': 28.7,
                'difficulty': 3,
                'terrain_type': 'górski',
                'region': 'Karkonosze',
                'description': 'Wymagający szlak przez najwyższe szczyty Karkonoszy.',
                'elevation_m': 1602,
                'estimated_time': 12.0,
                'category': 'ekstremalna',
                'tags': ['śnieżka', 'wysokogórski', 'trudny'],
                'reviews': [
                    'Bardzo wymagający szlak, ale widoki rekompensują trud.',
                    'Uwaga na pogodę - może się szybko zmienić.',
                    'Najlepszy szlak w Karkonoszach dla doświadczonych.'
                ]
            },
            {
                'name': 'Szlak Nadmorski',
                'length_km': 15.2,
                'difficulty': 1,
                'terrain_type': 'nizinny',
                'region': 'Wybrzeże',
                'description': 'Szlak wzdłuż wybrzeża Bałtyku przez wydmy i lasy.',
                'elevation_m': 58,
                'estimated_time': 4.5,
                'category': 'sportowa',
                'tags': ['morze', 'wydmy', 'plaża'],
                'reviews': [
                    'Piękny szlak z widokiem na morze.',
                    'Można połączyć z kąpielą w morzu.',
                    'Uwaga na wiatr - może być silny.'
                ]
            }
        ]
        
        logger.info(f"Wygenerowano {len(sample_trails)} przykładowych tras")
        return sample_trails 