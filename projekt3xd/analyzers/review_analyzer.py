"""
MODUŁ ANALIZY RECENZJI UŻYTKOWNIKÓW - SENTYMENT I EKSTRAKCJA DANYCH
==================================================================

Ten moduł zawiera klasę ReviewAnalyzer, która analizuje recenzje użytkowników
tras turystycznych pod kątem sentymentu, ocen, dat i innych kluczowych informacji.

FUNKCJONALNOŚCI:
- Ekstrakcja ocen liczbowych w różnych formatach (1-5, 1-10, gwiazdki)
- Analiza sentymentu tekstu (pozytywny, negatywny, neutralny)
- Rozpoznawanie dat w różnych formatach polskich
- Identyfikacja aspektów tras (widoki, trudność, oznakowanie, etc.)
- Wykrywanie sezonowości (wiosna, lato, jesień, zima)
- Agregacja statystyk z wielu recenzji

WYMAGANIA: Implementacja zgodna z specyfikacją z updatelist.txt
AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import statistics

# ============================================================================
# KONFIGURACJA LOGOWANIA
# ============================================================================
logging.basicConfig(level=logging.INFO)    # Ustawienia logowania na poziom INFO
logger = logging.getLogger(__name__)       # Logger specyficzny dla tego modułu

# ============================================================================
# STRUKTURY DANYCH
# ============================================================================

@dataclass
class ReviewData:
    """
    Struktura danych przechowująca informacje o pojedynczej recenzji użytkownika.
    
    Attributes:
        text: Oryginalny tekst recenzji użytkownika
        rating: Ocena liczbowa w skali 1-5 (None jeśli nie znaleziono)
        sentiment: Wydźwięk emocjonalny ('positive', 'negative', 'neutral')
        date: Data napisania recenzji w formacie YYYY-MM-DD
        aspects: Lista aspektów trasy wspomnianych w recenzji
        season: Pora roku wspomniana w recenzji ('wiosna', 'lato', 'jesień', 'zima')
    
    Wszystkie pola oprócz text są opcjonalne i mogą mieć wartość None.
    """
    text: str                                    # Tekst recenzji (wymagany)
    rating: Optional[float] = None               # Ocena liczbowa 1-5
    sentiment: Optional[str] = None              # 'positive', 'negative', 'neutral'
    date: Optional[str] = None                   # Data w formacie YYYY-MM-DD
    aspects: List[str] = None                    # Lista aspektów trasy
    season: Optional[str] = None                 # Pora roku
    
    def __post_init__(self):
        """
        Inicjalizacja pustej listy aspektów jeśli nie została podana.
        Wywoływana automatycznie po utworzeniu obiektu.
        """
        if self.aspects is None:
            self.aspects = []  # Pusta lista zamiast None

@dataclass
class ReviewAnalysis:
    """Struktura wyników analizy recenzji."""
    total_reviews: int = 0
    average_rating: Optional[float] = None
    sentiment_distribution: Dict[str, int] = None
    common_aspects: List[Tuple[str, int]] = None
    seasonal_preferences: Dict[str, int] = None
    rating_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.sentiment_distribution is None:
            self.sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        if self.common_aspects is None:
            self.common_aspects = []
        if self.seasonal_preferences is None:
            self.seasonal_preferences = {}
        if self.rating_distribution is None:
            self.rating_distribution = {}

class ReviewAnalyzer:
    """
    Klasa do analizy recenzji użytkowników tras turystycznych.
    """
    
    def __init__(self):
        """Inicjalizacja wzorców i słowników analizy sentymentu."""
        # Wzorce zgodnie z wymaganiami z updatelist.txt
        self.patterns = {
            # Oceny: r'(\d(?:\.\d)?)/5|(\d{1,2})/10|★{1,5}'
            'ratings': [
                re.compile(r'(\d(?:\.\d)?)/5', re.IGNORECASE),
                re.compile(r'(\d{1,2})/10', re.IGNORECASE),
                re.compile(r'(★{1,5})', re.IGNORECASE),
                re.compile(r'(\d(?:\.\d)?)\s*(?:stars?|gwiazdek?|gwiazd)', re.IGNORECASE),
                re.compile(r'ocena[:\s]*(\d(?:\.\d)?)', re.IGNORECASE)
            ],
            
            # Daty: r'(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})'
            'dates': [
                re.compile(r'(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})'),
                re.compile(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})'),
                re.compile(r'byłem\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})', re.IGNORECASE),
                re.compile(r'(styczeń|luty|marzec|kwiecień|maj|czerwiec|lipiec|sierpień|wrzesień|październik|listopad|grudzień)\s*(\d{2,4})', re.IGNORECASE)
            ],
            
            # Aspekty tras
            'aspects': [
                re.compile(r'(widoki?|panorama|krajobraz)', re.IGNORECASE),
                re.compile(r'(trudność|trudne|łatwe|poziom)', re.IGNORECASE),
                re.compile(r'(oznakowanie|znaki|tablice)', re.IGNORECASE),
                re.compile(r'(parking|dojazd|dostęp)', re.IGNORECASE),
                re.compile(r'(czas|długość|dystans)', re.IGNORECASE),
                re.compile(r'(pogoda|warunki|klimat)', re.IGNORECASE),
                re.compile(r'(tłumy?|ludzie|turyści)', re.IGNORECASE),
                re.compile(r'(bezpieczeństwo|niebezpieczne|bezpieczne)', re.IGNORECASE)
            ],
            
            # Sezonowość
            'seasons': [
                re.compile(r'(wiosną|na\s+wiosnę|w\s+marcu|w\s+kwietniu|w\s+maju)', re.IGNORECASE),
                re.compile(r'(latem|w\s+lecie|w\s+czerwcu|w\s+lipcu|w\s+sierpniu)', re.IGNORECASE),
                re.compile(r'(jesienią|na\s+jesień|we\s+wrześniu|w\s+październiku|w\s+listopadzie)', re.IGNORECASE),
                re.compile(r'(zimą|w\s+zimie|w\s+grudniu|w\s+styczniu|w\s+lutym)', re.IGNORECASE)
            ]
        }
        
        # Słowniki dla analizy sentymentu
        self.positive_words = {
            'wspaniały', 'piękny', 'fantastyczny', 'świetny', 'doskonały', 'polecam',
            'rewelacyjny', 'cudowny', 'zachwycający', 'niesamowity', 'super',
            'widoki', 'przepiękny', 'warto', 'bezpieczny', 'komfortowy', 'przyjemny',
            'łatwy', 'dobry', 'fajny', 'miły', 'relaksujący', 'spokojny'
        }
        
        self.negative_words = {
            'trudny', 'niebezpieczny', 'męczący', 'strasznie', 'okropny', 'zły',
            'nie polecam', 'unikać', 'problem', 'problemy', 'źle', 'kiepski',
            'trudności', 'zagrożenie', 'błoto', 'śliskie', 'stromość', 'długie',
            'zbyt', 'bardzo trudne', 'wyczerpujący', 'niedostępny', 'zamknięte'
        }
    
    def extract_rating(self, text: str) -> Optional[float]:
        """
        Ekstraktuje oceny numeryczne z różnych formatów.
        
        Args:
            text: Tekst recenzji
            
        Returns:
            Ocena jako float lub None jeśli nie znaleziono
        """
        for pattern in self.patterns['ratings']:
            matches = pattern.findall(text)
            if matches:
                try:
                    match = matches[0]
                    if isinstance(match, str):
                        if '★' in match:
                            # Zlicz gwiazdki
                            return float(len(match))
                        else:
                            return float(match)
                    elif isinstance(match, tuple):
                        # Znajdź pierwszą niepustą wartość
                        for value in match:
                            if value:
                                if '★' in value:
                                    return float(len(value))
                                else:
                                    rating = float(value)
                                    # Normalizuj do skali 1-5
                                    if rating > 5:
                                        rating = rating / 2  # Z skali 1-10 na 1-5
                                    return rating
                except (ValueError, TypeError):
                    continue
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        Wydobywa daty z opinii użytkowników.
        
        Args:
            text: Tekst recenzji
            
        Returns:
            Data w formacie YYYY-MM-DD lub None jeśli nie znaleziono
        """
        for pattern in self.patterns['dates']:
            matches = pattern.findall(text)
            if matches:
                try:
                    match = matches[0]
                    if isinstance(match, tuple) and len(match) >= 3:
                        day, month, year = match[:3]
                        # Sprawdź format roku
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif isinstance(match, tuple) and len(match) == 2:
                        # Format z nazwą miesiąca
                        month_name, year = match
                        month_map = {
                            'styczeń': '01', 'luty': '02', 'marzec': '03', 'kwiecień': '04',
                            'maj': '05', 'czerwiec': '06', 'lipiec': '07', 'sierpień': '08',
                            'wrzesień': '09', 'październik': '10', 'listopad': '11', 'grudzień': '12'
                        }
                        month_num = month_map.get(month_name.lower(), '01')
                        return f"{year}-{month_num}-01"
                except (ValueError, TypeError):
                    continue
        return None
    
    def extract_aspects(self, text: str) -> List[str]:
        """
        Identyfikuje najczęściej wspominane aspekty trasy.
        
        Args:
            text: Tekst recenzji
            
        Returns:
            Lista znalezionych aspektów
        """
        aspects = []
        aspect_categories = {
            'widoki': ['widoki', 'panorama', 'krajobraz'],
            'trudność': ['trudność', 'trudne', 'łatwe', 'poziom'],
            'oznakowanie': ['oznakowanie', 'znaki', 'tablice'],
            'dojazd': ['parking', 'dojazd', 'dostęp'],
            'czas': ['czas', 'długość', 'dystans'],
            'pogoda': ['pogoda', 'warunki', 'klimat'],
            'tłumy': ['tłumy', 'ludzie', 'turyści'],
            'bezpieczeństwo': ['bezpieczeństwo', 'niebezpieczne', 'bezpieczne']
        }
        
        text_lower = text.lower()
        for category, keywords in aspect_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                aspects.append(category)
        
        return aspects
    
    def extract_season(self, text: str) -> Optional[str]:
        """
        Wydobywa informacje o sezonowości z opinii.
        
        Args:
            text: Tekst recenzji
            
        Returns:
            Nazwa sezonu lub None jeśli nie znaleziono
        """
        season_patterns = {
            'wiosna': self.patterns['seasons'][0],
            'lato': self.patterns['seasons'][1],
            'jesień': self.patterns['seasons'][2],
            'zima': self.patterns['seasons'][3]
        }
        
        for season, pattern in season_patterns.items():
            if pattern.search(text):
                return season
        return None
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analiza sentymentu używając wzorców tekstowych.
        
        Args:
            text: Tekst recenzji
            
        Returns:
            'positive', 'negative' lub 'neutral'
        """
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Dodatkowo sprawdź kontekst negacji
        negation_patterns = [r'nie\s+' + word for word in self.positive_words]
        for pattern in negation_patterns:
            if re.search(pattern, text_lower):
                negative_count += 1
                positive_count = max(0, positive_count - 1)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def process_review(self, review_text: str) -> ReviewData:
        """
        Przetwarza pojedynczą recenzję i ekstraktuje informacje.
        
        Args:
            review_text: Tekst recenzji
            
        Returns:
            ReviewData z wyekstraktowanymi informacjami
        """
        if not review_text or not isinstance(review_text, str):
            return ReviewData(text='')
        
        return ReviewData(
            text=review_text,
            rating=self.extract_rating(review_text),
            sentiment=self.analyze_sentiment(review_text),
            date=self.extract_date(review_text),
            aspects=self.extract_aspects(review_text),
            season=self.extract_season(review_text)
        )
    
    def analyze_reviews(self, reviews: List[str]) -> ReviewAnalysis:
        """
        Analizuje listę recenzji i generuje zbiorczy raport.
        
        Args:
            reviews: Lista tekstów recenzji
            
        Returns:
            ReviewAnalysis ze zbiorczymi wynikami
        """
        if not reviews:
            return ReviewAnalysis()
        
        processed_reviews = [self.process_review(review) for review in reviews]
        analysis = ReviewAnalysis()
        
        analysis.total_reviews = len(processed_reviews)
        
        # Analiza ocen
        ratings = [r.rating for r in processed_reviews if r.rating is not None]
        if ratings:
            analysis.average_rating = statistics.mean(ratings)
            # Rozkład ocen
            analysis.rating_distribution = {}
            for rating in ratings:
                rating_str = str(int(rating)) if rating == int(rating) else str(rating)
                analysis.rating_distribution[rating_str] = analysis.rating_distribution.get(rating_str, 0) + 1
        
        # Analiza sentymentu
        for review in processed_reviews:
            if review.sentiment:
                analysis.sentiment_distribution[review.sentiment] += 1
        
        # Analiza aspektów
        aspect_counts = {}
        for review in processed_reviews:
            for aspect in review.aspects:
                aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1
        
        analysis.common_aspects = sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Analiza sezonowości
        for review in processed_reviews:
            if review.season:
                analysis.seasonal_preferences[review.season] = analysis.seasonal_preferences.get(review.season, 0) + 1
        
        # Logowanie wyników
        avg_rating_str = f"{analysis.average_rating:.2f}" if analysis.average_rating is not None else "brak"
        logger.info(f"Przeanalizowano {analysis.total_reviews} recenzji. Średnia ocena: {avg_rating_str}")
        
        return analysis
    
    def enhance_trail_with_reviews(self, trail_data: Dict[str, Any], reviews: List[str]) -> Dict[str, Any]:
        """
        Rozszerza dane trasy o analizę recenzji użytkowników.
        
        Args:
            trail_data: Słownik z danymi trasy
            reviews: Lista recenzji użytkowników
            
        Returns:
            Rozszerzony słownik z analizą recenzji
        """
        enhanced_trail = trail_data.copy()
        
        if not reviews:
            enhanced_trail['reviews'] = []
            enhanced_trail['review_analysis'] = ReviewAnalysis().__dict__
            return enhanced_trail
        
        # Dodaj surowe recenzje
        enhanced_trail['reviews'] = reviews
        
        # Przeprowadź analizę
        analysis = self.analyze_reviews(reviews)
        
        # Dodaj wyniki analizy
        enhanced_trail['review_analysis'] = {
            'total_reviews': analysis.total_reviews,
            'average_rating': analysis.average_rating,
            'sentiment_distribution': analysis.sentiment_distribution,
            'common_aspects': analysis.common_aspects[:5],  # Top 5 aspektów
            'seasonal_preferences': analysis.seasonal_preferences,
            'rating_distribution': analysis.rating_distribution,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Dodaj podsumowanie do głównych danych trasy
        if analysis.average_rating:
            enhanced_trail['user_rating'] = round(analysis.average_rating, 1)
        
        # Dodaj najczęstsze aspekty jako tagi
        if analysis.common_aspects:
            existing_tags = enhanced_trail.get('tags', [])
            new_tags = [aspect for aspect, _ in analysis.common_aspects[:3]]
            enhanced_trail['tags'] = list(set(existing_tags + new_tags))
        
        return enhanced_trail 