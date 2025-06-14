"""
PAKIET RECOMMENDATION - SYSTEM REKOMENDACJI TRAS TURYSTYCZNYCH
=============================================================

Ten pakiet zawiera główną logikę systemu rekomendacji tras turystycznych.
Implementuje algorytmy rekomendacji oparte na preferencjach użytkownika,
warunkach pogodowych i charakterystyce tras.

GŁÓWNE KLASY:
- TrailRecommender: Główna klasa systemu rekomendacji

FUNKCJONALNOŚCI:
- Rekomendacje tras na podstawie preferencji użytkownika
- Analiza warunków pogodowych
- Kategoryzacja tras (rodzinna, widokowa, sportowa, ekstremalna)
- Obliczanie indeksów komfortu
- Generowanie raportów z rekomendacjami

UŻYCIE:
    from recommendation import TrailRecommender
    
    recommender = TrailRecommender()
    trails = recommender.recommend_trails(
        city="Gdańsk",
        date="2024-06-01",
        difficulty=2
    )

AUTOR: System Rekomendacji Tras Turystycznych
"""

from .trail_recommender import TrailRecommender

# Lista wszystkich publicznych klas/funkcji eksportowanych przez pakiet
__all__ = ['TrailRecommender']

# Informacje o wersji pakietu
__version__ = '1.0.0'
__author__ = 'System Rekomendacji Tras Turystycznych' 