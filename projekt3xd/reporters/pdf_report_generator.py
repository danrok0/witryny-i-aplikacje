"""
GENERATOR PROFESJONALNYCH RAPORTÓW PDF - MODUŁ TWORZENIA DOKUMENTACJI
====================================================================

Ten moduł zawiera klasę PDFReportGenerator do tworzenia wielostronicowych,
profesjonalnych raportów PDF z rekomendacjami tras turystycznych.

FUNKCJONALNOŚCI:
- Generowanie kompleksowych raportów PDF z wieloma sekcjami
- Automatyczne tworzenie spisu treści i strony tytułowej
- Wbudowane wykresy i wizualizacje danych
- Tabele porównawcze tras z formatowaniem
- Obsługa polskich znaków i czcionek UTF-8
- Profesjonalne nagłówki i stopki na każdej stronie
- Automatyczne numerowanie stron i podrozdziałów

STRUKTURA RAPORTU:
1. Strona tytułowa z metadanymi
2. Spis treści z odnośnikami
3. Podsumowanie wykonawcze
4. Sekcja wykresów i statystyk
5. Szczegółowe opisy tras
6. Tabela porównawcza wszystkich tras

WYMAGANIA: ReportLab, matplotlib, pillow
ZGODNOŚĆ: Implementacja zgodna z wymaganiami updatelist.txt
AUTOR: System Rekomendacji Tras Turystycznych - Etap 4
"""

# ============================================================================
# IMPORTY BIBLIOTEK REPORTLAB - GENEROWANIE PDF
# ============================================================================
from reportlab.lib.pagesizes import letter, A4           # Rozmiary stron
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # Style tekstu
from reportlab.lib.units import inch, cm                 # Jednostki miar
from reportlab.lib import colors                         # Kolory
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY  # Wyrównanie tekstu
from reportlab.pdfgen import canvas                      # Canvas do rysowania
from reportlab.pdfbase import pdfmetrics                 # Metryki czcionek
from reportlab.pdfbase.ttfonts import TTFont             # Czcionki TrueType

# ============================================================================
# IMPORTY BIBLIOTEK STANDARDOWYCH
# ============================================================================
from typing import Dict, List, Any, Optional            # Podpowiedzi typów
import logging                                          # System logowania
import os                                               # Operacje systemowe
from datetime import datetime                           # Obsługa dat
import sys                                              # Funkcje systemowe
import inspect                                          # Inspekcja kodu

# Dynamiczny import dla obsługi względnych importów
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir)

