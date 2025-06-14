"""
Klasa ChartGenerator do tworzenia wykresów dla raportów PDF
zgodnie z wymaganiami z updatelist.txt.
"""

# Konfiguracja matplotlib przed importem pyplot - naprawia błąd Qt na Windows
import matplotlib
matplotlib.use('Agg')  # Backend bez GUI - rozwiązuje problem Qt
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
import os
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja wykresów
plt.style.use('default')
try:
    sns.set_palette("husl")
except Exception as e:
    logger.warning(f"Nie można ustawić palety seaborn: {e}")

class ChartGenerator:
    """
    Klasa do generowania różnych typów wykresów dla raportów o trasach turystycznych.
    """
    
    def __init__(self, output_dir: str = "reports/charts"):
        """
        Inicjalizacja generatora wykresów.
        
        Args:
            output_dir: Katalog do zapisywania wykresów
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Konfiguracja kolorów i stylów
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336',
            'info': '#2196F3',
            'light': '#F5F5F5',
            'dark': '#212121'
        }
        
        # Konfiguracja matplotlib
        plt.rcParams.update({
            'font.size': 10,
            'font.family': 'sans-serif',
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 16
        })
    
    def create_length_histogram(self, trails_data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Tworzy histogram długości tras.
        
        Args:
            trails_data: Lista danych tras
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            filename = f"length_histogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Wyekstraktuj długości tras
        lengths = [trail.get('length_km', 0) for trail in trails_data if trail.get('length_km')]
        
        if not lengths:
            logger.warning("Brak danych o długości tras")
            return None
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Histogram z dostosowaną liczbą binów
        n_bins = min(20, len(set(lengths)))
        ax.hist(lengths, bins=n_bins, color=self.colors['primary'], alpha=0.7, edgecolor='white')
        
        # Konfiguracja wykresu
        ax.set_xlabel('Długość trasy (km)')
        ax.set_ylabel('Liczba tras')
        ax.set_title('Rozkład długości analizowanych tras', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Dodaj statystyki
        mean_length = np.mean(lengths)
        median_length = np.median(lengths)
        ax.axvline(mean_length, color=self.colors['danger'], linestyle='--', linewidth=2, label=f'Średnia: {mean_length:.1f} km')
        ax.axvline(median_length, color=self.colors['warning'], linestyle='--', linewidth=2, label=f'Mediana: {median_length:.1f} km')
        
        ax.legend()
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono histogram długości tras: {file_path}")
        return file_path
    
    def create_category_pie_chart(self, trails_data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Generuje wykres kołowy kategorii tras.
        
        Args:
            trails_data: Lista danych tras
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            filename = f"category_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Zlicz kategorie
        categories = {}
        for trail in trails_data:
            category = trail.get('category', 'nieskategoryzowana')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        if not categories:
            logger.warning("Brak danych o kategoriach tras")
            return None
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(10, 10))
        
        labels = list(categories.keys())
        sizes = list(categories.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        # Wykres kołowy z procentami
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                         colors=colors, startangle=90, textprops={'fontsize': 11})
        
        # Konfiguracja
        ax.set_title('Rozkład kategorii tras', fontsize=16, fontweight='bold')
        
        # Legenda
        ax.legend(wedges, [f'{label}: {size}' for label, size in zip(labels, sizes)],
                 title="Kategorie", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono wykres kołowy kategorii: {file_path}")
        return file_path
    
    def create_rating_bar_chart(self, trails_data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Wykres słupkowy ocen użytkowników.
        
        Args:
            trails_data: Lista danych tras
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            filename = f"rating_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Wyekstraktuj oceny
        ratings = []
        for trail in trails_data:
            rating = trail.get('user_rating') or trail.get('rating')
            if rating and isinstance(rating, (int, float)):
                ratings.append(round(rating))
        
        if not ratings:
            logger.warning("Brak danych o ocenach tras")
            return None
        
        # Zlicz oceny
        rating_counts = {i: ratings.count(i) for i in range(1, 6)}
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = list(rating_counts.keys())
        y = list(rating_counts.values())
        bars = ax.bar(x, y, color=self.colors['primary'], alpha=0.8, edgecolor='white')
        
        # Dodaj wartości na słupkach
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # Konfiguracja
        ax.set_xlabel('Ocena (gwiazdki)')
        ax.set_ylabel('Liczba tras')
        ax.set_title('Rozkład ocen użytkowników', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'{i} ★' for i in x])
        ax.grid(True, alpha=0.3, axis='y')
        
        # Dodaj średnią ocenę
        if ratings:
            avg_rating = np.mean(ratings)
            ax.axvline(avg_rating, color=self.colors['danger'], linestyle='--', 
                      linewidth=2, label=f'Średnia: {avg_rating:.1f} ★')
            ax.legend()
        
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono wykres słupkowy ocen: {file_path}")
        return file_path
    
    def create_seasonal_heatmap(self, trails_data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Mapa ciepła dostępności tras w poszczególnych miesiącach.
        
        Args:
            trails_data: Lista danych tras
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            filename = f"seasonal_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Symulowane dane sezonowości (w rzeczywistej aplikacji z analizy recenzji)
        months = ['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 
                 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru']
        
        categories = ['rodzinna', 'widokowa', 'sportowa', 'ekstremalna']
        
        # Przykładowe dane popularności (0-100)
        np.random.seed(42)  # Dla powtarzalności
        data = np.random.randint(20, 100, size=(len(categories), len(months)))
        
        # Modyfikacja dla realności (zima mniej popularna dla ekstremalnych)
        data[3, [0, 1, 11]] = np.random.randint(10, 30, 3)  # ekstremalna zima
        data[0, [5, 6, 7]] = np.random.randint(80, 100, 3)  # rodzinna lato
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(12, 6))
        
        im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
        
        # Konfiguracja osi
        ax.set_xticks(np.arange(len(months)))
        ax.set_yticks(np.arange(len(categories)))
        ax.set_xticklabels(months)
        ax.set_yticklabels([cat.capitalize() for cat in categories])
        
        # Obrót etykiet
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Dodaj wartości w komórkach
        for i in range(len(categories)):
            for j in range(len(months)):
                text = ax.text(j, i, f'{data[i, j]}%', ha="center", va="center", 
                             color="white" if data[i, j] < 50 else "black", fontweight='bold')
        
        # Tytuł i kolorbar
        ax.set_title("Popularność kategorii tras według miesięcy", fontsize=16, fontweight='bold')
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Popularność (%)', rotation=270, labelpad=20)
        
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono mapę ciepła sezonowości: {file_path}")
        return file_path
    
    def create_elevation_profile(self, trail_data: Dict[str, Any], filename: str = None) -> str:
        """
        Wykresy liniowe pokazujące profile wysokościowe.
        
        Args:
            trail_data: Dane pojedynczej trasy
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            trail_name = trail_data.get('name', 'unknown').replace(' ', '_')
            filename = f"elevation_profile_{trail_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Symulowane dane profilu wysokościowego
        length_km = trail_data.get('length_km', 10)
        elevation_gain = trail_data.get('elevation_gain', 500)
        
        # Generuj symulowany profil
        distance_points = np.linspace(0, length_km, 100)
        # Prosty model: stopniowy wzrost z kilkoma wzniesieniami
        base_elevation = 500
        elevation_profile = base_elevation + (elevation_gain * distance_points / length_km) + \
                          50 * np.sin(distance_points * 3) + \
                          30 * np.sin(distance_points * 7)
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Wypełnij obszar pod krzywą
        ax.fill_between(distance_points, elevation_profile, alpha=0.3, color=self.colors['primary'])
        ax.plot(distance_points, elevation_profile, color=self.colors['primary'], linewidth=2)
        
        # Konfiguracja
        ax.set_xlabel('Dystans (km)')
        ax.set_ylabel('Wysokość (m n.p.m.)')
        ax.set_title(f'Profil wysokościowy: {trail_data.get("name", "Nieznana trasa")}', 
                    fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Dodaj informacje o trasie
        info_text = f"Długość: {length_km:.1f} km\n"
        info_text += f"Przewyższenie: {elevation_gain} m\n"
        info_text += f"Maks. wysokość: {max(elevation_profile):.0f} m"
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono profil wysokościowy: {file_path}")
        return file_path
    
    def create_radar_chart(self, trail_data: Dict[str, Any], filename: str = None) -> str:
        """
        Wykresy radarowe oceniające trasy pod względem różnych kryteriów.
        
        Args:
            trail_data: Dane trasy
            filename: Nazwa pliku do zapisania
            
        Returns:
            Ścieżka do zapisanego wykresu
        """
        if not filename:
            trail_name = trail_data.get('name', 'unknown').replace(' ', '_')
            filename = f"radar_chart_{trail_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Kryteria oceny
        categories = ['Widoki', 'Dostępność', 'Trudność', 'Bezpieczeństwo', 'Oznakowanie', 'Infrastruktura']
        
        # Konwertuj dane trasy na oceny (0-100)
        difficulty = trail_data.get('difficulty', 2)
        length = trail_data.get('length_km', 10)
        rating = trail_data.get('user_rating', 3.5)
        
        # Symulowane oceny na podstawie danych trasy
        values = [
            min(100, rating * 20),  # Widoki
            max(20, 100 - length * 5),  # Dostępność (krótsze = bardziej dostępne)
            difficulty * 30,  # Trudność
            min(100, rating * 18 + 10),  # Bezpieczeństwo
            min(100, rating * 15 + 25),  # Oznakowanie
            min(100, rating * 12 + 30)   # Infrastruktura
        ]
        
        # Dodaj pierwszy punkt na końcu dla zamknięcia wykresu
        values += values[:1]
        
        # Kąty dla każdej kategorii
        angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
        angles += angles[:1]
        
        # Utwórz wykres
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Narysuj wykres
        ax.plot(angles, values, 'o-', linewidth=2, label=trail_data.get('name', 'Trasa'), color=self.colors['primary'])
        ax.fill(angles, values, alpha=0.25, color=self.colors['primary'])
        
        # Dodaj etykiety kategorii
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        
        # Konfiguracja skali
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9)
        ax.grid(True)
        
        # Tytuł
        plt.title(f'Profil oceny trasy: {trail_data.get("name", "Nieznana trasa")}', 
                 size=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Zapisz wykres
        file_path = os.path.join(self.output_dir, filename)
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Utworzono wykres radarowy: {file_path}")
        return file_path
    
    def generate_all_charts(self, trails_data: List[Dict[str, Any]], report_name: str = None) -> Dict[str, str]:
        """
        Generuje wszystkie wykresy dla raportu.
        
        Args:
            trails_data: Lista danych tras
            report_name: Nazwa raportu (używana w nazwach plików)
            
        Returns:
            Słownik z nazwami wykresów i ścieżkami do plików
        """
        if not report_name:
            report_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        charts = {}
        
        logger.info(f"Generowanie wykresów dla raportu: {report_name}")
        
        # Generuj wszystkie typy wykresów
        chart_functions = [
            ('length_histogram', self.create_length_histogram),
            ('category_pie', self.create_category_pie_chart),
            ('rating_bar', self.create_rating_bar_chart),
            ('seasonal_heatmap', self.create_seasonal_heatmap),
        ]
        
        for chart_name, chart_function in chart_functions:
            try:
                filename = f"{report_name}_{chart_name}.png"
                chart_path = chart_function(trails_data, filename)
                if chart_path:
                    charts[chart_name] = chart_path
            except Exception as e:
                logger.error(f"Błąd podczas generowania wykresu {chart_name}: {e}")
        
        # Generuj profil wysokościowy dla pierwszej trasy
        if trails_data:
            try:
                filename = f"{report_name}_elevation_profile.png"
                chart_path = self.create_elevation_profile(trails_data[0], filename)
                if chart_path:
                    charts['elevation_profile'] = chart_path
            except Exception as e:
                logger.error(f"Błąd podczas generowania profilu wysokościowego: {e}")
        
        # Generuj wykres radarowy dla pierwszej trasy
        if trails_data:
            try:
                filename = f"{report_name}_radar_chart.png"
                chart_path = self.create_radar_chart(trails_data[0], filename)
                if chart_path:
                    charts['radar_chart'] = chart_path
            except Exception as e:
                logger.error(f"Błąd podczas generowania wykresu radarowego: {e}")
        
        logger.info(f"Wygenerowano {len(charts)} wykresów dla raportu {report_name}")
        return charts 