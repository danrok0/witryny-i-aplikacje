"""
Moduł do ekstraktowania danych z dokumentów HTML i portali internetowych
dla systemu rekomendacji tras turystycznych.
"""

from .html_route_extractor import HTMLRouteExtractor
from .web_data_collector import WebDataCollector

__all__ = ['HTMLRouteExtractor', 'WebDataCollector'] 