try:
    from chart_generator import ChartGenerator
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Nie można zaimportować ChartGenerator")
    class ChartGenerator:
        def generate_all_charts(self, trails_data, report_name):
            return {}

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """
    Klasa do generowania profesjonalnych raportów PDF z rekomendacjami tras turystycznych.
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Inicjalizacja generatora raportów PDF.
        
        Args:
            output_dir: Katalog do zapisywania raportów
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Inicjalizuj generator wykresów
        self.chart_generator = ChartGenerator()
        
        # Konfiguracja kolorów (musi być przed stylami)
        self.report_colors = {
            'primary': colors.Color(46/255, 134/255, 171/255),      # #2E86AB
            'secondary': colors.Color(162/255, 59/255, 114/255),     # #A23B72
            'success': colors.Color(76/255, 175/255, 80/255),        # #4CAF50
            'warning': colors.Color(255/255, 152/255, 0/255),        # #FF9800
            'danger': colors.Color(244/255, 67/255, 54/255),         # #F44336
            'light_gray': colors.Color(245/255, 245/255, 245/255),   # #F5F5F5
            'dark_gray': colors.Color(33/255, 33/255, 33/255)        # #212121
        }
        
        # Konfiguracja czcionek obsługujących polskie znaki
        self._setup_fonts()
        
        # Konfiguracja stylów (po kolorach)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_fonts(self):
        """Konfiguruje czcionki obsługujące polskie znaki dla Windows."""
        try:
            # Rejestruj czcionki systemowe Windows
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))
                self.font_family = 'Arial'
                logger.info("Zarejestrowano czcionki Arial z obsługą polskich znaków")
            except:
                # Fallback do DejaVu Sans jeśli dostępne
                try:
                    pdfmetrics.registerFont(TTFont('DejaVuSans', 'C:/Windows/Fonts/DejaVuSans.ttf'))
                    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'C:/Windows/Fonts/DejaVuSans-Bold.ttf'))
                    self.font_family = 'DejaVuSans'
                    logger.info("Zarejestrowano czcionki DejaVu Sans")
                except:
                    # Próbuj Calibri
                    try:
                        pdfmetrics.registerFont(TTFont('Calibri', 'C:/Windows/Fonts/calibri.ttf'))
                        pdfmetrics.registerFont(TTFont('Calibri-Bold', 'C:/Windows/Fonts/calibrib.ttf'))
                        self.font_family = 'Calibri'
                        logger.info("Zarejestrowano czcionki Calibri")
                    except:
                        self.font_family = 'Helvetica'
                        logger.warning("Używam domyślnych czcionek Helvetica - polskie znaki mogą nie działać")
        except Exception as e:
            self.font_family = 'Helvetica'
            logger.warning(f"Błąd podczas konfiguracji czcionek: {e}")
    
    def _setup_custom_styles(self):
        """Konfiguruje niestandardowe style dla dokumentu."""
        
        # Określ czcionki na podstawie dostępności
        bold_font = f'{self.font_family}-Bold' if self.font_family != 'Helvetica' else 'Helvetica-Bold'
        normal_font = self.font_family
        
        # Styl tytułu głównego
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName=bold_font
        ))
        
        # Styl nagłówków sekcji
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.darkblue,
            fontName=bold_font
        ))
        
        # Styl podsekcji
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=15,
            textColor=colors.darkblue,
            fontName=bold_font
        ))
        
        # Styl zwykłego tekstu
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName=normal_font
        ))
        
        # Styl dla statystyk
        self.styles.add(ParagraphStyle(
            name='StatStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            fontName=bold_font,
            textColor=self.report_colors['primary']
        ))
    
    def _create_header_footer(self, canvas, doc):
        """
        Dodaje nagłówki i stopki do każdej strony.
        
        Args:
            canvas: Canvas ReportLab
            doc: Dokument
        """
        canvas.saveState()
        
        # Nagłówek
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(self.report_colors['primary'])
        canvas.drawString(inch, A4[1] - 0.75*inch, 
                         "System Rekomendacji Tras Turystycznych")
        
        # Linia pod nagłówkiem
        canvas.setLineWidth(1)
        canvas.line(inch, A4[1] - 0.9*inch, A4[0] - inch, A4[1] - 0.9*inch)
        
        # Stopka
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.gray)
        canvas.drawString(inch, 0.75*inch, 
                         f"Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Numer strony
        canvas.drawRightString(A4[0] - inch, 0.75*inch, 
                              f"Strona {doc.page}")
        
        # Linia nad stopką
        canvas.line(inch, inch, A4[0] - inch, inch)
        
        canvas.restoreState()
    
    def _create_title_page(self, trails_data: List[Dict[str, Any]], search_params: Dict[str, Any]) -> List:
        """
        Tworzy stronę tytułową z datą generowania i parametrami wyszukiwania.
        
        Args:
            trails_data: Lista danych tras
            search_params: Parametry wyszukiwania użyte w raporcie
            
        Returns:
            Lista elementów dla strony tytułowej
        """
        story = []
        
        # Tytuł główny
        title = f"Raport Rekomendacji Tras Turystycznych"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Podtytuł z datą
        subtitle = f"Analiza tras - {datetime.now().strftime('%B %Y')}"
        story.append(Paragraph(subtitle, self.styles['SectionHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        # Parametry wyszukiwania
        story.append(Paragraph("Parametry wyszukiwania:", self.styles['SubHeader']))
        
        search_info = []
        if search_params.get('city'):
            search_info.append(f"Miasto: {search_params['city']}")
        if search_params.get('date'):
            search_info.append(f"Data: {search_params['date']}")
        if search_params.get('difficulty'):
            search_info.append(f"Poziom trudności: {search_params['difficulty']}")
        if search_params.get('category'):
            search_info.append(f"Kategoria: {search_params['category']}")
        if search_params.get('min_length'):
            search_info.append(f"Min. długość: {search_params['min_length']} km")
        if search_params.get('max_length'):
            search_info.append(f"Max. długość: {search_params['max_length']} km")
        
        for info in search_info:
            story.append(Paragraph(f"• {info}", self.styles['CustomNormal']))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Podsumowanie statystyczne
        story.append(Paragraph("Podsumowanie analizy:", self.styles['SubHeader']))
        
        total_trails = len(trails_data)
        avg_length = sum(t.get('length_km', 0) for t in trails_data) / total_trails if total_trails > 0 else 0
        avg_rating = sum(t.get('user_rating', 0) or t.get('rating', 0) for t in trails_data) / total_trails if total_trails > 0 else 0
        
        summary_stats = [
            f"Łączna liczba analizowanych tras: {total_trails}",
            f"Średnia długość trasy: {avg_length:.1f} km",
            f"Średnia ocena użytkowników: {avg_rating:.1f}/5",
            f"Data wygenerowania raportu: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        ]
        
        for stat in summary_stats:
            story.append(Paragraph(stat, self.styles['StatStyle']))
        
        story.append(PageBreak())
        return story
    
    def _create_table_of_contents(self, trails_data: List[Dict[str, Any]]) -> List:
        """
        Tworzy spis treści z linkami do sekcji.
        
        Args:
            trails_data: Lista danych tras
            
        Returns:
            Lista elementów spisu treści
        """
        story = []
        
        story.append(Paragraph("Spis treści", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.3*inch))
        
        sections = [
            "1. Podsumowanie wykonawcze",
            "2. Analiza wykresowa",
            "3. Rekomendowane trasy",
            "4. Szczegółowe opisy tras",
            "5. Tabela zbiorcza",
            "6. Aneks z danymi źródłowymi"
        ]
        
        for section in sections:
            story.append(Paragraph(section, self.styles['CustomNormal']))
        
        story.append(PageBreak())
        return story
    
    def _create_executive_summary(self, trails_data: List[Dict[str, Any]]) -> List:
        """
        Tworzy podsumowanie wykonawcze z najważniejszymi wnioskami.
        
        Args:
            trails_data: Lista danych tras
            
        Returns:
            Lista elementów podsumowania
        """
        story = []
        
        story.append(Paragraph("1. Podsumowanie wykonawcze", self.styles['SectionHeader']))
        
        # Analiza statystyczna
        total_trails = len(trails_data)
        if total_trails == 0:
            story.append(Paragraph("Brak danych tras do analizy.", self.styles['CustomNormal']))
            story.append(PageBreak())
            return story
        
        # Kategorie tras
        categories = {}
        difficulty_levels = {}
        lengths = []
        ratings = []
        
        for trail in trails_data:
            # Kategorie
            cat = trail.get('category', 'nieskategoryzowana')
            categories[cat] = categories.get(cat, 0) + 1
            
            # Trudność
            diff = trail.get('difficulty', 2)
            difficulty_levels[diff] = difficulty_levels.get(diff, 0) + 1
            
            # Długość i oceny
            if trail.get('length_km'):
                lengths.append(trail['length_km'])
            if trail.get('user_rating') or trail.get('rating'):
                ratings.append(trail.get('user_rating') or trail.get('rating'))
        
        # Najważniejsze wnioski
        most_common_category = max(categories.items(), key=lambda x: x[1]) if categories else ('brak', 0)
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        summary_text = f"""
        Analiza obejmuje {total_trails} tras turystycznych. Najczęściej występującą kategorią 
        tras jest "{most_common_category[0]}" ({most_common_category[1]} tras). 
        
        Średnia długość analizowanych tras wynosi {avg_length:.1f} km, co wskazuje na 
        {"krótkie, rodzinne trasy" if avg_length < 8 else "średnie trasy rekreacyjne" if avg_length < 15 else "długie, wymagające trasy"}.
        
        Średnia ocena użytkowników to {avg_rating:.1f}/5, co oznacza 
        {"niski poziom zadowolenia" if avg_rating < 3 else "umiarkowany poziom zadowolenia" if avg_rating < 4 else "wysoki poziom zadowolenia"}.
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomNormal']))
        
        # Rekomendacje
        story.append(Paragraph("Kluczowe rekomendacje:", self.styles['SubHeader']))
        
        recommendations = []
        if avg_rating < 3.5:
            recommendations.append("Zaleca się dokładniejszą weryfikację jakości tras przed rekomendacją.")
        if avg_length > 15:
            recommendations.append("Rozważenie dodania krótszych tras dla rodzin z dziećmi.")
        if most_common_category[0] == 'sportowa':
            recommendations.append("Zwiększenie oferty tras widokowych i rekreacyjnych.")
        
        if not recommendations:
            recommendations.append("Obecna oferta tras jest dobrze zrównoważona i odpowiada potrzebom użytkowników.")
        
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['CustomNormal']))
        
        story.append(PageBreak())
        return story
    
    def _create_charts_section(self, trails_data: List[Dict[str, Any]], report_name: str) -> List:
        """
        Tworzy sekcję z wykresami porównawczymi.
        
        Args:
            trails_data: Lista danych tras
            report_name: Nazwa raportu
            
        Returns:
            Lista elementów sekcji wykresów
        """
        story = []
        
        story.append(Paragraph("2. Analiza wykresowa", self.styles['SectionHeader']))
        
        # Generuj wykresy
        charts = self.chart_generator.generate_all_charts(trails_data, report_name)
        
        # Dodaj wykresy do raportu
        chart_descriptions = {
            'length_histogram': 'Histogram przedstawia rozkład długości analizowanych tras.',
            'category_pie': 'Wykres kołowy pokazuje proporcje różnych kategorii tras.',
            'rating_bar': 'Wykres słupkowy przedstawia rozkład ocen użytkowników.',
            'seasonal_heatmap': 'Mapa ciepła pokazuje popularność tras w różnych miesiącach.',
            'elevation_profile': 'Profil wysokościowy przykładowej trasy.',
            'radar_chart': 'Wykres radarowy oceniający trasę pod różnymi względami.'
        }
        
        for chart_name, chart_path in charts.items():
            if os.path.exists(chart_path):
                # Tytuł wykresu
                chart_title = chart_descriptions.get(chart_name, f'Wykres {chart_name}')
                story.append(Paragraph(chart_title, self.styles['SubHeader']))
                
                # Obraz wykresu
                try:
                    img = Image(chart_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    logger.error(f"Błąd podczas dodawania wykresu {chart_name}: {e}")
                    story.append(Paragraph(f"Błąd podczas ładowania wykresu: {chart_name}", 
                                         self.styles['CustomNormal']))
        
        story.append(PageBreak())
        return story
    
    def _create_detailed_routes_section(self, trails_data: List[Dict[str, Any]]) -> List:
        """
        Tworzy szczegółowe opisy rekomendowanych tras.
        
        Args:
            trails_data: Lista danych tras
            
        Returns:
            Lista elementów szczegółowych opisów
        """
        story = []
        
        story.append(Paragraph("4. Szczegółowe opisy tras", self.styles['SectionHeader']))
        
        # Ograniczenie do top 10 tras
        top_trails = trails_data[:10]
        
        for i, trail in enumerate(top_trails, 1):
            # Nagłówek trasy
            trail_name = trail.get('name', f'Trasa {i}')
            story.append(Paragraph(f"{i}. {trail_name}", self.styles['SubHeader']))
            
            # Podstawowe informacje
            info_data = []
            if trail.get('length_km'):
                info_data.append(['Długość:', f"{trail['length_km']:.1f} km"])
            if trail.get('difficulty'):
                info_data.append(['Trudność:', f"{trail['difficulty']}/3"])
            if trail.get('terrain_type'):
                info_data.append(['Typ terenu:', trail['terrain_type']])
            if trail.get('estimated_time'):
                hours = int(trail['estimated_time'])
                minutes = int((trail['estimated_time'] - hours) * 60)
                if hours > 0 and minutes > 0:
                    time_str = f"{hours}h {minutes}min"
                elif hours > 0:
                    time_str = f"{hours}h"
                else:
                    time_str = f"{minutes}min"
                info_data.append(['Czas przejścia:', time_str])
            if trail.get('user_rating') or trail.get('rating'):
                rating = trail.get('user_rating') or trail.get('rating')
                # Używamy prostego tekstu zamiast symboli
                rating_text = f"{rating:.1f}/5"
                if rating >= 4.5:
                    rating_text += " (Doskonała)"
                elif rating >= 4.0:
                    rating_text += " (Bardzo dobra)"
                elif rating >= 3.0:
                    rating_text += " (Dobra)"
                elif rating >= 2.0:
                    rating_text += " (Przeciętna)"
                else:
                    rating_text += " (Słaba)"
                info_data.append(['Ocena użytkowników:', rating_text])
            if trail.get('category'):
                info_data.append(['Kategoria:', trail['category']])
            if trail.get('comfort_index'):
                info_data.append(['Indeks komfortu:', f"{trail['comfort_index']:.1f}/100"])
            
            if info_data:
                info_table = Table(info_data, colWidths=[2*inch, 3*inch])
                # Określ czcionki dla tabeli
                table_bold_font = f'{self.font_family}-Bold' if self.font_family != 'Helvetica' else 'Helvetica-Bold'
                table_normal_font = self.font_family
                
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), self.report_colors['light_gray']),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), table_bold_font),
                    ('FONTNAME', (1, 0), (1, -1), table_normal_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(info_table)
                story.append(Spacer(1, 0.2*inch))
            
            # Opis trasy
            if trail.get('description'):
                story.append(Paragraph("Opis:", self.styles['CustomNormal']))
                story.append(Paragraph(trail['description'][:500] + "..." if len(trail['description']) > 500 else trail['description'], 
                                     self.styles['CustomNormal']))
            
            # Recenzje (jeśli są)
            if trail.get('reviews') and len(trail['reviews']) > 0:
                story.append(Paragraph("Przykładowe recenzje:", self.styles['CustomNormal']))
                for review in trail['reviews'][:3]:  # Max 3 recenzje
                    story.append(Paragraph(f"• {review[:200]}{'...' if len(review) > 200 else ''}", 
                                         self.styles['CustomNormal']))
            
            story.append(Spacer(1, 0.3*inch))
        
        story.append(PageBreak())
        return story
    
    def _create_summary_table(self, trails_data: List[Dict[str, Any]]) -> List:
        """
        Tworzy tabelę zbiorczą wszystkich analizowanych tras.
        
        Args:
            trails_data: Lista danych tras
            
        Returns:
            Lista elementów tabeli zbiorczej
        """
        story = []
        
        story.append(Paragraph("5. Tabela zbiorcza tras", self.styles['SectionHeader']))
        
        # Nagłówki tabeli
        headers = ['Lp.', 'Nazwa trasy', 'Długość (km)', 'Trudność', 'Ocena', 'Kategoria']
        
        # Dane tabeli
        table_data = [headers]
        for i, trail in enumerate(trails_data[:20], 1):  # Max 20 tras w tabeli
            row = [
                str(i),
                trail.get('name', 'Nieznana')[:30] + '...' if len(trail.get('name', '')) > 30 else trail.get('name', 'Nieznana'),
                f"{trail.get('length_km', 0):.1f}" if trail.get('length_km') else 'N/A',
                f"{trail.get('difficulty', 'N/A')}/3" if trail.get('difficulty') else 'N/A',
                f"{trail.get('user_rating') or trail.get('rating', 0):.1f}/5" if trail.get('user_rating') or trail.get('rating') else 'N/A',
                trail.get('category', 'N/A')
            ]
            table_data.append(row)
        
        # Utwórz tabelę
        table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
        # Określ czcionki dla tabeli
        table_bold_font = f'{self.font_family}-Bold' if self.font_family != 'Helvetica' else 'Helvetica-Bold'
        table_normal_font = self.font_family
        
        table.setStyle(TableStyle([
            # Nagłówek
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), table_bold_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Zawartość
            ('FONTNAME', (0, 1), (-1, -1), table_normal_font),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Naprzemienne kolory wierszy
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.report_colors['light_gray']]),
        ]))
        
        story.append(table)
        story.append(PageBreak())
        return story
    
    def generate_pdf_report(self, trails_data: List[Dict[str, Any]], 
                          search_params: Dict[str, Any] = None, 
                          filename: str = None) -> str:
        """
        Główna metoda generująca kompletny raport PDF.
        
        Args:
            trails_data: Lista danych tras
            search_params: Parametry wyszukiwania
            filename: Nazwa pliku PDF
            
        Returns:
            Ścieżka do wygenerowanego pliku PDF
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"raport_tras_{timestamp}.pdf"
        
        if not search_params:
            search_params = {}
        
        file_path = os.path.join(self.output_dir, filename)
        
        logger.info(f"Generowanie raportu PDF: {filename}")
        
        # Utwórz dokument
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Zbierz wszystkie elementy dokumentu
        story = []
        
        # Nazwa raportu dla wykresów
        report_name = filename.replace('.pdf', '')
        
        try:
            # 1. Strona tytułowa
            story.extend(self._create_title_page(trails_data, search_params))
            
            # 2. Spis treści
            story.extend(self._create_table_of_contents(trails_data))
            
            # 3. Podsumowanie wykonawcze
            story.extend(self._create_executive_summary(trails_data))
            
            # 4. Sekcja wykresów
            story.extend(self._create_charts_section(trails_data, report_name))
            
            # 5. Szczegółowe opisy tras
            story.extend(self._create_detailed_routes_section(trails_data))
            
            # 6. Tabela zbiorcza
            story.extend(self._create_summary_table(trails_data))
            
            # Zbuduj dokument
            doc.build(story, onFirstPage=self._create_header_footer, 
                     onLaterPages=self._create_header_footer)
            
            logger.info(f"Raport PDF został pomyślnie wygenerowany: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania raportu PDF: {e}")
            raise 