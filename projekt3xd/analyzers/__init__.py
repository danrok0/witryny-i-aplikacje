"""
MODUŁ INICJALIZACYJNY PAKIETU ANALYZERS
======================================

Ten plik służy jako punkt wejścia do pakietu analyzers, który zawiera
klasy odpowiedzialne za analizę i przetwarzanie danych tekstowych
w systemie rekomendacji tras turystycznych.

STRUKTURA PAKIETU:
- text_processor.py: Klasa TextProcessor do ekstrakcji informacji z opisów tras
- review_analyzer.py: Klasa ReviewAnalyzer do analizy sentymentu recenzji

FUNKCJONALNOŚĆ:
Pakiet umożliwia:
1. Automatyczne wydobywanie kluczowych informacji z opisów tras (czas, wysokość, trudność)
2. Analizę sentymentu i ekstrakcję danych z recenzji użytkowników
3. Standaryzację i normalizację danych tekstowych

UŻYCIE:
from analyzers import TextProcessor, ReviewAnalyzer

processor = TextProcessor()
analyzer = ReviewAnalyzer()
"""

# ============================================================================
# IMPORTY KLAS Z MODUŁÓW PAKIETU
# ============================================================================

# Import klasy TextProcessor z modułu text_processor
# Klasa odpowiedzialna za przetwarzanie opisów tras i ekstrakcję informacji
from .text_processor import TextProcessor

# Import klasy ReviewAnalyzer z modułu review_analyzer  
# Klasa odpowiedzialna za analizę recenzji użytkowników i sentymentu
from .review_analyzer import ReviewAnalyzer

# ============================================================================
# DEFINICJA PUBLICZNEGO API PAKIETU
# ============================================================================

# Lista __all__ definiuje, które klasy będą dostępne przy imporcie z gwiazdką
# Przykład: from analyzers import *
# Dzięki temu tylko te klasy będą zaimportowane, co zapewnia czystość namespace
__all__ = ['TextProcessor', 'ReviewAnalyzer'] 